import asyncio
import sys
import uuid
from datetime import timedelta

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleSpec,
    ScheduleState,
)
from temporalio.exceptions import ApplicationError

from src.workflows.sample_workflow import SampleWorkflow

# The task queue the worker is listening on
TASK_QUEUE = "sample-task-queue"


async def main():
    # Connect to the same Temporal server as the worker
    client = await Client.connect("localhost:7233")

    # The first command-line argument determines the action
    action = sys.argv[1] if len(sys.argv) > 1 else "help"

    if action == "start":
        if len(sys.argv) < 3:
            print("Usage: python run_sample_workflow.py start <task_description>")
            return

        task_description = sys.argv[2]
        # Generate a unique ID for this workflow execution
        workflow_id = f"sample-workflow-{uuid.uuid4()}"

        print(f"Starting workflow with ID: {workflow_id}")
        print(f"Task: '{task_description}'")

        # Start the workflow. This call is non-blocking.
        await client.start_workflow(
            SampleWorkflow.run,
            task_description,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )

    elif action == "signal":
        if len(sys.argv) < 4 or sys.argv[3] not in ["approve", "reject"]:
            print(
                "Usage: python run_sample_workflow.py signal <workflow_id> <approve|reject> [reason]"
            )
            return

        token = sys.argv[2].strip("'\"")
        decision = sys.argv[3]

        handle = client.get_async_activity_handle(task_token=bytes.fromhex(token))
        if decision == "approve":
            print(f"Approving task")
            await handle.complete("approve")
        else:
            print(f"Rejecting task")
            await handle.fail(ApplicationError("reject", non_retryable=True))

    elif action == "schedule":
        # This is a simple loop to simulate a scheduler.
        # In a production environment, you would use Temporal's built-in
        # Cron Schedule feature when starting the workflow.
        print("Starting scheduler simulation. Press Ctrl+C to stop.")
        print("A new workflow will be started every 15 seconds.")
        await client.create_schedule(
            "workflow-schedule-id",
            Schedule(
                action=ScheduleActionStartWorkflow(
                    SampleWorkflow.run,
                    "my schedule arg",
                    id=f"scheduled-workflow-id",
                    task_queue=TASK_QUEUE,
                ),
                spec=ScheduleSpec(
                    intervals=[ScheduleIntervalSpec(every=timedelta(seconds=15))]
                ),
                state=ScheduleState(note="Here's a note on my Schedule."),
                policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.ALLOW_ALL),
            ),
        )

    else:
        print("Unknown action.")
        print("Usage:")
        print("  python run_sample_workflow.py start <task_description>")
        print(
            "  python run_sample_workflow.py signal <workflow_id> <approve|reject> [reason]"
        )
        print("  python run_sample_workflow.py schedule")


if __name__ == "__main__":
    asyncio.run(main())
