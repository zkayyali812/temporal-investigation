.PHONY: reqs run-server run-worker sample-workflow approve-workflow reject-workflow policy-denied-workflow schedule-workflow unit-tests

reqs:  ## Install requirements
	pip install -r requirements.txt

run-server:  ## Run the Temporal server
	temporal server start-dev # --db-filename=app.db

run-worker:  ## Start the Temporal worker
	python -m src.worker.main

sample-workflow:  ## Kickoff the sample workflow (Requires HITL approval)
	python run_sample_workflow.py start "Execute important task"

approve-workflow:  ## Approve the sample workflow
	@read -p "Enter the task token: " task_token_input; \
	if [ -z "$$task_token_input" ]; then \
		echo "Error: task token cannot be empty."; \
		exit 1; \
	fi; \
	python run_sample_workflow.py signal $$task_token_input approve;

reject-workflow:  ## Reject the sample workflow
	@read -p "Enter the task token: " task_token_input; \
	if [ -z "$$task_token_input" ]; then \
		echo "Error: task_token cannot be empty."; \
		exit 1; \
	fi; \
	python run_sample_workflow.py signal $$task_token_input reject;

policy-denied-workflow:  ## Start a workflow that will be denied by the policy
	python run_sample_workflow.py start "Forbidden task"

schedule-workflow:  ## Schedule a workflow
	python run_sample_workflow.py schedule

unit-test:  ## Run the unit tests
	python -m pytest .

dynamic-workflow:  ## Start a dynamic workflow
	python run_dynamic_workflow.py --workflow-definition workflow_definition.yaml
