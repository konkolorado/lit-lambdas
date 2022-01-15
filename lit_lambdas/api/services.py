from mypy_boto3_dynamodb import DynamoDBClient

from api.models import Action


def store_actions(db: DynamoDBClient, *actions: Action):
    ...


def get_actions(db: DynamoDBClient, *actions: Action):
    ...


def delete_actions(db: DynamoDBClient, *actions: Action):
    ...
