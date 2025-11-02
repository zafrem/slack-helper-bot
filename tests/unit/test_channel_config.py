"""Tests for channel configuration."""

import pytest
import yaml
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.config.channel_config import (
    ChannelConfigManager,
    ChannelConfig,
    RetrievalParams,
    ChannelPolicies,
)


@pytest.fixture
def temp_config_file():
    """Create a temporary config file."""
    config_data = {
        "channels": [
            {
                "channel_id": "C123",
                "name": "test-channel",
                "rag_index": "test-index",
                "retrieval_params": {
                    "top_k": 5,
                    "filters": {"product": "core"},
                    "similarity_threshold": 0.7,
                },
                "approvers": ["U111", "U222"],
                "sla_minutes": 120,
                "first_response_minutes": 15,
                "policies": {
                    "pii_redaction": True,
                    "action_whitelist": ["restart_service"],
                    "require_approval": True,
                },
                "enabled": True,
            },
            {
                "channel_id": "C456",
                "name": "disabled-channel",
                "rag_index": "disabled-index",
                "enabled": False,
            },
        ]
    }

    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        yield f.name

    Path(f.name).unlink()


def test_load_config(temp_config_file):
    """Test loading configuration from file."""
    manager = ChannelConfigManager(temp_config_file)

    channels = manager.list_channels()
    assert len(channels) == 2

    # Check first channel
    config = manager.get_channel_config("C123")
    assert config is not None
    assert config.name == "test-channel"
    assert config.rag_index == "test-index"
    assert config.sla_minutes == 120
    assert config.enabled is True


def test_get_channel_config(temp_config_file):
    """Test retrieving specific channel config."""
    manager = ChannelConfigManager(temp_config_file)

    config = manager.get_channel_config("C123")
    assert config is not None
    assert config.channel_id == "C123"
    assert config.name == "test-channel"

    # Test retrieval params
    assert config.retrieval_params.top_k == 5
    assert config.retrieval_params.filters == {"product": "core"}
    assert config.retrieval_params.similarity_threshold == 0.7

    # Test approvers
    assert len(config.approvers) == 2
    assert "U111" in config.approvers

    # Test policies
    assert config.policies.pii_redaction is True
    assert "restart_service" in config.policies.action_whitelist


def test_get_channel_config_not_found(temp_config_file):
    """Test retrieving non-existent channel."""
    manager = ChannelConfigManager(temp_config_file)

    config = manager.get_channel_config("C999")
    assert config is None


def test_is_channel_enabled(temp_config_file):
    """Test checking if channel is enabled."""
    manager = ChannelConfigManager(temp_config_file)

    assert manager.is_channel_enabled("C123") is True
    assert manager.is_channel_enabled("C456") is False
    assert manager.is_channel_enabled("C999") is False


def test_list_channels(temp_config_file):
    """Test listing all channels."""
    manager = ChannelConfigManager(temp_config_file)

    channels = manager.list_channels()
    assert len(channels) == 2

    channel_ids = [c.channel_id for c in channels]
    assert "C123" in channel_ids
    assert "C456" in channel_ids


def test_reload_config(temp_config_file):
    """Test reloading configuration."""
    manager = ChannelConfigManager(temp_config_file)

    # Initial load
    assert len(manager.list_channels()) == 2

    # Modify file
    config_data = {
        "channels": [
            {
                "channel_id": "C789",
                "name": "new-channel",
                "rag_index": "new-index",
                "enabled": True,
            }
        ]
    }

    with open(temp_config_file, "w") as f:
        yaml.dump(config_data, f)

    # Reload
    manager.reload()

    # Verify new config
    channels = manager.list_channels()
    assert len(channels) == 1
    assert channels[0].channel_id == "C789"


def test_create_default_config():
    """Test creating default config when file doesn't exist."""
    with NamedTemporaryFile(delete=True, suffix=".yaml") as f:
        config_path = f.name

    # File doesn't exist, should create default
    manager = ChannelConfigManager(config_path)

    channels = manager.list_channels()
    assert len(channels) == 1
    assert channels[0].channel_id == "C_EXAMPLE"
    assert channels[0].enabled is False

    # Clean up
    Path(config_path).unlink()


def test_retrieval_params_defaults():
    """Test default retrieval parameters."""
    params = RetrievalParams()

    assert params.top_k == 5
    assert params.filters == {}
    assert params.similarity_threshold == 0.7
    assert params.namespace is None


def test_channel_policies_defaults():
    """Test default channel policies."""
    policies = ChannelPolicies()

    assert policies.pii_redaction is True
    assert policies.action_whitelist == []
    assert policies.require_approval is True
    assert policies.max_actions_per_day == 100


def test_channel_config_model():
    """Test ChannelConfig model creation."""
    config = ChannelConfig(
        channel_id="C123",
        name="test",
        rag_index="test-index",
    )

    assert config.channel_id == "C123"
    assert config.name == "test"
    assert config.enabled is True
    assert config.sla_minutes == 120
    assert config.first_response_minutes == 15
    assert isinstance(config.retrieval_params, RetrievalParams)
    assert isinstance(config.policies, ChannelPolicies)
