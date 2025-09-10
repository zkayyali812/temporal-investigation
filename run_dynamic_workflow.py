import argparse
import asyncio
import logging
import uuid
from pathlib import Path

import yaml
from temporalio.client import Client

from src.worker.main import TASK_QUEUE
from src.workflows.dynamic_workflow import DynamicWorkflow


async def main():
    # Set up basic logging
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Temporal Dynamic Workflow Driver")
    parser.add_argument(
        "--workflow-definition",
        required=True,
        help="Path to the workflow definition file.",
    )
    args = parser.parse_args()

    try:
        # Make sure 'workflow_definition.yaml' is in the same directory
        # or provide the correct path to it.
        workflow_definition = Path(args.workflow_definition).read_text()
    except FileNotFoundError:
        logging.error(
            "Error: workflow_definition.yaml not found in the current directory."
        )
        return

    client = await Client.connect("localhost:7233")
    logging.info("Starting dynamic workflow...")
    await client.start_workflow(
        DynamicWorkflow.run,
        workflow_definition,
        id=f"dynamic-workflow-py-{uuid.uuid4()}",
        task_queue=TASK_QUEUE,
    )


if __name__ == "__main__":
    asyncio.run(main())
