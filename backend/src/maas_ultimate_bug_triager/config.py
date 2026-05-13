from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel


class LaunchpadConfig(BaseModel):
    oauth_token: str
    oauth_token_secret: str
    consumer_key: str = "maas-ultimate-bug-triager"


class AIConfig(BaseModel):
    model: str = "gemini-2.5-pro"
    api_key: str


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]


class AppConfig(BaseModel):
    launchpad: LaunchpadConfig
    ai: AIConfig
    server: ServerConfig


def load_config(path: str | None = None) -> AppConfig:
    config_path = path or os.environ.get("MAAS_TRIAGER_CONFIG") or "config.yaml"
    data = yaml.safe_load(Path(config_path).read_text())
    return AppConfig.model_validate(data)
