import pydantic
from pydantic import AnyHttpUrl, Field, HttpUrl

if pydantic.VERSION.startswith('1.'):
    from pydantic import BaseSettings
else:
    from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureActiveDirectory(BaseSettings):  # type: ignore[misc, valid-type]
    OPENAPI_CLIENT_ID: str = Field(default='')
    TENANT_ID: str = Field(default='')
    APP_CLIENT_ID: str = Field(default='')
    AUTH_URL: AnyHttpUrl = Field(default=AnyHttpUrl('https://dummy.com/'))
    CONFIG_URL: AnyHttpUrl = Field(default=AnyHttpUrl('https://dummy.com/'))
    TOKEN_URL: AnyHttpUrl = Field(default=AnyHttpUrl('https://dummy.com/'))
    GRAPH_SECRET: str = Field(default='')
    CLIENT_SECRET: str = Field(default='')


class Settings(AzureActiveDirectory):
    API_V1_STR: str = '/api/v1'

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: list[str | AnyHttpUrl] = ['http://localhost:8000']

    PROJECT_NAME: str = 'My Project'
    SENTRY_DSN: HttpUrl | None = None

    model_config = SettingsConfigDict(
        env_file='demo_project/.env', env_file_encoding='utf-8', extra='ignore', case_sensitive=True
    )


settings = Settings()
