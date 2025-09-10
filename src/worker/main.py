import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from src.activities.activities import *
from src.workflows.dynamic_workflow import DynamicWorkflow
from src.workflows.sample_workflow import SampleWorkflow

# This is the task queue the worker will listen on.
TASK_QUEUE = "sample-task-queue"


async def main():
    logging.basicConfig(level=logging.INFO)

    # Create a client to connect to the Temporal server.
    # For local development, this will connect to localhost:7233 by default.
    client = await Client.connect("localhost:7233")

    # Create a new worker.
    # The worker is responsible for polling the task queue, executing the code,
    # and communicating results back to the Temporal server.
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[SampleWorkflow, DynamicWorkflow],
        activities=[
            check_policy,
            request_human_approval,
            execute_agent_task,
            cleanup_task,
            # Base workflow activities
            generate_report,
            send_notification,
            # Complex workflow activities
            initialize_workflow,
            validate_input,
            check_permissions,
            verify_resources,
            request_approval,
            extract_data,
            transform_data,
            load_data,
            send_start_notification,
            monitor_progress,
            log_metrics,
            send_progress_update,
            run_quality_checks,
            generate_quality_report,
            cleanup_resources,
            generate_final_report,
            send_completion_notification,
        ],
    )
    logging.info(f"Worker started for task queue '{TASK_QUEUE}'. Waiting for tasks...")
    # Run the worker until interrupted.
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWorker shutting down.")
