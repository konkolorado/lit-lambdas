import datetime
import json
import typing as t
import uuid
from abc import ABC, abstractmethod

import arrow
import boto3
from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import Attr, Key
from mypy_boto3_dynamodb import ServiceResource

from api.config import Settings
from api.models import Action, ActionStatus

logger = Logger(service="gw-api", utc=True)


class ActionRepository(ABC):
    @abstractmethod
    def store_actions(self, *actions: Action):
        ...

    @abstractmethod
    def get_action_by_id(self, user_id: str, action_id: str) -> t.Optional[Action]:
        ...

    @abstractmethod
    def enumerate_actions_for_user(self, user_id: str) -> t.List[Action]:
        ...

    @abstractmethod
    def get_actions_by_status(
        self, user_id: str, status: ActionStatus
    ) -> t.List[Action]:
        ...

    @abstractmethod
    def get_actions_by_created_at(
        self,
        user_id: str,
        *,
        since: t.Optional[datetime.datetime] = None,
        until: t.Optional[datetime.datetime] = None,
    ) -> t.List[Action]:
        ...

    @abstractmethod
    def get_actions_by_completed_at(
        self,
        user_id: str,
        *,
        since: t.Optional[datetime.datetime] = None,
        until: t.Optional[datetime.datetime] = None,
    ) -> t.List[Action]:
        ...


class DynamoActionRepository(ActionRepository):
    def action_to_item(self, action: Action) -> t.Dict:
        return {
            "created_by": str(action.created_by),
            "action_id": f"action#{str(action.id)}",
            "created_at#id": f"{action.created_at}#{str(action.id)}",
            "completed_at#id": f"{action.completed_at}#{str(action.id)}",
            "status#id": f"{action.status}#{str(action.id)}",
            "expires_at": int(action.expires_at.timestamp()),
            "action": json.loads(action.json()),
        }

    def __init__(self):
        settings = Settings()
        logger.info(
            "Creating DynamoDB client",
            extra={
                "region_name": settings.boto_client_config.region_name,
                "connect_timeout": settings.boto_client_config.connect_timeout,
                "retries": settings.boto_client_config.retries,
                "endpoint_url": settings.dynamo_endpoint_url,
            },
        )
        dynamo: ServiceResource = boto3.resource(
            "dynamodb",
            config=settings.boto_client_config,
            endpoint_url=settings.dynamo_endpoint_url,
            # aws_access_key_id="TEST",
            # aws_secret_access_key="TEST",
        )
        self.table = dynamo.Table(settings.dynamo_table_name)

    def enumerate_actions(self) -> t.List[Action]:
        items = self.table.scan().get("Items", [])
        return [Action(**item["action"]) for item in items]

    def store_actions(self, *actions: Action):
        with self.table.batch_writer() as batch:
            for a in actions:
                batch.put_item(Item=self.action_to_item(a))

    def enumerate_actions_for_user(self, user_id: str) -> t.List[Action]:
        now = int(arrow.utcnow().timestamp())
        response = self.table.query(
            KeyConditionExpression=Key("created_by").eq(user_id),
            ReturnConsumedCapacity="TOTAL",
            FilterExpression=Attr("expires_at").gte(now),
        )
        logger.info(
            "Dynamo query consumed capacity", extra=response["ConsumedCapacity"]
        )
        return [Action(**item["action"]) for item in response["Items"]]

    def get_action_by_id(self, user_id: str, action_id: str) -> t.Optional[Action]:
        now = int(arrow.utcnow().timestamp())
        response = self.table.query(
            KeyConditionExpression=Key("created_by").eq(user_id)
            & Key("action_id").eq(f"action#{action_id}"),
            ReturnConsumedCapacity="INDEXES",
            FilterExpression=Attr("expires_at").gte(now),
        )
        logger.info(
            "Dynamo query consumed capacity", extra=response["ConsumedCapacity"]
        )
        if response["Count"] == 0:
            return None
        return Action(**response["Items"][0]["action"])

    def get_actions_by_status(
        self, user_id: str, status: ActionStatus
    ) -> t.List[Action]:
        now = int(arrow.utcnow().timestamp())
        response = self.table.query(
            IndexName="ActionStatusLSI",
            KeyConditionExpression=Key("created_by").eq(user_id)
            & Key("status#id").begins_with(f"{status}"),
            ReturnConsumedCapacity="INDEXES",
            FilterExpression=Attr("expires_at").gte(now),
        )
        logger.info(
            "Dynamo query consumed capacity", extra=response["ConsumedCapacity"]
        )
        return [Action(**item["action"]) for item in response["Items"]]

    def get_actions_by_created_at(
        self,
        user_id: str,
        *,
        since: t.Optional[datetime.datetime] = None,
        until: t.Optional[datetime.datetime] = None,
    ) -> t.List[Action]:
        if since is None:
            since = arrow.get(datetime.datetime.min).to("utc").datetime
        if until is None:
            until = arrow.get(datetime.datetime.max).to("utc").datetime

        lower_bound = f"{since}#{uuid.UUID(int=0)}"
        upper_bound = f"{until}#ffffffff-ffff-ffff-ffff-ffffffffffff"
        now = int(arrow.utcnow().timestamp())

        response = self.table.query(
            IndexName="CreatedAtLSI",
            KeyConditionExpression=Key("created_by").eq(user_id)
            & Key("created_at#id").between(lower_bound, upper_bound),
            ReturnConsumedCapacity="INDEXES",
            FilterExpression=Attr("expires_at").gte(now),
        )
        logger.info(
            "Dynamo query consumed capacity", extra=response["ConsumedCapacity"]
        )
        return [Action(**item["action"]) for item in response["Items"]]

    def get_actions_by_completed_at(
        self,
        user_id: str,
        *,
        since: t.Optional[datetime.datetime] = None,
        until: t.Optional[datetime.datetime] = None,
    ) -> t.List[Action]:
        if since is None:
            since = arrow.get(datetime.datetime.min).to("utc").datetime
        if until is None:
            until = arrow.get(datetime.datetime.max).to("utc").datetime

        lower_bound = f"{since}#{uuid.UUID(int=0)}"
        upper_bound = f"{until}#ffffffff-ffff-ffff-ffff-ffffffffffff"
        now = int(arrow.utcnow().timestamp())

        response = self.table.query(
            IndexName="CompletedAtLSI",
            KeyConditionExpression=Key("created_by").eq(user_id)
            & Key("completed_at#id").between(lower_bound, upper_bound),
            ReturnConsumedCapacity="INDEXES",
            FilterExpression=Attr("expires_at").gte(now),
        )
        logger.info(
            "Dynamo query consumed capacity", extra=response["ConsumedCapacity"]
        )
        return [Action(**item["action"]) for item in response["Items"]]
