"""Tests for web dashboard application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.web.app import app, manager


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


def test_dashboard_page(client):
    """Test main dashboard page."""
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Slack RAG Assistant" in response.content


def test_logs_page(client):
    """Test logs viewer page."""
    response = client.get("/logs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Logs Viewer" in response.content


@pytest.mark.asyncio
async def test_stats_endpoint():
    """Test stats endpoint with mocked database."""
    with patch("src.web.app.AsyncSessionLocal") as mock_session_class:
        # Create mock session
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_class.return_value = mock_session

        # Mock database queries
        mock_result = AsyncMock()
        mock_result.scalar_one.return_value = 100
        mock_result.all.return_value = [("bug", 50), ("how_to", 30)]
        mock_session.execute.return_value = mock_result

        # Import and call function
        from src.web.app import get_stats

        stats = await get_stats()

        assert "total_conversations" in stats
        assert "helpful_rate" in stats
        assert "timestamp" in stats


@pytest.mark.asyncio
async def test_recent_conversations():
    """Test recent conversations endpoint."""
    with patch("src.web.app.AsyncSessionLocal") as mock_session_class:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_class.return_value = mock_session

        # Mock conversation
        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.channel_id = "C123"
        mock_conversation.thread_ts = "1234567890.123456"
        mock_conversation.user_id = "U123"
        mock_conversation.question_type = None
        mock_conversation.status = "active"
        mock_conversation.created_at = datetime.utcnow()
        mock_conversation.jira_key = None

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [mock_conversation]
        mock_session.execute.return_value = mock_result

        from src.web.app import get_recent_conversations

        data = await get_recent_conversations(limit=10)

        assert "conversations" in data
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["id"] == 1


@pytest.mark.asyncio
async def test_audit_events():
    """Test audit events endpoint."""
    with patch("src.web.app.AsyncSessionLocal") as mock_session_class:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_class.return_value = mock_session

        # Mock audit event
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.event_type = "message_received"
        mock_event.actor_id = "U123"
        mock_event.channel_id = "C123"
        mock_event.thread_ts = "1234567890.123456"
        mock_event.result = "success"
        mock_event.created_at = datetime.utcnow()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [mock_event]
        mock_session.execute.return_value = mock_result

        from src.web.app import get_audit_events

        data = await get_audit_events(limit=50)

        assert "events" in data
        assert len(data["events"]) == 1
        assert data["events"][0]["event_type"] == "message_received"


@pytest.mark.asyncio
async def test_channel_stats():
    """Test channel statistics endpoint."""
    with patch("src.web.app.AsyncSessionLocal") as mock_session_class:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_class.return_value = mock_session

        # Mock channel stats
        mock_result = AsyncMock()
        mock_result.all.return_value = [("C123", 100, 10)]
        mock_session.execute.return_value = mock_result

        from src.web.app import get_channel_stats

        data = await get_channel_stats()

        assert "channel_stats" in data
        assert len(data["channel_stats"]) == 1
        assert data["channel_stats"][0]["channel_id"] == "C123"


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")

    assert response.status_code == 200
    # Check for Prometheus format indicators
    assert b"slack_rag" in response.content or b"# HELP" in response.content


@pytest.mark.asyncio
async def test_websocket_logs():
    """Test WebSocket logs endpoint connection."""
    client = TestClient(app)

    with client.websocket_connect("/ws/logs") as websocket:
        # Send ping
        websocket.send_text("ping")

        # Receive pong
        data = websocket.receive_json()
        assert data["type"] == "pong"


def test_connection_manager_connect():
    """Test connection manager connect."""
    mock_websocket = AsyncMock()

    # Test connection
    assert len(manager.active_connections) == 0


def test_connection_manager_disconnect():
    """Test connection manager disconnect."""
    mock_websocket = AsyncMock()

    # Add connection
    if mock_websocket not in manager.active_connections:
        manager.active_connections.append(mock_websocket)

    # Disconnect
    manager.disconnect(mock_websocket)

    assert mock_websocket not in manager.active_connections


@pytest.mark.asyncio
async def test_broadcast():
    """Test broadcasting message to connections."""
    # Add mock connection
    mock_websocket = AsyncMock()
    manager.active_connections.append(mock_websocket)

    # Broadcast
    await manager.broadcast({"type": "test", "data": "hello"})

    # Verify message was sent
    mock_websocket.send_json.assert_called_once()

    # Clean up
    manager.disconnect(mock_websocket)
