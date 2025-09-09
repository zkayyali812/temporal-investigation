import asyncio
import unittest
import unittest.mock as mock
from datetime import timedelta

from temporalio.client import WorkflowFailureError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import activity

# Import the code to be tested
from src.activities.activities import (check_policy, cleanup_task, execute_agent_task, request_human_approval)
from src.workflows.sample_workflow import SampleWorkflow
from temporalio.exceptions import TimeoutError as TemporalTimeoutError

# Custom activity for testing retries
_failure_count = 0

@activity.defn
async def failing_execute_agent_task(task_description: str) -> str:
    """Activity that fails twice then succeeds, for testing retries."""
    global _failure_count
    _failure_count += 1
    
    activity.logger.info(f"Executing failing_execute_agent_task, attempt {_failure_count}")
    
    if _failure_count <= 2:
        activity.logger.info(f"Simulating failure on attempt {_failure_count}")
        raise RuntimeError(f"Simulated failure #{_failure_count}")
    
    activity.logger.info("Task succeeded after retries!")
    return "SUCCESS"

# Custom workflow for retry testing
from temporalio import workflow
from temporalio.common import RetryPolicy

@workflow.defn
class RetryTestWorkflow:
    """Test workflow that uses the failing activity to test retries."""

    def __init__(self) -> None:
        self._human_approved: bool | None = None
        self._rejection_reason: str | None = None

    @workflow.run
    async def run(self, task_description: str) -> str:
        workflow.logger.info(f"RetryTestWorkflow started for task: '{task_description}'")

        # 1. Policy check (use regular activity)
        policy_result = await workflow.execute_activity(
            check_policy,
            task_description,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        if policy_result != "approve":
            workflow.logger.warning("Workflow terminated due to policy denial.")
            return "TERMINATED_POLICY_DENIAL"

        # 2. Human approval request (use regular activity)
        await workflow.execute_activity(
            request_human_approval,
            task_description,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Wait for human approval signal
        await workflow.wait_condition(
            lambda: self._human_approved is not None, timeout=timedelta(minutes=30)
        )

        if not self._human_approved:
            return f"TERMINATED_REJECTED: {self._rejection_reason}"

        # 3. Execute agent task with retries (use failing activity)
        execution_result = await workflow.execute_activity(
            failing_execute_agent_task,  # This will fail twice then succeed
            task_description,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=3, non_retryable_error_types=["ApplicationError"]
            ),
        )

        # 4. Cleanup (use regular activity)
        await workflow.execute_activity(
            cleanup_task,
            task_description,
            start_to_close_timeout=timedelta(seconds=20),
        )

        return f"COMPLETED: {execution_result}"

    @workflow.signal
    def human_approval_signal(self, approved: bool, reason: str | None = None) -> None:
        """Signal method to receive the result of the human approval step."""
        self._human_approved = approved
        self._rejection_reason = reason

TASK_QUEUE = "test-orchestration-task-queue"

class TestOrchestrationWorkflow(unittest.IsolatedAsyncioTestCase):
    """
    Test suite for the OrchestrationWorkflow.

    This suite uses the temporalio.testing.WorkflowEnvironment to run tests
    against an in-memory, time-skipping version of the Temporal server. This
    makes tests fast, reliable, and independent of external services.
    """

    async def test_happy_path_successful_execution(self):
        """TC-HP-01: Validates a successful end-to-end workflow execution."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            # Create a worker that uses our activities and workflow
            async with Worker(
                env.client,
                task_queue=TASK_QUEUE,
                workflows=[SampleWorkflow],
                activities=[
                    check_policy,
                    request_human_approval,
                    execute_agent_task,
                    cleanup_task,
                ],
            ):
                task_description = "Deploy new web server"
                handle = await env.client.start_workflow(
                    SampleWorkflow.run,
                    task_description,
                    id=f"test-happy-path",
                    task_queue=TASK_QUEUE,
                )

                # Send the approval signal
                await handle.signal("human_approval_signal", True)

                # Await the result and assert
                result = await handle.result()
                self.assertEqual(result, "COMPLETED: SUCCESS")

    async def test_policy_denial_terminates_workflow(self):
        """TC-PE-01: Validates that the workflow terminates if the policy is denied."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue=TASK_QUEUE,
                workflows=[SampleWorkflow],
                activities=[check_policy],
            ):
                # Use a description that will trigger a policy denial
                task_description = "Launch forbidden process"
                result = await env.client.execute_workflow(
                    SampleWorkflow.run,
                    task_description,
                    id="test-policy-denial",
                    task_queue=TASK_QUEUE,
                )
                self.assertEqual(result, "TERMINATED_POLICY_DENIAL")

    async def test_human_rejection_terminates_workflow(self):
        """TC-HIL-01: Validates workflow termination on human rejection."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue=TASK_QUEUE,
                workflows=[SampleWorkflow],
                activities=[check_policy, request_human_approval],
            ):
                handle = await env.client.start_workflow(
                    SampleWorkflow.run,
                    "Reboot primary database",
                    id="test-human-rejection",
                    task_queue=TASK_QUEUE,
                )

                # Signal rejection with a reason
                await handle.signal("human_approval_signal", False)

                result = await handle.result()
                assert "TERMINATED_REJECTED" in result

    @mock.patch("src.workflows.sample_workflow.workflow.wait_condition")
    async def test_timeout_waiting_for_approval(self, mock_wait_condition):
        """
        TC-HIL-02: Validates workflow termination after timing out
        waiting for a human approval signal.
        """
        # Configure the mock to simulate a timeout
        mock_wait_condition.side_effect = asyncio.TimeoutError("Test timeout")

        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue=TASK_QUEUE,
                workflows=[SampleWorkflow],
                activities=[check_policy, request_human_approval],
            ):
                result = await env.client.execute_workflow(
                    SampleWorkflow.run,
                    "A task that will be ignored",
                    id="test-timeout",
                    task_queue=TASK_QUEUE,
                )
                # Check that the workflow returns the correct timeout status
                self.assertEqual(result, "TERMINATED_TIMEOUT")


    async def test_activity_retry_on_failure(self):
        """TC-AFR-01: Validates that an activity is retried upon failure."""
        # Reset the failure count before the test
        global _failure_count
        _failure_count = 0

        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue=TASK_QUEUE,
                workflows=[RetryTestWorkflow],  # Use the custom workflow
                activities=[
                    check_policy,
                    request_human_approval,
                    failing_execute_agent_task,  # Use the failing activity
                    cleanup_task,
                ],
            ):
                handle = await env.client.start_workflow(
                    RetryTestWorkflow.run,  # Use the retry test workflow
                    "Test transient failure",
                    id="test-retry",
                    task_queue=TASK_QUEUE,
                )

                await handle.signal("human_approval_signal", True)

                # The workflow should complete successfully after retries
                result = await handle.result()
                self.assertEqual(result, "COMPLETED: SUCCESS")

                # Verify that the failing activity was called 3 times
                # (failed twice, succeeded on third attempt)
                self.assertEqual(_failure_count, 3)

