import ipaddress
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from hpm.errors import BindRefused


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "dev"
    database_url: str = "sqlite:///./data/hpm.sqlite"
    host: str = "127.0.0.1"
    port: int = 8102
    allow_network_bind: bool = False
    cors_origins: str = "http://127.0.0.1:5102,http://localhost:5102"
    max_upload_bytes: int = 10 * 1024 * 1024
    max_rows: int = 50_000
    stale_job_seconds: int = 900
    seed_on_startup: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]

    @property
    def demo_banner(self) -> bool:
        return self.app_env == "demo"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def assert_bind_allowed(host: str, allow_network_bind: bool) -> None:
    """Refuse a non-loopback bind unless the operator opts in explicitly."""
    if allow_network_bind:
        return
    normalized = host.strip().lower()
    if normalized == "localhost":
        return
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError as exc:
        raise BindRefused(
            f"Refusing to bind host {host!r} without ALLOW_NETWORK_BIND=true"
        ) from exc
    if not address.is_loopback:
        raise BindRefused(
            f"Refusing to bind non-loopback host {host!r} without ALLOW_NETWORK_BIND=true"
        )


def host_from_argv(argv: list[str]) -> str | None:
    if "--host" in argv:
        index = argv.index("--host")
        if index + 1 < len(argv):
            return argv[index + 1]
    for arg in argv:
        if arg.startswith("--host="):
            return arg.split("=", 1)[1]
    return None
