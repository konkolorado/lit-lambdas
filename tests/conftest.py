import typing as t
import uuid
from dataclasses import dataclass

import boto3
import botocore
import pytest
from mypy_boto3_dynamodb import ServiceResource

from lit_lambdas.api.config import Settings
from lit_lambdas.api.repository import ActionRepository, DynamoActionRepository


@pytest.fixture
def lambda_context():
    """
    A mock lambda context object for testing
    """

    @dataclass
    class LambdaContext:
        function_name: str = "test"
        function_version: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:us-east-1:000000000:function:test"
        aws_request_id: str = str(uuid.UUID(int=0))

    return LambdaContext()


@pytest.fixture(scope="function")
def apigateway_event() -> t.Dict[str, t.Any]:
    return {
        "resource": "/my/path",
        "path": "/my/path",
        "httpMethod": "GET",
        "headers": {"header1": "value1", "header2": "value2"},
        "multiValueHeaders": {
            "header1": ["value1"],
            "header2": ["value1", "value2"],
        },
        "queryStringParameters": {"parameter1": "value1", "parameter2": "value"},
        "multiValueQueryStringParameters": {
            "parameter1": ["value1", "value2"],
            "parameter2": ["value"],
        },
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "id",
            "authorizer": {"claims": None, "scopes": None},
            "domainName": "id.execute-api.us-east-1.amazonaws.com",
            "domainPrefix": "id",
            "extendedRequestId": "request-id",
            "httpMethod": "GET",
            "identity": {
                "accessKey": None,
                "accountId": None,
                "caller": None,
                "cognitoAuthenticationProvider": None,
                "cognitoAuthenticationType": None,
                "cognitoIdentityId": None,
                "cognitoIdentityPoolId": None,
                "principalOrgId": None,
                "sourceIp": "IP",
                "user": None,
                "userAgent": "user-agent",
                "userArn": None,
                "clientCert": {
                    "clientCertPem": "CERT_CONTENT",
                    "subjectDN": "www.example.com",
                    "issuerDN": "Example issuer",
                    "serialNumber": "a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1:a1",
                    "validity": {
                        "notBefore": "May 28 12:30:02 2019 GMT",
                        "notAfter": "Aug  5 09:36:04 2021 GMT",
                    },
                },
            },
            "path": "/my/path",
            "protocol": "HTTP/1.1",
            "requestId": "id=",
            "requestTime": "04/Mar/2020:19:15:17 +0000",
            "requestTimeEpoch": 1583349317135,
            "resourceId": None,
            "resourcePath": "/my/path",
            "stage": "$default",
        },
        "pathParameters": None,
        "stageVariables": None,
        "body": "Hello from Lambda!",
        "isBase64Encoded": False,
    }


@pytest.fixture
def localstack_settings(monkeypatch) -> Settings:
    monkeypatch.setenv("APP_DYNAMO_TABLE_NAME", "tests")
    monkeypatch.setenv("APP_DYNAMO_ENDPOINT_URL", "http://localhost:4566")
    monkeypatch.setenv("APP_BOTO_CLIENT_REGION_NAME", "test")
    monkeypatch.setenv("APP_BOTO_CLIENT_CONNECTION_TIMEOUT", "1")
    monkeypatch.setenv("APP_BOTO_CLIENT_CONNECTION_RETRIES", "1")
    return Settings()


@pytest.fixture(scope="function")
def using_localstack(localstack_settings: Settings):
    dynamo: ServiceResource = boto3.resource(
        "dynamodb",
        config=localstack_settings.boto_client_config,
        endpoint_url=localstack_settings.dynamo_endpoint_url,
        aws_access_key_id="TEST",
        aws_secret_access_key="TEST",
    )
    try:
        table = dynamo.create_table(
            TableName=localstack_settings.dynamo_table_name,
            KeySchema=[
                {"AttributeName": "created_by", "KeyType": "HASH"},
                {"AttributeName": "action_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "created_by", "AttributeType": "S"},
                {"AttributeName": "action_id", "AttributeType": "S"},
                {"AttributeName": "created_at#id", "AttributeType": "S"},
                {"AttributeName": "completed_at#id", "AttributeType": "S"},
                {"AttributeName": "status#id", "AttributeType": "S"},
            ],
            LocalSecondaryIndexes=[
                {
                    "IndexName": "CreatedAtLSI",
                    "KeySchema": [
                        {"AttributeName": "created_by", "KeyType": "HASH"},
                        {"AttributeName": "created_at#id", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "CompletedAtLSI",
                    "KeySchema": [
                        {"AttributeName": "created_by", "KeyType": "HASH"},
                        {"AttributeName": "completed_at#id", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "ActionStatusLSI",
                    "KeySchema": [
                        {"AttributeName": "created_by", "KeyType": "HASH"},
                        {"AttributeName": "status#id", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
            ProvisionedThroughput={"ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
        )
        dynamo.meta.client.update_time_to_live(
            TableName=localstack_settings.dynamo_table_name,
            TimeToLiveSpecification={"Enabled": True, "AttributeName": "expires_at"},
        )
    except dynamo.meta.client.exceptions.ResourceInUseException:
        table = dynamo.Table(localstack_settings.dynamo_table_name)
    except botocore.exceptions.ClientError as ce:
        raise

    yield table
    table.delete()


@pytest.fixture
def repo(using_localstack) -> ActionRepository:
    return DynamoActionRepository()
