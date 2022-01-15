import datetime
import json
import typing as t
import uuid
from abc import ABC

from aws_lambda_powertools import Logger

from api.models import Action, LambdaResponse

logger = Logger(service="gw-api", utc=True)


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return str(obj)
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, Action):
            return obj.dict()
        else:
            return json.JSONEncoder.default(self, obj)


class BaseResponse(ABC):
    http_status: int
    headers: t.Dict[str, str] = {"Content-Type": "application/json"}

    @classmethod
    def as_json(cls, body: t.Any) -> LambdaResponse:
        return {
            "statusCode": cls.http_status,
            "headers": cls.headers,
            "body": json.dumps(body, cls=Encoder),
        }


class BaseError(ABC):
    http_status: int
    headers: t.Dict[str, str] = {"Content-Type": "application/json"}

    @classmethod
    def as_json(
        cls,
        message: t.Optional[t.Union[str, dict, list]] = None,
    ) -> LambdaResponse:
        return {
            "statusCode": cls.http_status,
            "headers": cls.headers,
            "body": json.dumps(
                {
                    "request_id": logger.get_correlation_id(),
                    "error_code": cls.__name__,
                    "details": json.dumps(message, cls=Encoder),
                },
                cls=Encoder,
            ),
        }


class Ok(BaseResponse):
    http_status = 200


class Accepted(BaseResponse):
    http_status = 202


class InternalServerError(BaseError):
    http_status: int = 500


class BadRequest(BaseError):
    http_status = 409


class NotFound(BaseError):
    http_status = 404
