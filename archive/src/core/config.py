from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # AWS
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    aws_s3_jd_bucket: str
    aws_s3_jobs_path: str
    aws_s3_dev_jd_file: str

    # Pinecone
    pinecone_api_key: str
    pinecone_index_name: str = "de15-jd"

    # OpenAI
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-large"

    # Anthropic
    anthropic_api_key: str
    anthropic_chat_model: str = "claude-3-5-sonnet-latest"

    # LinkedIn
    linkedin_account: str
    linkedin_password: str

    # Application Configuration
    batch_size: int = 100
    cache_ttl: int = 300
    embedding_dimension: int = 3072

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings()
