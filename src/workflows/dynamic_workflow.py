# (Inside temporal_workflow_driver.py)
from datetime import timedelta

import yaml
from temporalio import workflow


@workflow.defn
class DynamicWorkflow:
    @workflow.run
    async def run(self, raw_config: str) -> str:
        workflow.logger.info("DynamicWorkflow started")
        config = yaml.safe_load(raw_config)

        results = []
        for activity_def in config.get("activities", []):
            activity_name = activity_def["activityName"]
            activity_args = activity_def.get("args", [])

            result = await workflow.execute_activity(
                activity_name,
                activity_args,
                start_to_close_timeout=timedelta(seconds=30),
            )
            results.append(f"Activity {activity_name} Result: {result}")

        return "\n".join(results)
