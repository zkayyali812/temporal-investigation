import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest
from temporalio.exceptions import ApplicationError

from src.activities.activities import (
    PolicyErrors,
    check_policy,
    cleanup_task,
    execute_agent_task,
    request_human_approval,
)


class TestCheckPolicy:
    """Test suite for the check_policy activity."""

    @pytest.mark.asyncio
    async def test_check_policy_approve_valid_args(self):
        """Test that check_policy approves valid arguments."""
        valid_args = ["deploy application", "update configuration"]

        with patch("src.activities.activities.activity") as mock_activity:
            mock_activity.logger = MagicMock()
            result = await check_policy(valid_args)
            assert result == "approve"

    @pytest.mark.asyncio
    async def test_check_policy_deny_forbidden_args(self):
        """Test that check_policy denies arguments containing 'forbidden'."""
        forbidden_args = ["deploy forbidden application", "update config"]

        with patch("src.activities.activities.activity") as mock_activity:
            mock_activity.logger = MagicMock()
            with pytest.raises(ApplicationError) as exc_info:
                await check_policy(forbidden_args)

            assert exc_info.value.type == PolicyErrors.POLICY_DENIED
            assert exc_info.value.non_retryable is True
            # Check that the message contains the forbidden args
            parsed_message = json.loads(exc_info.value.message)
            assert parsed_message == forbidden_args

    @pytest.mark.asyncio
    async def test_check_policy_case_insensitive_forbidden(self):
        """Test that check_policy is case insensitive for forbidden detection."""
        forbidden_args = ["deploy FORBIDDEN application"]

        with patch("src.activities.activities.activity") as mock_activity:
            mock_activity.logger = MagicMock()
            with pytest.raises(ApplicationError) as exc_info:
                await check_policy(forbidden_args)

            assert exc_info.value.type == PolicyErrors.POLICY_DENIED

    @pytest.mark.asyncio
    async def test_check_policy_empty_args(self):
        """Test that check_policy handles empty arguments."""
        empty_args = []

        with patch("src.activities.activities.activity") as mock_activity:
            mock_activity.logger = MagicMock()
            result = await check_policy(empty_args)
            assert result == "approve"

    @pytest.mark.asyncio
    async def test_check_policy_multiple_forbidden_args(self):
        """Test that check_policy fails on multiple forbidden arguments."""
        forbidden_args = ["forbidden task 1", "forbidden task 2"]

        with patch("src.activities.activities.activity") as mock_activity:
            mock_activity.logger = MagicMock()
            with pytest.raises(ApplicationError) as exc_info:
                await check_policy(forbidden_args)

            assert exc_info.value.type == PolicyErrors.POLICY_DENIED

    @pytest.mark.asyncio
    async def test_check_policy_mixed_args(self):
        """Test that check_policy fails if any argument contains forbidden."""
        mixed_args = ["valid task", "forbidden operation", "another valid task"]

        with patch("src.activities.activities.activity") as mock_activity:
            mock_activity.logger = MagicMock()
            with pytest.raises(ApplicationError) as exc_info:
                await check_policy(mixed_args)

            assert exc_info.value.type == PolicyErrors.POLICY_DENIED


class TestRequestHumanApproval:
    """Test suite for the request_human_approval activity."""

    @pytest.mark.asyncio
    async def test_request_human_approval_raises_complete_async(self):
        """Test that request_human_approval raises complete async exception."""
        args = ["approval needed task"]

        with patch("src.activities.activities.activity") as mock_activity:
            mock_info = MagicMock()
            mock_info.task_token = b"test_token"
            mock_activity.info.return_value = mock_info
            mock_activity.heartbeat = MagicMock()
            mock_activity.raise_complete_async = MagicMock(
                side_effect=Exception("Complete async")
            )

            # The activity should raise complete async, which means it won't complete normally
            with pytest.raises(
                Exception
            ):  # This will raise an internal Temporal exception
                await request_human_approval(args)

    @pytest.mark.asyncio
    async def test_request_human_approval_sends_heartbeat(self):
        """Test that request_human_approval sends heartbeat with task token."""
        args = ["approval needed task"]

        with patch("src.activities.activities.activity") as mock_activity:
            # Mock the activity info and heartbeat
            mock_info = MagicMock()
            mock_info.task_token = b"test_token"
            mock_activity.info.return_value = mock_info
            mock_activity.heartbeat = MagicMock()
            mock_activity.raise_complete_async = MagicMock(
                side_effect=Exception("Complete async")
            )

            with pytest.raises(Exception):
                await request_human_approval(args)

            # Verify heartbeat was called with hex representation of task token
            mock_activity.heartbeat.assert_called_once_with("746573745f746f6b656e")


class TestExecuteAgentTask:
    """Test suite for the execute_agent_task activity."""

    @pytest.mark.asyncio
    async def test_execute_agent_task_success(self):
        """Test successful execution of agent task."""
        args = ["deploy application"]

        with patch("src.activities.activities.activity") as mock_activity:
            mock_info = MagicMock()
            mock_info.attempt = 3  # Third attempt should succeed
            mock_activity.info.return_value = mock_info
            mock_activity.logger = MagicMock()
            result = await execute_agent_task(args)
            assert result == "SUCCESS"

    @pytest.mark.asyncio
    async def test_execute_agent_task_with_retry_simulation(self):
        """Test that execute_agent_task can handle retry simulation."""
        args = ["task with potential retries"]

        with patch("src.activities.activities.activity") as mock_activity:
            # Mock activity info to simulate different attempt numbers
            mock_info = MagicMock()
            mock_info.attempt = 3  # Third attempt should succeed
            mock_activity.info.return_value = mock_info
            mock_activity.logger = MagicMock()

            result = await execute_agent_task(args)
            assert result == "SUCCESS"

    @pytest.mark.asyncio
    async def test_execute_agent_task_logs_correctly(self):
        """Test that execute_agent_task logs the correct information."""
        args = ["test logging task"]

        with patch("src.activities.activities.activity") as mock_activity:
            mock_info = MagicMock()
            mock_info.attempt = 3
            mock_activity.info.return_value = mock_info
            mock_activity.logger = MagicMock()

            result = await execute_agent_task(args)

            # Verify logging calls
            assert mock_activity.logger.info.call_count >= 2
            assert result == "SUCCESS"


class TestCleanupTask:
    """Test suite for the cleanup_task activity."""

    @pytest.mark.asyncio
    async def test_cleanup_task_success(self):
        """Test successful execution of cleanup task."""
        args = ["cleanup test resources"]

        with patch("src.activities.activities.activity") as mock_activity:
            mock_activity.logger = MagicMock()
            # cleanup_task returns None
            result = await cleanup_task(args)
            assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_task_with_empty_args(self):
        """Test cleanup task with empty arguments."""
        args = []

        with patch("src.activities.activities.activity") as mock_activity:
            mock_activity.logger = MagicMock()
            result = await cleanup_task(args)
            assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_task_logs_correctly(self):
        """Test that cleanup_task logs the correct information."""
        args = ["test cleanup logging"]

        with patch("src.activities.activities.activity") as mock_activity:
            mock_activity.logger = MagicMock()

            result = await cleanup_task(args)

            # Verify logging was called
            mock_activity.logger.info.assert_called()
            assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_task_handles_multiple_args(self):
        """Test cleanup task with multiple arguments."""
        args = ["resource1", "resource2", "resource3"]

        with patch("src.activities.activities.activity") as mock_activity:
            mock_activity.logger = MagicMock()
            result = await cleanup_task(args)
            assert result is None


class TestPolicyErrors:
    """Test suite for PolicyErrors constants."""

    def test_policy_errors_constants(self):
        """Test that PolicyErrors constants are defined correctly."""
        assert PolicyErrors.POLICY_DENIED == "POLICY_DENIED"


if __name__ == "__main__":
    pytest.main([__file__])
