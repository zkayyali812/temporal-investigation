# Temporal Investigation - Demo & Documentation

This project provides a runnable Python implementation of the Orchestration & Scheduling service using the Temporal framework. It's designed to demonstrate the core capabilities outlined in the architecture diagram and satisfy the acceptance criteria, even while other services are still in development.

## How it Works

The system is composed of four key parts:

1. **[activities.py](src/activities/activities.py)**: Defines the individual units of work. These are simple Python functions that would, in a real system, contain the logic to call other services (like the Policy Engine, an external agent, or a human-in-the-loop UI service). Here, they are mocked to return predefined responses.
2. **[workflows.py](src/workflows/sample_workflow.py)**: Defines the orchestration logic. It sequences the calls to activities, handles conditional logic, and manages the crucial "human-in-the-loop" waiting step using Temporal's signal feature.
3. **[worker.py](src/worker/main.py)**: This is the process that runs the code. It connects to the Temporal Server, listens for tasks on a specific "task queue," and executes the appropriate workflow or activity code. You can run multiple instances of the worker for scalability.
4. **[run_workflow.py](run_workflow.py)**: A command-line client used to start workflows and send signals to them. This simulates external triggers, such as a user action or a scheduled event.

## How to Run This Demo

### Prerequisites

1. **Python 3.11+**: Ensure you have a modern version of Python installed.
2. **Temporal Server**: The easiest way to get a local Temporal server running is with Docker. If you don't have it, this will start a complete local environment:

    ```bash
    # Mac
    brew install temporal
    # Otherwise check out installation instructions here - https://temporal.io/setup/install-temporal-cli
    ```

### Step-by-Step Instructions

**0. Initialize Virtual Environment:**

First, create and activate your virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

**1. Install Dependencies:**

Install the necessary Python requirements.

```bash
make reqs
```

**2. Start the Temporal Server:**

This command starts the temporal server, allowing you to access its UI on - http://localhost:8233

```bash
make run-server
```

Leave this terminal running.

**3. Run the Worker:**

Open another terminal window and start the worker. It will connect to the Temporal server and wait for tasks.

```bash
make run-worker
```

Leave this terminal running.

**4. Start a Workflow:**

Open another terminal window. Use the `run_workflow.py` script to start a Sample workflow.

```bash
# This will start a workflow that should pass the policy check
make sample-workflow
```

You'll see output like: `Started workflow with ID: sample-workflow-xxxx`. Note this ID. In the worker's terminal, you'll see logs indicating the workflow has started and is now waiting for human approval.
If you visit the UI, you will see this workflow and it's status - it should be in a **Running** state.

**5. Send an Approval or Rejection Signal:**

Now, simulate the human interface sending an "approve" signal back to the waiting workflow. Use the ID from the previous step.

```bash
make approve-workflow # Prompts for workflow-id and approves the workflow
make reject workflow  # Prompts for workflow-id and rejects the workflow
```

Check the worker's terminal again. You'll see the workflow resumed, executed the final agent task, and completed successfully.

### Testing Other Scenarios

* **Policy Denial:** Start a workflow with a task description that will be blocked by our mock policy.

    ```bash
    make policy-denied-workflow
    ```

    The workflow will start and then terminate immediately after the policy check fails. The mock policy denies all workflows given with input starting with `forbidden`.

* **Scheduled Workflows (Simulation):** To simulate the "Schedule Coordinator," you can run the scheduler command, which will start a new workflow every 15 seconds.

    ```bash
    make schedule-workflow
    ```
