import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from src.activities.activities import (
    check_policy,
    cleanup_task,
    execute_agent_task,
    request_human_approval,
)


@workflow.defn
class SampleWorkflow:
    """
    This workflow orchestrates the entire process, demonstrating all key
    capabilities from the acceptance criteria.
    """

    def __init__(self) -> None:
        self._human_approved: bool | None = None
        self._rejection_reason: str | None = None

    @workflow.run
    async def run(self, task_description: str) -> str:
        workflow.logger.info(f"Workflow started for task: '{task_description}'")

        # 1. Policy Engine Governance
        # The activity is executed with a retry policy. If it fails due to
        # a transient error, Temporal will retry it automatically.
        await workflow.execute_activity(
            check_policy,
            task_description,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        # 2. Human-in-the-Loop Approval
        # This activity will not complete on return, so the workflow will wait for the human approval signal.
        await workflow.execute_activity(
            request_human_approval,
            task_description,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # 3. Core Workflow Execution (Agent Task)
        # This is the main task. It's also given a long timeout and retries.
        execution_result = await workflow.execute_activity(
            execute_agent_task,
            task_description,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=3, non_retryable_error_types=["ApplicationError"]
            ),
        )

        # 4. Final step
        await workflow.execute_activity(
            cleanup_task,
            task_description,
            start_to_close_timeout=timedelta(seconds=20),
        )

        workflow.logger.info("Workflow completed successfully.")
        return f"COMPLETED: {execution_result}"

    @workflow.signal
    def human_approval_signal(self, approved: bool, reason: str | None = None) -> None:
        """
        Signal method to receive the result of the human approval step.
        The Human Interface Layer would call this via the Temporal client.
        """
        self._human_approved = approved
        self._rejection_reason = reason
