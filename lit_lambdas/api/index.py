from os import stat

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    event_source,
)

from api.endpoints import enumerate, introspect, release, run, status
from api.models import HttpMethod, LambdaResponse
from api.responses import NotFound

logger = Logger(service="gw-api", utc=True)


@logger.inject_lambda_context
@event_source(data_class=APIGatewayProxyEvent)
def handler(event: APIGatewayProxyEvent, context) -> LambdaResponse:
    logger.set_correlation_id(event.request_context.request_id)
    if event.path == "/" and event.http_method.upper() == HttpMethod.GET:
        logger.info("Dispatching event to instrospect")
        return introspect(context)
    elif event.path == "/actions" and event.http_method == HttpMethod.GET:
        logger.info("Dispatching event to enumerate")
        return enumerate(event)
    elif event.path == "/actions" and event.http_method == HttpMethod.POST:
        logger.info("Dispatching event to run")
        return run(event)
    elif event.path.startswith("/actions/") and event.http_method == HttpMethod.GET:
        logger.info(f"Dispatching event to status")
        return status(event)
    elif event.path.startswith("/actions/") and event.http_method == HttpMethod.DELETE:
        logger.info(f"Dispatching event to release")
        return release(event)
    else:
        logger.warning(
            "Unable to dispatch event",
            extra={
                "event_path": event.path,
                "event_http_method": event.http_method,
            },
        )
        return NotFound.as_json()
