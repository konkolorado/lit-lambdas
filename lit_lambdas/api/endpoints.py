import uuid

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from pydantic import ValidationError

from api.models import Action, EnumerationQueryArgs, LambdaResponse
from api.repository import DynamoActionRepository
from api.responses import BadRequest, NotFound, Ok

logger = Logger(service="gw-api", utc=True)


def introspect(context) -> LambdaResponse:
    return Ok.as_json({"version": context.function_version, "schema": ""})


def enumerate(event: APIGatewayProxyEvent) -> LambdaResponse:
    raw_qargs = (
        {} if event["queryStringParameters"] is None else event["queryStringParameters"]
    )
    try:
        qargs = EnumerationQueryArgs(**raw_qargs)
    except ValidationError as ve:
        logger.info("Unable to parse query args", extra={"errors": ve.errors()})
        return BadRequest.as_json(ve.errors())

    uid = str(uuid.UUID(int=0))
    repo = DynamoActionRepository()
    if qargs.status:
        result = repo.get_actions_by_status(uid, qargs.status)
    elif qargs.created_at:
        result = repo.get_actions_by_created_at(
            uid, since=qargs.created_at.since, until=qargs.created_at.until
        )
    elif qargs.completed_at:
        result = repo.get_actions_by_completed_at(
            uid, since=qargs.completed_at.since, until=qargs.completed_at.until
        )
    else:
        result = repo.enumerate_actions_for_user(uid)
    return Ok.as_json(result)


def run(event: APIGatewayProxyEvent) -> LambdaResponse:
    # Do something interesting
    repo = DynamoActionRepository()
    action = Action(details={"endpoint": "run"}, created_by=uuid.UUID(int=0))
    repo.store_actions(action)
    return Ok.as_json(action)


def status(event: APIGatewayProxyEvent) -> LambdaResponse:
    uid = str(uuid.UUID(int=0))
    repo = DynamoActionRepository()

    assert event.path_parameters
    action_id = event.path_parameters["action_id"]
    action = repo.get_action_by_id(uid, action_id)

    if action is None:
        logger.info(
            "Unable to find Action", extra={"user_id": uid, "action_id": action_id}
        )
        return NotFound.as_json(f"Action with ID {action_id} was not found.")
    return Ok.as_json(action)


def cancel(event: APIGatewayProxyEvent) -> LambdaResponse:
    return Ok.as_json({"Endpoint": "cancel"})


def release(event: APIGatewayProxyEvent) -> LambdaResponse:
    return Ok.as_json({"Endpoint": "release"})
