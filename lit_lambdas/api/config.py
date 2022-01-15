import typing as t

from botocore.config import Config as BotoClientConfig
from pydantic import BaseSettings


class Settings(BaseSettings):
    dynamo_table_name: str = "actions"
    dynamo_endpoint_url: t.Optional[str] = None
    dynamo_item_ttl_s: int = 60 * 60 * 24 * 31  # 1 month

    boto_client_region_name: str = "us-east-1"
    boto_client_connection_timeout: int = 30
    boto_client_connection_retries: int = 2

    @property
    def boto_client_config(self) -> BotoClientConfig:
        return BotoClientConfig(
            connect_timeout=self.boto_client_connection_timeout,
            retries={"total_max_attempts": self.boto_client_connection_retries},
            region_name=self.boto_client_region_name,
        )

    class Config:
        env_prefix = "APP_"
