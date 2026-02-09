"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import List

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationConfig(BaseModel):
    """Configuration for a single application in the catalog."""

    name: str
    url: str
    status: str


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",
        extra="ignore",
    )

    # Application
    control_plane_env: str = Field(default="development", alias="CONTROL_PLANE_ENV")
    control_plane_host: str = Field(default="0.0.0.0", alias="CONTROL_PLANE_HOST")
    control_plane_port: int = Field(default=8000, alias="CONTROL_PLANE_PORT")
    control_plane_log_level: str = Field(default="info", alias="CONTROL_PLANE_LOG_LEVEL")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # OIDC / Zitadel
    oidc_issuer: str = Field(..., alias="OIDC_ISSUER")
    oidc_client_id: str = Field(..., alias="OIDC_CLIENT_ID")
    oidc_client_secret: str = Field(..., alias="OIDC_CLIENT_SECRET")
    oidc_redirect_uri: str = Field(..., alias="OIDC_REDIRECT_URI")
    oidc_scopes: str = Field(default="openid profile email", alias="OIDC_SCOPES")

    # Application Catalog (seed data)
    applications_pacs_name: str = Field(default="PACS", alias="APPLICATIONS__PACS__NAME")
    applications_pacs_url: str = Field(
        default="https://pacs.example.com/launch", alias="APPLICATIONS__PACS__URL"
    )
    applications_pacs_status: str = Field(default="active", alias="APPLICATIONS__PACS__STATUS")

    applications_erp_name: str = Field(default="ERP", alias="APPLICATIONS__ERP__NAME")
    applications_erp_url: str = Field(
        default="https://erp.example.com/launch", alias="APPLICATIONS__ERP__URL"
    )
    applications_erp_status: str = Field(default="active", alias="APPLICATIONS__ERP__STATUS")

    @property
    def applications(self) -> List[tuple[str, ApplicationConfig]]:
        """Get application catalog as list of (key, config) tuples."""
        return [
            (
                "pacs",
                ApplicationConfig(
                    name=self.applications_pacs_name,
                    url=self.applications_pacs_url,
                    status=self.applications_pacs_status,
                ),
            ),
            (
                "erp",
                ApplicationConfig(
                    name=self.applications_erp_name,
                    url=self.applications_erp_url,
                    status=self.applications_erp_status,
                ),
            ),
        ]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
