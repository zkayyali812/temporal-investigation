.PHONY: reqs run-server run-worker sample-workflow approve-workflow reject-workflow policy-denied-workflow schedule-workflow unit-tests

reqs:  ## Install requirements
	pip install -r requirements.txt

run-server:  ## Run the Temporal server
	temporal server start-dev --db-filename=app.db

run-worker:  ## Start the Temporal worker
	python -m src.worker.main

sample-workflow:  ## Kickoff the sample workflow (Requires HITL approval)
	python run_workflow.py start "Execute important task"

approve-workflow:  ## Approve the sample workflow
	@read -p "Enter the workflow_id: " workflow_id_input; \
	if [ -z "$$workflow_id_input" ]; then \
		echo "Error: workflow_id cannot be empty."; \
		exit 1; \
	fi; \
	python run_workflow.py signal $$workflow_id_input approve;

reject-workflow:  ## Reject the sample workflow
	@read -p "Enter the workflow_id: " workflow_id_input; \
	if [ -z "$$workflow_id_input" ]; then \
		echo "Error: workflow_id cannot be empty."; \
		exit 1; \
	fi; \
	python run_workflow.py signal $$workflow_id_input reject;

policy-denied-workflow:  ## Start a workflow that will be denied by the policy
	python run_workflow.py start "Forbidden task"

schedule-workflow:  ## Schedule a workflow
	python run_workflow.py schedule

unit-test:  ## Run the unit tests
	python -m pytest .
