import httpx
import structlog

from lit_lambdas.logs import init_logging
from lit_lambdas.models import LambdaEvent

init_logging()
logger = structlog.get_logger(__name__)


def handler(event, context):
    #logger.bind(request_id=context.aws_request_id)

    event = LambdaEvent(**event)
    r = httpx.get("https://www.example.org/")
    logger.info(r.status_code)
    logger.warning(event)


if __name__ == "__main__":
    handler({"name": 1}, {})
