"""Grassmarket configuration — one generation, no version suffixes (CLAUDE.md Layout).

Fail-loud: a missing required setting refuses to start rather than defaulting to something
insecure. `GM_JWT_SECRET` has no default — construct `Settings` without it and the app will not
boot. Production additionally refuses SQLite and the placeholder secret.

Settings are read once via `get_settings()`. Tests construct `Settings(...)` directly with
explicit overrides — never by mutating a global.
"""

from __future__ import annotations

import functools

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The exact placeholder shipped in .env.example; production refuses to boot with it (below).
_PLACEHOLDER_SECRET = "change-me-in-real-environments-use-a-48-byte-urlsafe-token"  # noqa: E501  # pragma: allowlist secret
# A valid dev/test Fernet key so local ingestion works out of the box; prod refuses it (below).
_PLACEHOLDER_TRANSCRIPT_KEY = "XLLj_pbyBm78QwMhfP5tNhN4Z9JfimC8EhnHa_d4FmM="  # noqa: E501  # pragma: allowlist secret


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,  # lets tests construct Settings(jwt_secret=...) by field name
    )

    env: str = Field(default="local", validation_alias=AliasChoices("GM_ENV", "ENV"))
    debug: bool = Field(default=False, validation_alias=AliasChoices("GM_DEBUG", "DEBUG"))

    # Railway injects DATABASE_URL for managed Postgres; local/CI default to SQLite.
    database_url: str = Field(
        default="sqlite+pysqlite:///./local.db",
        validation_alias=AliasChoices("GM_DATABASE_URL", "DATABASE_URL"),
    )

    # No default — a missing JWT secret is a boot failure, never a weak default.
    jwt_secret: str = Field(validation_alias=AliasChoices("GM_JWT_SECRET", "JWT_SECRET"))
    jwt_algorithm: str = Field(default="HS256", validation_alias="GM_JWT_ALGORITHM")
    jwt_access_ttl_minutes: int = Field(default=30, validation_alias="GM_JWT_ACCESS_TTL_MINUTES")
    jwt_issuer: str = Field(
        default="advisors.bruntsfieldcapital.com", validation_alias="GM_JWT_ISSUER"
    )
    jwt_audience: str = Field(default="bruntsfield", validation_alias="GM_JWT_AUDIENCE")

    # Transcript encryption at rest (GRS-0029). A url-safe base64 Fernet key; the dev default
    # works locally, production refuses it (below).
    transcript_encryption_key: str = Field(
        default=_PLACEHOLDER_TRANSCRIPT_KEY,
        validation_alias=AliasChoices("GM_TRANSCRIPT_ENCRYPTION_KEY", "TRANSCRIPT_ENCRYPTION_KEY"),
    )
    # Upload guard (GRS-0029): reject media larger than this before scanning/transcribing.
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, validation_alias="GM_MAX_UPLOAD_BYTES")

    invite_ttl_hours: int = Field(default=168, validation_alias="GM_INVITE_TTL_HOURS")
    # The canonical advisory-app origin — the OAuth callback redirects here, and it is always CORS-
    # allowed. Back-compat: GM_FRONTEND_ORIGIN still works unchanged.
    frontend_origin: str = Field(
        default="http://localhost:3000", validation_alias="GM_FRONTEND_ORIGIN"
    )
    # Additional CORS-allowed origins (GRS-0074), comma-separated — e.g. the public Bruntsfield
    # Capital marketing site that carries "LOG IN". Empty by default.
    frontend_origins_extra: str = Field(default="", validation_alias="GM_FRONTEND_ORIGINS")
    # One-time login hand-off code TTL (ADR-0024): short enough to bound replay across the redirect.
    login_handoff_ttl_seconds: int = Field(
        default=60, validation_alias="GM_LOGIN_HANDOFF_TTL_SECONDS"
    )

    @property
    def cors_origins(self) -> list[str]:
        """The CORS allow-list: the advisory app plus any GM_FRONTEND_ORIGINS extras, de-duped and
        order-preserving (advisory app first)."""
        ordered: list[str] = []
        extras = [o.strip() for o in self.frontend_origins_extra.split(",") if o.strip()]
        for origin in [self.frontend_origin, *extras]:
            if origin and origin not in ordered:
                ordered.append(origin)
        return ordered

    # --- Google OAuth (ADR-0024) ---
    # Operator-supplied (Google Cloud Console); no default — an unconfigured OAuth client makes the
    # /auth/google/* endpoints refuse loud (GoogleOAuthNotConfiguredError → 503), never a weak
    # fallback. None until the operator provisions them.
    google_client_id: str | None = Field(
        default=None, validation_alias=AliasChoices("GM_GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_ID")
    )
    google_client_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GM_GOOGLE_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET"),
    )
    google_redirect_uri: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GM_GOOGLE_REDIRECT_URI", "GOOGLE_REDIRECT_URI"),
    )

    @field_validator("database_url", mode="after")
    @classmethod
    def _normalise_db_scheme(cls, value: str) -> str:
        """Managed Postgres providers (Railway, Heroku) inject `postgres://` / `postgresql://`.
        We use psycopg 3, which SQLAlchemy only selects for the `postgresql+psycopg://` scheme —
        so rewrite the bare schemes rather than fail loud on a URL that is otherwise correct."""
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix) :]
        return value

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @model_validator(mode="after")
    def _refuse_insecure_production(self) -> Settings:
        if self.is_production:
            if self.jwt_secret == _PLACEHOLDER_SECRET or len(self.jwt_secret) < 32:
                raise ValueError(
                    "Refusing to run in production with a placeholder or short GM_JWT_SECRET. "
                    "Generate a strong secret (>=32 chars)."
                )
            if self.database_url.startswith("sqlite"):
                raise ValueError(
                    "Refusing to run in production on SQLite. Provide a Postgres DATABASE_URL."
                )
            if self.transcript_encryption_key == _PLACEHOLDER_TRANSCRIPT_KEY:
                raise ValueError(
                    "Refusing to run in production with the placeholder transcript key."
                    " Generate one with Fernet.generate_key()."
                )
        return self


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, constructed once. Fails loud if required env is absent."""
    return Settings()  # type: ignore[call-arg]  # values come from env / .env
