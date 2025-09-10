import asyncio
import json

from temporalio import activity
from temporalio.exceptions import ApplicationError

# These activities are mocks that simulate interactions with other services
# in your architecture diagram.


class PolicyErrors:
    POLICY_DENIED = "POLICY_DENIED"


@activity.defn(name="CheckPolicy")
async def check_policy(args: list[str]) -> str:
    """
    Simulates calling the Policy Engine (OPA Governance).
    In a real system, this would make an RPC/API call.
    """
    activity.logger.info(f"Checking policy for task: '{args}'")
    for arg in args:
        if "forbidden" in arg.lower():
            activity.logger.warning("Policy check DENIED.")
            raise ApplicationError(
                message=json.dumps(args),
                type=PolicyErrors.POLICY_DENIED,
                non_retryable=True,
            )

    await asyncio.sleep(1)  # simulate network latency
    activity.logger.info("Policy check APPROVED.")
    return "approve"


@activity.defn(name="RequestHumanApproval")
async def request_human_approval(args: list[str]) -> str:
    """
    Simulates notifying the Human-In-Loop Service that an approval is needed.
    It returns a task ID that the human interface can use to correlate the approval.
    """
    task_token = activity.info().task_token

    # In a real app, you would send this task_token to your UI/backend service
    # so it can be used to signal completion.
    activity.heartbeat(task_token.hex())
    # Tell the worker not to complete this activity.
    # It will be completed externally.
    activity.raise_complete_async()


@activity.defn(name="ExecuteAgentTask")
async def execute_agent_task(args: list[str]) -> str:
    """
    Simulates the Temporal Worker executing a task via the Agent Management Layer.
    This is the core "work" of the workflow.
    """
    activity.logger.info(f"Executing agent task: '{args}'...")

    # Simulate a task that can fail and be retried by Temporal
    if activity.info().attempt < 3:
        # This will cause the activity to fail, and Temporal will retry it
        # based on the workflow's retry policy.
        # raise RuntimeError("Simulating a transient failure! Temporal will retry.")
        pass

    await asyncio.sleep(3)  # simulate a long-running task
    activity.logger.info(f"Agent task '{args}' completed successfully.")
    return "SUCCESS"


@activity.defn(name="CleanupTask")
async def cleanup_task(args: list[str]) -> None:
    """
    Simulates a final cleanup or notification step.
    """
    activity.logger.info(f"Cleaning up resources for task: '{args}'.")
    await asyncio.sleep(1)
