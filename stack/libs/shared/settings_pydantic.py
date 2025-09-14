from pydantic import BaseSettings, Field  # pants: no-infer-dep


class Settings(BaseSettings):
    env: str = Field(default="local")
    log_level: str = Field(default="INFO")

    # Common AWS-related
    aws_region: str = Field(default="eu-west-2")

    # Optional service-specific
    queue_url: str | None = None
    status_bucket: str | None = None
    service_name: str = Field(default="app")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
