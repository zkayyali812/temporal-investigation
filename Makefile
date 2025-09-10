.PHONY: reqs run-server run-worker sample-workflow approve-workflow reject-workflow policy-denied-workflow schedule-workflow unit-tests

reqs:  ## Install requirements
	pip install -r requirements.txt

run-server:  ## Run the Temporal server
	temporal server start-dev # --db-filename=app.db

run-worker:  ## Start the Temporal worker
	python -m src.worker.main

sample-workflow:  ## Kickoff the sample workflow (Requires HITL approval)
	python run_sample_workflow.py start "Execute important task"

approve-task:  ## Approve a given task
	@read -p "Enter the task token: " task_token_input; \
	if [ -z "$$task_token_input" ]; then \
		echo "Error: task token cannot be empty."; \
		exit 1; \
	fi; \
	python run_sample_workflow.py signal $$task_token_input approve;

reject-task:  ## Reject a given task
	@read -p "Enter the task token: " task_token_input; \
	if [ -z "$$task_token_input" ]; then \
		echo "Error: task_token cannot be empty."; \
		exit 1; \
	fi; \
	python run_sample_workflow.py signal $$task_token_input reject;

schedule-workflow:  ## Schedule a workflow
	python run_sample_workflow.py schedule

unit-test:  ## Run the unit tests
	python -m pytest .

dynamic-workflow:  ## Start a dynamic workflow
	python run_dynamic_workflow.py --workflow-definition workflow_definition.yaml

complex-workflow:  ## Start a complex workflow
	python run_dynamic_workflow.py --workflow-definition workflow_definition_complex_example.yaml

dataflow-workflow:  ## Start a dataflow workflow
	python run_dynamic_workflow.py --workflow-definition workflow_definition_data_flow.yaml

complex-dataflow-workflow:  ## Start a complex dataflow workflow
	python run_dynamic_workflow.py --workflow-definition workflow_definition_complex_data_flow.yaml
