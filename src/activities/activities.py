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


@activity.defn(name="GenerateReport")
async def generate_report(args: list[str]) -> str:
    """
    Simulates generating a report for the given user.
    """
    activity.logger.info(f"Generating report for: '{args}'")
    await asyncio.sleep(2)  # simulate report generation time
    activity.logger.info(f"Report generated successfully for: '{args}'")
    return "report_generated"


@activity.defn(name="SendNotification")
async def send_notification(args: list[str]) -> str:
    """
    Simulates sending a notification to the user.
    """
    email, message = args[0], args[1] if len(args) > 1 else "Default message"
    activity.logger.info(f"Sending notification to {email}: '{message}'")
    await asyncio.sleep(1)  # simulate notification sending
    activity.logger.info(f"Notification sent successfully to {email}")
    return "notification_sent"


@activity.defn(name="CleanupTask")
async def cleanup_task(args: list[str]) -> None:
    """
    Simulates a final cleanup or notification step.
    """
    activity.logger.info(f"Cleaning up resources for task: '{args}'.")
    await asyncio.sleep(1)


# Activities for complex workflow
@activity.defn(name="InitializeWorkflow")
async def initialize_workflow(args: list[str]) -> str:
    """
    Initializes the workflow with the given configuration from YAML.
    """
    # First arg could be previous activity data (if data flow), rest are from YAML
    if len(args) > 1:
        # Data flow mode - first arg is from previous activity
        previous_data = args[0]
        workflow_config = args[1] if len(args) > 1 else "default-workflow"
        activity.logger.info(f"Received data from previous activity: {previous_data}")
    else:
        # No previous data
        previous_data = None
        workflow_config = args[0] if args else "default-workflow"

    activity.logger.info(f"Initializing workflow with config: {workflow_config}")
    await asyncio.sleep(1)

    # Create initialization result that includes YAML config
    result = {
        "workflow_id": workflow_config,
        "previous_data": previous_data,
        "session_id": f"session_{workflow_config}",
        "status": "initialized",
    }

    activity.logger.info(f"Workflow initialized: {result}")
    return json.dumps(result)


@activity.defn(name="ValidateInput")
async def validate_input(args: list[str]) -> str:
    """
    Validates the input data using data from previous activity and YAML config.
    """
    # Parse data flow: first arg is from previous activity, second is from YAML
    if len(args) >= 2:
        try:
            previous_data = json.loads(args[0])
            input_type = args[1]
            activity.logger.info(f"Received workflow data: {previous_data}")
            activity.logger.info(f"Validating input type: {input_type}")

            # Use data from previous activity for validation
            session_id = previous_data.get("session_id", "unknown")
            workflow_id = previous_data.get("workflow_id", "unknown")
        except (json.JSONDecodeError, IndexError):
            previous_data = {"error": "invalid_previous_data"}
            input_type = args[0] if args else "unknown"
            session_id = "error_session"
            workflow_id = "error_workflow"
    else:
        input_type = args[0] if args else "unknown"
        previous_data = None
        session_id = "no_session"
        workflow_id = "no_workflow"

    await asyncio.sleep(1)

    # Create validation result that transforms and extends the data
    validation_result = {
        "session_id": session_id,
        "workflow_id": workflow_id,
        "input_type": input_type,
        "validation_status": "passed",
        "validated_fields": ["user_credentials", "permissions", "data_format"],
        "previous_activity_data": previous_data,
    }

    activity.logger.info(f"Input validation completed: {validation_result}")
    return json.dumps(validation_result)


@activity.defn(name="CheckPermissions")
async def check_permissions(args: list[str]) -> str:
    """
    Checks user permissions for workflow execution.
    """
    permission_type = args[0] if args else "default_permissions"
    activity.logger.info(f"Checking permissions: {permission_type}")
    await asyncio.sleep(1)
    activity.logger.info(f"Permission check completed for: {permission_type}")
    return "permissions_granted"


@activity.defn(name="VerifyResources")
async def verify_resources(args: list[str]) -> str:
    """
    Verifies system resources are available for workflow execution.
    """
    resource_type = args[0] if args else "system_resources"
    activity.logger.info(f"Verifying resources: {resource_type}")
    await asyncio.sleep(1)
    activity.logger.info(f"Resource verification completed for: {resource_type}")
    return "resources_available"


@activity.defn(name="RequestApproval")
async def request_approval(args: list[str]) -> str:
    """
    Requests approval for workflow execution.
    """
    approval_type = args[0] if args else "workflow_execution"
    activity.logger.info(f"Requesting approval for: {approval_type}")
    await asyncio.sleep(2)
    activity.logger.info(f"Approval granted for: {approval_type}")
    return "approved"


@activity.defn(name="ExtractData")
async def extract_data(args: list[str]) -> str:
    """
    Extracts data from the source system.
    """
    source = args[0] if args else "default_source"
    activity.logger.info(f"Extracting data from: {source}")
    await asyncio.sleep(3)  # simulate data extraction time
    activity.logger.info(f"Data extraction completed from: {source}")
    return "data_extracted"


@activity.defn(name="TransformData")
async def transform_data(args: list[str]) -> str:
    """
    Transforms data according to the specified rules.
    """
    rules = args[0] if args else "default_rules"
    activity.logger.info(f"Transforming data with rules: {rules}")
    await asyncio.sleep(2)
    activity.logger.info(f"Data transformation completed with rules: {rules}")
    return "data_transformed"


@activity.defn(name="LoadData")
async def load_data(args: list[str]) -> str:
    """
    Loads transformed data into the target system.
    """
    target = args[0] if args else "default_target"
    activity.logger.info(f"Loading data to: {target}")
    await asyncio.sleep(2)
    activity.logger.info(f"Data loading completed to: {target}")
    return "data_loaded"


@activity.defn(name="SendStartNotification")
async def send_start_notification(args: list[str]) -> str:
    """
    Sends notification that the workflow has started.
    """
    recipients = args[0] if args else "default_stakeholders"
    activity.logger.info(f"Sending start notification to: {recipients}")
    await asyncio.sleep(1)
    activity.logger.info(f"Start notification sent to: {recipients}")
    return "start_notification_sent"


@activity.defn(name="MonitorProgress")
async def monitor_progress(args: list[str]) -> str:
    """
    Monitors workflow progress according to configuration.
    """
    config = args[0] if args else "default_config"
    activity.logger.info(f"Monitoring progress with config: {config}")
    await asyncio.sleep(2)
    activity.logger.info(f"Progress monitoring active with config: {config}")
    return "monitoring_active"


@activity.defn(name="LogMetrics")
async def log_metrics(args: list[str]) -> str:
    """
    Logs workflow metrics according to configuration.
    """
    config = args[0] if args else "default_metrics"
    activity.logger.info(f"Logging metrics with config: {config}")
    await asyncio.sleep(1)
    activity.logger.info(f"Metrics logging active with config: {config}")
    return "metrics_logged"


@activity.defn(name="SendProgressUpdate")
async def send_progress_update(args: list[str]) -> str:
    """
    Sends progress update to stakeholders.
    """
    report = args[0] if args else "progress_report"
    activity.logger.info(f"Sending progress update: {report}")
    await asyncio.sleep(1)
    activity.logger.info(f"Progress update sent: {report}")
    return "progress_update_sent"


@activity.defn(name="RunQualityChecks")
async def run_quality_checks(args: list[str]) -> str:
    """
    Runs quality checks according to criteria.
    """
    criteria = args[0] if args else "default_criteria"
    activity.logger.info(f"Running quality checks with criteria: {criteria}")
    await asyncio.sleep(2)
    activity.logger.info(f"Quality checks completed with criteria: {criteria}")
    return "quality_checks_passed"


@activity.defn(name="GenerateQualityReport")
async def generate_quality_report(args: list[str]) -> str:
    """
    Generates quality report based on results.
    """
    results = args[0] if args else "quality_results"
    activity.logger.info(f"Generating quality report from: {results}")
    await asyncio.sleep(1)
    activity.logger.info(f"Quality report generated from: {results}")
    return "quality_report_generated"


@activity.defn(name="CleanupResources")
async def cleanup_resources(args: list[str]) -> str:
    """
    Cleans up temporary resources.
    """
    resources = args[0] if args else "temp_resources"
    activity.logger.info(f"Cleaning up resources: {resources}")
    await asyncio.sleep(1)
    activity.logger.info(f"Resource cleanup completed for: {resources}")
    return "resources_cleaned"


@activity.defn(name="GenerateFinalReport")
async def generate_final_report(args: list[str]) -> str:
    """
    Generates final execution report.
    """
    summary = args[0] if args else "execution_summary"
    activity.logger.info(f"Generating final report: {summary}")
    await asyncio.sleep(2)
    activity.logger.info(f"Final report generated: {summary}")
    return "final_report_generated"


@activity.defn(name="SendCompletionNotification")
async def send_completion_notification(args: list[str]) -> str:
    """
    Sends completion notification to stakeholders.
    """
    status = args[0] if args else "completed"
    recipients = args[1] if len(args) > 1 else "stakeholders"
    activity.logger.info(
        f"Sending completion notification with status '{status}' to: {recipients}"
    )
    await asyncio.sleep(1)
    activity.logger.info(
        f"Completion notification sent with status '{status}' to: {recipients}"
    )
    return "completion_notification_sent"
