#PROJECT_VERSION := `poetry version -s`
set positional-arguments

# Display all recipes
default:
    @just --list

# remove generated project files and directories
clean:
	rm -rf .pytest_cache cdk.out .venv .coverage

# start local instance of dependencies for testing
dependencies:
	docker compose up -d

# generate and display the project's Cloudformation
cfn:
	@poetry run cdk synth

# move poetry files during deployment
move:
    @cp {pyproject.toml,poetry.lock} lit_lambdas/

# remove poetry files post deployment
remove:
    @rm lit_lambdas/{pyproject.toml,poetry.lock,requirements.txt}

# deploy the project to AWS
deploy: move && remove
	-poetry run cdk deploy LitLambdaStack --require-approval never

# remove the project from AWS
destroy:
	poetry run cdk destroy LitLambdaStack --force

default-tests := ""
# test the project
test testnames=default-tests:
	poetry run pytest {{testnames}}
