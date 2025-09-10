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
