.PHONY: help clean cfn stack unstack

PROJECT_VERSION := $(shell poetry version -s)

define HELPTEXT
Run "make <target>" where <target> is one of:
 help:       print this message
 clean:      remove generated project files and directories
 cfn:        generate and display the project's Cloudformation
 stack:      deploy the project onto AWS
 unstack:    remove the project from AWS
endef
export HELPTEXT

help:
	@echo "$$HELPTEXT"

clean:
	rm -rf .pytest_cache cdk.out .venv .coverage

cfn:
	@poetry run cdk synth

stack:
	-@cp {pyproject.toml,poetry.lock} lit_lambdas/;
	-poetry run cdk deploy LitLambdaStack --require-approval never;
	-@rm lit_lambdas/{pyproject.toml,poetry.lock}
	
unstack:
	poetry run cdk destroy LitLambdaStack --force