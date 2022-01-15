import datetime
import enum
import typing as t
import uuid
from logging import log

import arrow
from aws_lambda_powertools import Logger
from pydantic import BaseModel, Field, root_validator, validator

from api.config import Settings

logger = Logger(service="gw-api", utc=True)


def _get_now() -> datetime.datetime:
    return arrow.utcnow().replace(microsecond=0).datetime


def _get_datetime_min() -> datetime.datetime:
    return arrow.get(datetime.datetime.min).to("utc").datetime


def _get_datetime_max() -> datetime.datetime:
    return arrow.get(datetime.datetime.max).to("utc").datetime


class HttpMethod(str, enum.Enum):
    GET = "GET"
    PUT = "PUT"
    DELETE = "DELETE"
    POST = "POST"
    OPTIONS = "OPTIONS"


class ActionStatus(str, enum.Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PENDING = "PENDING"


class LambdaResponse(t.TypedDict):
    statusCode: int
    headers: t.Dict[str, str]
    body: str


class DatetimeRange(BaseModel):
    since: datetime.datetime = Field(default_factory=_get_datetime_min)
    until: datetime.datetime = Field(default_factory=_get_datetime_max)

    @validator("since")
    def parse_since(cls, v):
        if v is None or v is "":
            return _get_datetime_min()
        return v

    @validator("until")
    def parse_until(cls, v):
        if v is None or v is "":
            return _get_datetime_max()
        return v


class EnumerationQueryArgs(BaseModel):
    status: t.Optional[ActionStatus] = None
    created_at: t.Optional[DatetimeRange] = None
    completed_at: t.Optional[DatetimeRange] = None

    @validator("status")
    def parse_status(cls, v):
        if v is not None:
            if len(v.split(",")) > 2:
                raise ValueError(
                    "The status query parameter only supports single values"
                )
        return v

    @validator("created_at", "completed_at", pre=True)
    def parse_datetimes(cls, v):
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("Unable to parse datetime value")

        parts = v.split(",")
        if len(parts) > 2:
            raise ValueError(
                "Datetime query parameters only support start and end values"
            )
        if len(parts) == 1:
            return DatetimeRange(since=parts[0])
        if len(parts) == 2:
            return DatetimeRange(since=parts[0], until=parts[1])

    @root_validator
    def allow_only_one(cls, values):
        counter = [1 for v in values.values() if v is not None]
        if sum(counter) > 1:
            raise ValueError("Only a single query parameter is supported")
        return values


class Action(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime.datetime = Field(default_factory=_get_now)
    created_by: uuid.UUID
    completed_at: t.Optional[datetime.datetime] = None
    expires_at: datetime.datetime = None  # type: ignore
    status: ActionStatus = ActionStatus.PENDING
    details: t.Dict

    _expiration_ttl: int = Settings().dynamo_item_ttl_s

    @validator("expires_at", pre=True, always=True)
    def set_expiration(cls, _, values):
        expiration = arrow.get(values["created_at"]).shift(seconds=cls._expiration_ttl)
        return expiration.datetime

    @root_validator
    def trim_microseconds(cls, values):
        for field_name in ["created_at", "completed_at", "expires_at"]:
            field_value = values[field_name]
            if field_value is None:
                continue
            trimmed = arrow.get(field_value).replace(microsecond=0)
            values[field_name] = trimmed.datetime
        return values
