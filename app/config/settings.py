"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from utils.env import env_int, env_str


def get_workspace_root() -> Path:
    """Return the workspace root that contains the app package."""

    return Path(__file__).resolve().parents[2]


def _normalize_dir(path_value: str) -> str:
    normalized = (
        path_value
        if os.path.isabs(path_value)
        else os.path.abspath(os.path.join(get_workspace_root(), path_value))
    )
    os.makedirs(normalized, exist_ok=True)
    return normalized


@dataclass(frozen=True)
class AppConfig:
    """Process-wide application configuration."""

    app_name: str = "dudu-agent-core"
    port: int = 8000
    logs_dir: str = "./logs"
    log_level: str = "DEBUG"
    cors_origins: tuple[str, ...] = ("*",)
    rideclaw_base_url: str = "https://rideclaw.dudubashi.com"
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "dudu_agent_core"
    mysql_charset: str = "utf8mb4"


_APP_CONFIG: AppConfig | None = None


def build_app_config(**overrides: Any) -> AppConfig:
    """Build config from defaults, env vars, and call-site overrides."""

    config = AppConfig(
        port=env_int("DUDU_PORT", AppConfig.port),
        log_level=env_str("DUDU_LOG_LEVEL", AppConfig.log_level) or AppConfig.log_level,
        rideclaw_base_url=env_str(
            "DUDU_RIDECLAW_BASE_URL",
            AppConfig.rideclaw_base_url,
        )
        or AppConfig.rideclaw_base_url,
        mysql_host=env_str("DUDU_MYSQL_HOST", AppConfig.mysql_host)
        or AppConfig.mysql_host,
        mysql_port=env_int("DUDU_MYSQL_PORT", AppConfig.mysql_port),
        mysql_user=env_str("DUDU_MYSQL_USER", AppConfig.mysql_user)
        or AppConfig.mysql_user,
        mysql_password=env_str("DUDU_MYSQL_PASSWORD", AppConfig.mysql_password)
        or AppConfig.mysql_password,
        mysql_database=env_str("DUDU_MYSQL_DATABASE", AppConfig.mysql_database)
        or AppConfig.mysql_database,
    )

    resolved_overrides = {
        key: value for key, value in overrides.items() if value is not None
    }
    if resolved_overrides:
        config = replace(config, **resolved_overrides)

    return replace(config, logs_dir=_normalize_dir(config.logs_dir))


def init_app_config(**overrides: Any) -> AppConfig:
    """Rebuild and cache app configuration."""

    global _APP_CONFIG

    _APP_CONFIG = build_app_config(**overrides)
    return _APP_CONFIG


def get_app_config() -> AppConfig:
    """Return the cached config, building it on first access."""

    global _APP_CONFIG

    if _APP_CONFIG is None:
        _APP_CONFIG = build_app_config()
    return _APP_CONFIG


__all__ = [
    "AppConfig",
    "build_app_config",
    "get_app_config",
    "get_workspace_root",
    "init_app_config",
]
