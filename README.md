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

## Temporal Acceptance Criteria Notes

### Core Workflow Execution

The workflow execution capability can be shown by running the demo [above](#core-workflow-execution). This demo shows the following case -

1. A workflow is launched
2. The workflow is evaluated against the mock policy engine
    1. Mock policy engine checks if the given input starts with **forbidden**, if so it is rejected, otherwise it passes
3. If passed via policy engine the workflow awaits for human input to accept/reject the workflow.
4. If approved, it continues to the activity - `execute_agent_task`, which is simulating interacting with an AI agent.
5. Workflow completes

This workflow is codified and can be run by running `make sample-workflow`.

This can be extended by creating a Driver workflow based on JSON/YAML definition which can then be interpreted by a temporal engine wrapper to execute the workflow as specified in the JSON/YAML definition.

### Human in the loop approval

Running the sample workflow above demonstrates this capability, where a specific task is created which awaits for an approve/reject signal.
Temporal can handle signals gracefully via built in mechanisms, and signals can be sent from the temporal client, the CLI, or within workflows.

### Scheduled and Event-Driven Triggers

A scheduled trigger can be shown by running the `make schedule-workflow` command. Which schedules a new workflow every 15 seconds.
Temporal supports many advanced scheduling capabilities with full CRUD capabilities, and capabilities around triggering/backfilling scheduled workfflows.
For more info see - https://docs.temporal.io/develop/python/schedules

Regarding event-driven triggers, an API can be created using a simple webserver to automatically trigger a workflow.

### Policy Engine Governance

We can create task(s) which have the responsibility of interacting with the policy engine. In the sample workflow above, there is a particular task which mocks this capability by checking if the input starts with `forbidden`, if so it is denied. This can be extended to work with Policy as Code, for more advanced policy checks.

### Resilience and Statefulness

Temporal ensures resiliency and statefulness through its core abstraction, the [Durable Execution](https://temporal.io/blog/building-reliable-distributed-systems-in-node#durable-execution) of a Workflow. A Workflow is essentially a piece of code whose state is continuously persisted by the Temporal Cluster. This process, known as event sourcing, records every state change, external event, and command as an immutable log. If a worker process running the Workflow fails for any reason—be it a server crash, a network partition, or a deployment—the Temporal system automatically preserves the Workflow's complete execution history. When a new worker becomes available, it can replay this history to reconstruct the exact state of the Workflow and seamlessly resume execution from the point of failure. This mechanism guarantees that long-running processes are fault-tolerant and maintain their state over potentially long periods, effectively abstracting away the complexities of state management and failure handling from the developer.

### Upgrade Strategy

Temporal has high level support for [Patching](https://docs.temporal.io/patching), allowing us to apply code changes to new workflow executions without affecting in-progress ones.
Temporal has replay support, so if we replay a workflow before the patch, we can use the existing logic, but future new iterations of the workflow will use the new logic.
Also see [versioning](https://docs.temporal.io/develop/python/versioning) for more information about patching.

With this advanced support, we can expect zero downtime when updating the application, as in progress workflows are unaffected, and new ones can use the new path. Old and new code can run simultaneously. This can be especially beneficial with long-running workflows and tasks where workflows executed before the upgrade can work as intended even after the upgrade.

### Workflow validation

Workflow validation can happen at various states -

1. Platform level validation: The temporal platform validates the integrity of a workflows execution. The platform validates that re-executing a workflow produces the exact same sequence of commands, as the original execution.
2. Initial Input Validation: A custom task is created to validate input at the very beginning
3. In workflow state validation: Each task can implement logic to validate its inputs

If we create a workflow definition backed by JSON/YAML, we would likely need to create a validation mechanism to ensure that the workflow itself is valid and can be executed. This would contain checks to ensure that each activity referenced does exist, and is passed the proper input(s).

### Monitoring & Observability

Temporal handles monitoring and observability through a comprehensive, built-in system that emits detailed metrics, supports distributed tracing, and enables structured logging. The Temporal Cluster and its SDKs are instrumented to produce a rich set of metrics out-of-the-box, covering everything from the health of the core services and persistence layers to granular details about workflow and activity performance, such as execution counts, latency, and failure rates. These metrics are designed to be scraped by standard observability platforms like Prometheus and visualized in dashboards using tools like Grafana. Furthermore, Temporal facilitates end-to-end distributed tracing by propagating context through workflows, activities, and even across retries, allowing developers to trace a single logical operation through its entire lifecycle. This, combined with structured logging from both the Cluster and workers, provides deep visibility into system behavior, making it easier to debug issues, optimize performance, and maintain a clear, real-time understanding of workflow executions.

For more info see - [Observability](https://docs.temporal.io/develop/python/observability). Temporal has high level capabilites for metrics, tracing, workflow logs, and visibility APIs.

### Auditability

Temporal provides robust auditability by design, centered around the immutable event history of every workflow execution. Because every action that changes a workflow's state—such as starting the workflow, firing a timer, executing an activity, or receiving a signal—is recorded as a discrete, timestamped event in an append-only log, this history serves as a definitive and complete audit trail. This log is the single source of truth for the workflow's execution, capturing not just what happened, but in what order, including all inputs and outputs for each step. This detailed, chronological record is persisted by the Temporal Cluster and can be retrieved via UI, CLI, or API at any time during or after a workflow's execution (up to the configured retention period), allowing developers and auditors to precisely reconstruct the state of a process at any point in time to debug issues, verify compliance, or analyze business operations.

### What does a workflow definition model look like?

By default a workflow definition is structured as code, but we can extend this to a driver based approach, where the workflow is codified in JSON/YAML, and executed.
