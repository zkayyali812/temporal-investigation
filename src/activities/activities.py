import asyncio
from temporalio import activity

# These activities are mocks that simulate interactions with other services
# in your architecture diagram.

@activity.defn
async def check_policy(task_description: str) -> str:
    """
    Simulates calling the Policy Engine (OPA Governance).
    In a real system, this would make an RPC/API call.
    """
    activity.logger.info(f"Checking policy for task: '{task_description}'")
    if "forbidden" in task_description.lower():
        activity.logger.warning("Policy check DENIED.")
        return "deny"
    
    await asyncio.sleep(1) # simulate network latency
    activity.logger.info("Policy check APPROVED.")
    return "approve"

@activity.defn
async def request_human_approval(task_description: str) -> str:
    """
    Simulates notifying the Human-In-Loop Service that an approval is needed.
    It returns a task ID that the human interface can use to correlate the approval.
    """
    approval_task_id = f"approval-task-{activity.info().workflow_run_id}"
    activity.logger.info(
        f"Requesting human approval for '{task_description}'. "
        f"Task ID: {approval_task_id}. "
        f"A notification would be sent to the Human Interface Layer (API/WebSocket)."
    )
    await asyncio.sleep(1) # simulate work/latency
    return approval_task_id

@activity.defn
async def execute_agent_task(task_description: str) -> str:
    """
    Simulates the Temporal Worker executing a task via the Agent Management Layer.
    This is the core "work" of the workflow.
    """
    activity.logger.info(f"Executing agent task: '{task_description}'...")
    
    # Simulate a task that can fail and be retried by Temporal
    if activity.info().attempt < 3:
        # This will cause the activity to fail, and Temporal will retry it
        # based on the workflow's retry policy.
        # raise RuntimeError("Simulating a transient failure! Temporal will retry.")
        pass

    await asyncio.sleep(3) # simulate a long-running task
    activity.logger.info(f"Agent task '{task_description}' completed successfully.")
    return "SUCCESS"

@activity.defn
async def cleanup_task(task_description: str) -> None:
    """
    Simulates a final cleanup or notification step.
    """
    activity.logger.info(f"Cleaning up resources for task: '{task_description}'.")
    await asyncio.sleep(1)
