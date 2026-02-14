from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'OpenCine Backend'
    log_level: str = 'INFO'

    database_url: str = Field(default='postgresql+psycopg://postgres:postgres@localhost:5432/opencine')
    redis_url: str = Field(default='redis://localhost:6379/0')

    llm_model_id: str = Field(default='meta-llama/Meta-Llama-3.1-70B-Instruct')
    llm_api_url: str | None = None
    llm_api_key: str | None = None

    flux_model_id: str = Field(default='black-forest-labs/FLUX.1-dev')
    ip_adapter_id: str = Field(default='h94/IP-Adapter-FaceID')
    hunyuan_model_id: str = Field(default='tencent/HunyuanVideo-I2V')

    output_dir: str = Field(default='outputs')
    s3_bucket: str = Field(default='opencine-renders')
    s3_region: str = Field(default='us-east-1')


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
