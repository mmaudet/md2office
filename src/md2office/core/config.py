"""Configuration management for md2office."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import msgspec
import yaml

from md2office.core.exceptions import ConfigError


class StylesConfig(msgspec.Struct, frozen=True):
    """Style mapping configuration."""

    headings: dict[str, str] = msgspec.field(
        default_factory=lambda: {
            "h1": "Heading 1",
            "h2": "Heading 2",
            "h3": "Heading 3",
            "h4": "Heading 4",
            "h5": "Heading 5",
            "h6": "Heading 6",
        }
    )
    paragraph: dict[str, str] = msgspec.field(
        default_factory=lambda: {"normal": "Normal", "quote": "Quote"}
    )
    code: dict[str, str] = msgspec.field(
        default_factory=lambda: {"inline": "Code Char", "block": "Code Block"}
    )
    list_styles: dict[str, str] = msgspec.field(
        default_factory=lambda: {"bullet": "List Bullet", "number": "List Number"}
    )
    table: dict[str, Any] = msgspec.field(
        default_factory=lambda: {
            "style": "Table Grid",
            "header_bg": "4472C4",
            "header_text": "FFFFFF",
            "alternating_rows": True,
            "alt_row_bg": "D9E2F3",
        }
    )
    admonitions: dict[str, dict[str, str]] = msgspec.field(
        default_factory=lambda: {
            "NOTE": {"icon": "i", "color": "0969DA", "bg": "DDF4FF"},
            "TIP": {"icon": "tip", "color": "1A7F37", "bg": "DCFFE4"},
            "IMPORTANT": {"icon": "!", "color": "8250DF", "bg": "FBEFFF"},
            "WARNING": {"icon": "warn", "color": "9A6700", "bg": "FFF8C5"},
            "CAUTION": {"icon": "x", "color": "CF222E", "bg": "FFEBE9"},
        }
    )


class ServerConfig(msgspec.Struct, frozen=True):
    """Server configuration."""

    host: str = "0.0.0.0"
    port: int = 8080
    reload: bool = False
    workers: int = 1
    log_level: str = "info"


class StorageConfig(msgspec.Struct, frozen=True):
    """Storage configuration."""

    templates_dir: str = "templates"
    output_dir: str = "output"
    temp_dir: str = "temp"
    max_file_size: int = 10 * 1024 * 1024  # 10MB


class Config(msgspec.Struct, frozen=True):
    """Main application configuration."""

    server: ServerConfig = msgspec.field(default_factory=ServerConfig)
    storage: StorageConfig = msgspec.field(default_factory=StorageConfig)
    styles: StylesConfig = msgspec.field(default_factory=StylesConfig)
    default_template: str = "default"


def _find_config_file() -> Path | None:
    """Find configuration file in standard locations."""
    locations = [
        Path("config/config.yaml"),
        Path("config.yaml"),
        Path.home() / ".config" / "md2office" / "config.yaml",
        Path("/etc/md2office/config.yaml"),
    ]

    for path in locations:
        if path.exists():
            return path

    return None


def _load_yaml_config(path: Path) -> dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file: {e}")
    except OSError as e:
        raise ConfigError(f"Cannot read config file: {e}")


def _merge_env_vars(config: dict[str, Any]) -> dict[str, Any]:
    """Merge environment variables into configuration."""
    env_mappings = {
        "MD2OFFICE_HOST": ("server", "host"),
        "MD2OFFICE_PORT": ("server", "port"),
        "MD2OFFICE_LOG_LEVEL": ("server", "log_level"),
        "MD2OFFICE_TEMPLATES_DIR": ("storage", "templates_dir"),
        "MD2OFFICE_OUTPUT_DIR": ("storage", "output_dir"),
        "MD2OFFICE_DEFAULT_TEMPLATE": ("default_template",),
    }

    for env_var, path in env_mappings.items():
        value = os.environ.get(env_var)
        if value is not None:
            current = config
            for key in path[:-1]:
                current = current.setdefault(key, {})
            # Convert port to int if needed
            if env_var == "MD2OFFICE_PORT":
                value = int(value)
            current[path[-1]] = value

    return config


def load_config(config_path: Path | str | None = None) -> Config:
    """Load configuration from file and environment variables.

    Args:
        config_path: Optional path to configuration file.
                    If not provided, searches standard locations.

    Returns:
        Config object with merged settings.
    """
    config_data: dict[str, Any] = {}

    # Load from file if available
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
        config_data = _load_yaml_config(path)
    else:
        path = _find_config_file()
        if path:
            config_data = _load_yaml_config(path)

    # Merge environment variables
    config_data = _merge_env_vars(config_data)

    # Convert nested dicts to config structs
    try:
        return msgspec.convert(config_data, Config)
    except msgspec.ValidationError as e:
        raise ConfigError(f"Invalid configuration: {e}")


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get cached configuration instance."""
    return load_config()


def load_styles_mapping(path: Path | str | None = None) -> StylesConfig:
    """Load styles mapping from YAML file.

    Args:
        path: Path to styles-mapping.yaml file.

    Returns:
        StylesConfig object with style mappings.
    """
    if path is None:
        path = Path("config/styles-mapping.yaml")

    if not Path(path).exists():
        return StylesConfig()

    try:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return msgspec.convert(data, StylesConfig)
    except (yaml.YAMLError, msgspec.ValidationError) as e:
        raise ConfigError(f"Invalid styles mapping: {e}")
