import json
from unittest.mock import patch

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from lit_lambdas.api.index import handler
from lit_lambdas.api.models import Action
from lit_lambdas.api.responses import NotFound, Ok


def test_introspect_handler(apigateway_event, lambda_context):
    apigateway_event["path"] = "/"
    apigateway_event["httpMethod"] = "GET"
    event = APIGatewayProxyEvent(apigateway_event)
    with patch("lit_lambdas.api.index.introspect") as introspect_mock:
        handler(event, lambda_context)

    introspect_mock.assert_called_once()


def test_enumerate_handler(apigateway_event, lambda_context):
    apigateway_event["path"] = "/actions"
    apigateway_event["httpMethod"] = "GET"
    event = APIGatewayProxyEvent(apigateway_event)
    with patch("lit_lambdas.api.index.enumerate") as enumerate_mock:
        handler(event, lambda_context)

    enumerate_mock.assert_called_once()


def test_run_handler(apigateway_event, lambda_context):
    apigateway_event["path"] = "/actions"
    apigateway_event["httpMethod"] = "POST"
    event = APIGatewayProxyEvent(apigateway_event)
    with patch("lit_lambdas.api.index.run") as run_mock:
        handler(event, lambda_context)

    run_mock.assert_called_once()


def test_unknown_handler(apigateway_event, lambda_context):
    apigateway_event["path"] = "/some/fake/path"
    apigateway_event["httpMethod"] = "POST"
    event = APIGatewayProxyEvent(apigateway_event)
    response = handler(event, lambda_context)

    assert response == NotFound.as_json()


def test_run_returns_action(using_localstack, apigateway_event, lambda_context):
    apigateway_event["path"] = "/actions"
    apigateway_event["httpMethod"] = "POST"
    event = APIGatewayProxyEvent(apigateway_event)
    resp = handler(event, lambda_context)

    assert "headers" in resp and resp["headers"] == Ok.headers
    assert "statusCode" in resp and resp["statusCode"] == Ok.http_status
    assert "body" in resp and Action(**json.loads(resp["body"]))
