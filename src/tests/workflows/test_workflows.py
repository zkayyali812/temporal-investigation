import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from temporalio.exceptions import ApplicationError

from src.activities.activities import PolicyErrors
from src.workflows.dynamic_workflow import DynamicWorkflow
from src.workflows.sample_workflow import SampleWorkflow


class TestSampleWorkflow:
    """Test suite for the SampleWorkflow."""

    @pytest.mark.asyncio
    async def test_sample_workflow_initialization(self):
        """Test SampleWorkflow initialization."""
        workflow = SampleWorkflow()
        assert workflow._human_approved is None
        assert workflow._rejection_reason is None

    @pytest.mark.asyncio
    async def test_sample_workflow_signal_handling(self):
        """Test SampleWorkflow signal handling for human approval."""
        workflow_instance = SampleWorkflow()

        # Test initial state
        assert workflow_instance._human_approved is None
        assert workflow_instance._rejection_reason is None

        # Send approval signal
        workflow_instance.human_approval_signal(True, None)
        assert workflow_instance._human_approved is True
        assert workflow_instance._rejection_reason is None

        # Send rejection signal
        workflow_instance.human_approval_signal(False, "Not authorized")
        assert workflow_instance._human_approved is False
        assert workflow_instance._rejection_reason == "Not authorized"

    @pytest.mark.asyncio
    async def test_sample_workflow_signal_with_reason(self):
        """Test SampleWorkflow signal handling with rejection reason."""
        workflow_instance = SampleWorkflow()

        # Send rejection signal with specific reason
        workflow_instance.human_approval_signal(False, "Insufficient permissions")
        assert workflow_instance._human_approved is False
        assert workflow_instance._rejection_reason == "Insufficient permissions"

    @pytest.mark.asyncio
    async def test_sample_workflow_approval_toggle(self):
        """Test that signals can change the approval state."""
        workflow_instance = SampleWorkflow()

        # First approve
        workflow_instance.human_approval_signal(True)
        assert workflow_instance._human_approved is True

        # Then reject
        workflow_instance.human_approval_signal(False, "Changed mind")
        assert workflow_instance._human_approved is False
        assert workflow_instance._rejection_reason == "Changed mind"

        # Approve again
        workflow_instance.human_approval_signal(True)
        assert workflow_instance._human_approved is True

    @pytest.mark.asyncio
    async def test_sample_workflow_signal_multiple_calls(self):
        """Test SampleWorkflow signal can be called multiple times."""
        workflow_instance = SampleWorkflow()

        # Multiple approval signals
        workflow_instance.human_approval_signal(True)
        workflow_instance.human_approval_signal(True, "Additional approval")
        assert workflow_instance._human_approved is True
        assert workflow_instance._rejection_reason == "Additional approval"

        # Multiple rejection signals
        workflow_instance.human_approval_signal(False, "First rejection")
        workflow_instance.human_approval_signal(False, "Second rejection")
        assert workflow_instance._human_approved is False
        assert workflow_instance._rejection_reason == "Second rejection"


class TestDynamicWorkflow:
    """Test suite for the DynamicWorkflow."""

    @pytest.mark.asyncio
    async def test_dynamic_workflow_config_parsing(self):
        """Test that DynamicWorkflow correctly parses YAML configuration."""
        config = {
            "activities": [{"activityName": "CheckPolicy", "args": ["test task"]}]
        }
        raw_config = yaml.dump(config)

        workflow_instance = DynamicWorkflow()

        with patch("src.workflows.dynamic_workflow.workflow") as mock_workflow:
            mock_workflow.execute_activity = AsyncMock(return_value="approved")
            mock_workflow.logger = MagicMock()

            result = await workflow_instance.run(raw_config)

            # Verify the activity was called with correct parameters
            mock_workflow.execute_activity.assert_called_once()
            call_args = mock_workflow.execute_activity.call_args
            assert call_args[0][0] == "CheckPolicy"  # activity name
            assert call_args[0][1] == ["test task"]  # activity args

            # Verify the result format
            assert "Activity CheckPolicy Result: approved" in result

    @pytest.mark.asyncio
    async def test_dynamic_workflow_multiple_activities(self):
        """Test DynamicWorkflow with multiple activities."""
        config = {
            "activities": [
                {"activityName": "CheckPolicy", "args": ["test task 1"]},
                {"activityName": "ExecuteAgentTask", "args": ["test task 2"]},
                {"activityName": "CleanupTask", "args": ["cleanup task"]},
            ]
        }
        raw_config = yaml.dump(config)

        workflow_instance = DynamicWorkflow()

        with patch("src.workflows.dynamic_workflow.workflow") as mock_workflow:
            mock_workflow.execute_activity = AsyncMock(
                side_effect=["approved", "SUCCESS", "cleaned"]
            )
            mock_workflow.logger = MagicMock()

            result = await workflow_instance.run(raw_config)

            # Verify all activities were called
            assert mock_workflow.execute_activity.call_count == 3

            # Verify all results are in the output
            assert "Activity CheckPolicy Result: approved" in result
            assert "Activity ExecuteAgentTask Result: SUCCESS" in result
            assert "Activity CleanupTask Result: cleaned" in result

    @pytest.mark.asyncio
    async def test_dynamic_workflow_empty_config(self):
        """Test DynamicWorkflow with empty configuration."""
        config = {"activities": []}
        raw_config = yaml.dump(config)

        workflow_instance = DynamicWorkflow()

        with patch("src.workflows.dynamic_workflow.workflow") as mock_workflow:
            mock_workflow.execute_activity = AsyncMock()
            mock_workflow.logger = MagicMock()

            result = await workflow_instance.run(raw_config)

            # No activities should be called
            mock_workflow.execute_activity.assert_not_called()

            # Result should be empty
            assert result == ""

    @pytest.mark.asyncio
    async def test_dynamic_workflow_activity_with_no_args(self):
        """Test DynamicWorkflow with activity that has no args."""
        config = {
            "activities": [
                {
                    "activityName": "CheckPolicy"
                    # No args provided
                }
            ]
        }
        raw_config = yaml.dump(config)

        workflow_instance = DynamicWorkflow()

        with patch("src.workflows.dynamic_workflow.workflow") as mock_workflow:
            mock_workflow.execute_activity = AsyncMock(return_value="approved")
            mock_workflow.logger = MagicMock()

            result = await workflow_instance.run(raw_config)

            # Verify the activity was called with empty args
            call_args = mock_workflow.execute_activity.call_args
            assert call_args[0][0] == "CheckPolicy"  # activity name
            assert call_args[0][1] == []  # should default to empty list

            assert "Activity CheckPolicy Result: approved" in result

    @pytest.mark.asyncio
    async def test_dynamic_workflow_invalid_yaml(self):
        """Test DynamicWorkflow with invalid YAML configuration."""
        invalid_yaml = "invalid: yaml: content: {"

        workflow_instance = DynamicWorkflow()

        with patch("src.workflows.dynamic_workflow.workflow") as mock_workflow:
            mock_workflow.logger = MagicMock()

            with pytest.raises(Exception):  # Should fail due to invalid YAML
                await workflow_instance.run(invalid_yaml)

    @pytest.mark.asyncio
    async def test_dynamic_workflow_config_without_activities(self):
        """Test DynamicWorkflow with config that has no activities key."""
        config = {"other_config": "value"}
        raw_config = yaml.dump(config)

        workflow_instance = DynamicWorkflow()

        with patch("src.workflows.dynamic_workflow.workflow") as mock_workflow:
            mock_workflow.execute_activity = AsyncMock()
            mock_workflow.logger = MagicMock()

            result = await workflow_instance.run(raw_config)

            # No activities should be called
            mock_workflow.execute_activity.assert_not_called()

            # Result should be empty
            assert result == ""

    @pytest.mark.asyncio
    async def test_dynamic_workflow_activity_with_complex_args(self):
        """Test DynamicWorkflow with activity that has complex arguments."""
        config = {
            "activities": [
                {
                    "activityName": "ExecuteAgentTask",
                    "args": ["task1", "task2", "task3"],
                }
            ]
        }
        raw_config = yaml.dump(config)

        workflow_instance = DynamicWorkflow()

        with patch("src.workflows.dynamic_workflow.workflow") as mock_workflow:
            mock_workflow.execute_activity = AsyncMock(return_value="SUCCESS")
            mock_workflow.logger = MagicMock()

            result = await workflow_instance.run(raw_config)

            # Verify the activity was called with correct complex args
            call_args = mock_workflow.execute_activity.call_args
            assert call_args[0][0] == "ExecuteAgentTask"  # activity name
            assert call_args[0][1] == ["task1", "task2", "task3"]  # activity args

            assert "Activity ExecuteAgentTask Result: SUCCESS" in result

    @pytest.mark.asyncio
    async def test_dynamic_workflow_activity_execution_timeout(self):
        """Test that DynamicWorkflow sets correct timeout for activities."""
        config = {
            "activities": [{"activityName": "CheckPolicy", "args": ["test task"]}]
        }
        raw_config = yaml.dump(config)

        workflow_instance = DynamicWorkflow()

        with patch("src.workflows.dynamic_workflow.workflow") as mock_workflow:
            mock_workflow.execute_activity = AsyncMock(return_value="approved")
            mock_workflow.logger = MagicMock()

            result = await workflow_instance.run(raw_config)

            # Verify that execute_activity was called with timeout
            call_args, call_kwargs = mock_workflow.execute_activity.call_args
            assert call_kwargs["start_to_close_timeout"] == timedelta(seconds=30)


if __name__ == "__main__":
    pytest.main([__file__])
