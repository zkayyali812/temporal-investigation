# Unit Tests

This directory contains comprehensive unit tests for the Temporal workflows and activities.

## Structure

```
src/tests/
├── activities/           # Tests for Temporal activities
│   ├── __init__.py
│   └── test_activities.py
├── workflows/            # Tests for Temporal workflows  
│   ├── __init__.py
│   └── test_workflows.py
├── __init__.py
└── README.md
```

## Test Coverage

### Activity Tests (`activities/test_activities.py`)
- **CheckPolicy**: Tests policy validation, forbidden keywords, case sensitivity
- **RequestHumanApproval**: Tests async completion and heartbeat functionality
- **ExecuteAgentTask**: Tests successful execution, retry simulation, and logging
- **CleanupTask**: Tests resource cleanup with various argument scenarios
- **PolicyErrors**: Tests error constants

### Workflow Tests (`workflows/test_workflows.py`)
- **SampleWorkflow**: Tests initialization, signal handling, approval/rejection logic
- **DynamicWorkflow**: Tests YAML configuration parsing, multiple activities, error handling

## Running Tests

### Run all tests:
```bash
python -m pytest src/tests/ -v
```

### Run activity tests only:
```bash
python -m pytest src/tests/activities/ -v
```

### Run workflow tests only:
```bash
python -m pytest src/tests/workflows/ -v
```

### Run a specific test:
```bash
python -m pytest src/tests/activities/test_activities.py::TestCheckPolicy::test_check_policy_approve_valid_args -v
```

## Test Features

- **Async Testing**: All tests use `pytest-asyncio` for proper async/await testing
- **Mocking**: Uses `unittest.mock` to isolate units under test
- **Comprehensive Coverage**: Tests both success and failure scenarios
- **Isolated Testing**: Activities tested independently without requiring Temporal server
- **Focused Workflow Testing**: Tests workflow logic without full integration

## Dependencies

The tests require the following packages (already included in `requirements.txt`):
- `pytest`
- `pytest-asyncio` 
- `pytest-mock`
- `temporalio`

## Test Design

- **Activity Tests**: Test activities directly with mocked Temporal context
- **Workflow Tests**: Focus on workflow logic, signal handling, and configuration parsing
- **No External Dependencies**: Tests run without requiring a running Temporal server
- **Fast Execution**: All tests complete in under 20 seconds

## Adding New Tests

When adding new activities or workflows:

1. **For Activities**: Add test methods to `test_activities.py` following the existing pattern
2. **For Workflows**: Add test methods to `test_workflows.py` focusing on workflow logic
3. **Use Mocking**: Mock external dependencies to keep tests isolated
4. **Test Edge Cases**: Include tests for error conditions and edge cases
