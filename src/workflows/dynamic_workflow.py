# (Inside temporal_workflow_driver.py)
import asyncio
from datetime import timedelta
from typing import Any, Dict, List

import yaml
from temporalio import workflow


@workflow.defn
class DynamicWorkflow:
    @workflow.run
    async def run(self, raw_config: str) -> str:
        workflow.logger.info("DynamicWorkflow started")
        config = yaml.safe_load(raw_config)

        # Support legacy format for backward compatibility
        if "activities" in config:
            results = await self._execute_legacy_activities(config["activities"])
        else:
            # New execution block format
            execution_block = config.get("execution", {})
            results = await self._execute_block(execution_block)

        return "\n".join(results)

    async def _execute_legacy_activities(
        self, activities: List[Dict[str, Any]]
    ) -> List[str]:
        """Execute activities in the legacy format for backward compatibility"""
        results = []
        for activity_def in activities:
            activity_name = activity_def["activityName"]
            activity_args = activity_def.get("args", [])

            result = await workflow.execute_activity(
                activity_name,
                activity_args,
                start_to_close_timeout=timedelta(seconds=30),
            )
            results.append(f"Activity {activity_name} Result: {result}")
        return results

    async def _execute_block(self, block: Dict[str, Any]) -> List[str]:
        """Execute a block which can be sequential, parallel, or a single activity"""
        block_type = block.get("type", "sequential")

        if block_type == "activity":
            return await self._execute_activity_block(block)
        elif block_type == "sequential":
            return await self._execute_sequential_block(block)
        elif block_type == "parallel":
            return await self._execute_parallel_block(block)
        else:
            workflow.logger.warning(f"Unknown block type: {block_type}")
            return [f"Warning: Unknown block type {block_type}"]

    async def _execute_activity_block(self, block: Dict[str, Any]) -> List[str]:
        """Execute a single activity"""
        activity_name = block["activityName"]
        activity_args = block.get("args", [])

        result = await workflow.execute_activity(
            activity_name,
            activity_args,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return [f"Activity {activity_name} Result: {result}"]

    async def _execute_sequential_block(self, block: Dict[str, Any]) -> List[str]:
        """Execute blocks sequentially, passing data between nodes"""
        results = []
        blocks = block.get("blocks", [])
        accumulated_data = []

        for sub_block in blocks:
            # Pass accumulated data to the next block (enabled by default, can be disabled with useDataFlow: false)
            if sub_block.get("type") == "activity" and sub_block.get(
                "useDataFlow", True
            ):
                # Append accumulated data to the activity's args
                current_args = sub_block.get("args", [])
                if accumulated_data:
                    # Add the previous results as the first argument
                    sub_block["args"] = [accumulated_data[-1]] + current_args

            sub_results = await self._execute_block(sub_block)
            results.extend(sub_results)

            # Extract actual result for data flow (remove the "Activity X Result: " prefix)
            if sub_results and sub_block.get("type") == "activity":
                actual_result = (
                    sub_results[-1].split("Result: ", 1)[-1]
                    if "Result: " in sub_results[-1]
                    else sub_results[-1]
                )
                accumulated_data.append(actual_result)

        return results

    async def _execute_parallel_block(self, block: Dict[str, Any]) -> List[str]:
        """Execute blocks in parallel"""
        blocks = block.get("blocks", [])

        # Create tasks for parallel execution
        tasks = []
        for sub_block in blocks:
            task = asyncio.create_task(self._execute_block(sub_block))
            tasks.append(task)

        # Wait for all tasks to complete
        results_lists = await asyncio.gather(*tasks)

        # Flatten results
        results = []
        for result_list in results_lists:
            results.extend(result_list)

        return results
