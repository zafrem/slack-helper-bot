"""Channel configuration management."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class RetrievalParams(BaseModel):
    """RAG retrieval parameters for a channel."""

    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] = Field(default_factory=dict)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    namespace: str | None = None


class ChannelPolicies(BaseModel):
    """Policies for a channel."""

    pii_redaction: bool = True
    action_whitelist: list[str] = Field(default_factory=list)
    require_approval: bool = True
    max_actions_per_day: int = Field(default=100, ge=1)


class ChannelConfig(BaseModel):
    """Configuration for a single Slack channel."""

    channel_id: str
    name: str
    rag_index: str
    retrieval_params: RetrievalParams = Field(default_factory=RetrievalParams)
    approvers: list[str] = Field(default_factory=list)
    sla_minutes: int = Field(default=120, ge=1)
    first_response_minutes: int = Field(default=15, ge=1)
    policies: ChannelPolicies = Field(default_factory=ChannelPolicies)
    enabled: bool = True


class ChannelConfigManager:
    """Manager for channel configurations."""

    def __init__(self, config_path: str | Path = "config/channels.yaml") -> None:
        """Initialize the channel config manager.

        Args:
            config_path: Path to the channels configuration file
        """
        self.config_path = Path(config_path)
        self._channels: dict[str, ChannelConfig] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load channel configurations from YAML file."""
        if not self.config_path.exists():
            # Create default config if it doesn't exist
            self._create_default_config()
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "channels" not in data:
            return

        for channel_data in data["channels"]:
            config = ChannelConfig(**channel_data)
            self._channels[config.channel_id] = config

    def _create_default_config(self) -> None:
        """Create a default configuration file."""
        default_config = {
            "channels": [
                {
                    "channel_id": "C_EXAMPLE",
                    "name": "example-channel",
                    "rag_index": "kb-example",
                    "retrieval_params": {
                        "top_k": 5,
                        "filters": {},
                        "similarity_threshold": 0.7,
                    },
                    "approvers": [],
                    "sla_minutes": 120,
                    "first_response_minutes": 15,
                    "policies": {
                        "pii_redaction": True,
                        "action_whitelist": [],
                        "require_approval": True,
                        "max_actions_per_day": 100,
                    },
                    "enabled": False,
                }
            ]
        }

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    def get_channel_config(self, channel_id: str) -> ChannelConfig | None:
        """Get configuration for a specific channel.

        Args:
            channel_id: Slack channel ID

        Returns:
            Channel configuration or None if not found
        """
        return self._channels.get(channel_id)

    def is_channel_enabled(self, channel_id: str) -> bool:
        """Check if a channel is enabled.

        Args:
            channel_id: Slack channel ID

        Returns:
            True if channel is enabled, False otherwise
        """
        config = self.get_channel_config(channel_id)
        return config is not None and config.enabled

    def list_channels(self) -> list[ChannelConfig]:
        """List all configured channels.

        Returns:
            List of channel configurations
        """
        return list(self._channels.values())

    def reload(self) -> None:
        """Reload configurations from file."""
        self._channels.clear()
        self._load_config()
