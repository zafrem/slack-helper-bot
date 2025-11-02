"""FastAPI web application for monitoring and logs."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import structlog
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import REGISTRY, generate_latest
from sqlalchemy import func, select

from src.config.settings import get_settings
from src.models.audit import AuditEvent
from src.models.base import AsyncSessionLocal
from src.models.conversation import Conversation, ConversationStatus, QuestionType
from src.models.feedback import Feedback, FeedbackRating
from src.observability.metrics import (
    errors_total,
    feedback_total,
    messages_processed_total,
    messages_received_total,
)

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Slack RAG Assistant - Monitoring Dashboard",
    description="Real-time monitoring, metrics, and logs",
    version="0.1.0",
)

# Templates
templates = Jinja2Templates(directory="src/web/templates")
settings = get_settings()


# WebSocket connections for real-time updates
class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected", total_connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Disconnect a WebSocket client."""
        self.active_connections.remove(websocket)
        logger.info(
            "WebSocket client disconnected", total_connections=len(self.active_connections)
        )

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning("Failed to send message to client", error=str(e))


manager = ConnectionManager()


# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Main dashboard page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "environment": settings.environment,
            "app_version": settings.app_version,
        },
    )


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request) -> HTMLResponse:
    """Logs viewer page."""
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "environment": settings.environment,
        },
    )


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/stats")
async def get_stats() -> dict[str, Any]:
    """Get overall statistics."""
    async with AsyncSessionLocal() as session:
        # Total conversations
        total_conversations = await session.execute(select(func.count(Conversation.id)))
        total_count = total_conversations.scalar_one()

        # Active conversations
        active_conversations = await session.execute(
            select(func.count(Conversation.id)).where(
                Conversation.status == ConversationStatus.ACTIVE
            )
        )
        active_count = active_conversations.scalar_one()

        # Total feedback
        total_feedback = await session.execute(select(func.count(Feedback.id)))
        feedback_count = total_feedback.scalar_one()

        # Helpful feedback
        helpful_feedback = await session.execute(
            select(func.count(Feedback.id)).where(Feedback.rating == FeedbackRating.HELPFUL)
        )
        helpful_count = helpful_feedback.scalar_one()

        # Calculate helpful rate
        helpful_rate = (helpful_count / feedback_count * 100) if feedback_count > 0 else 0

        # Conversations by type
        type_distribution = await session.execute(
            select(Conversation.question_type, func.count(Conversation.id))
            .where(Conversation.question_type.isnot(None))
            .group_by(Conversation.question_type)
        )
        type_counts = {
            row[0].value if row[0] else "unknown": row[1] for row in type_distribution.all()
        }

        return {
            "total_conversations": total_count,
            "active_conversations": active_count,
            "total_feedback": feedback_count,
            "helpful_count": helpful_count,
            "helpful_rate": round(helpful_rate, 2),
            "type_distribution": type_counts,
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.get("/api/recent_conversations")
async def get_recent_conversations(limit: int = 20) -> dict[str, Any]:
    """Get recent conversations."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        conversations = result.scalars().all()

        return {
            "conversations": [
                {
                    "id": conv.id,
                    "channel_id": conv.channel_id,
                    "thread_ts": conv.thread_ts,
                    "user_id": conv.user_id,
                    "question_type": conv.question_type.value if conv.question_type else None,
                    "status": conv.status.value,
                    "created_at": conv.created_at.isoformat(),
                    "jira_key": conv.jira_key,
                }
                for conv in conversations
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.get("/api/audit_events")
async def get_audit_events(limit: int = 50, event_type: str | None = None) -> dict[str, Any]:
    """Get audit events."""
    async with AsyncSessionLocal() as session:
        query = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)

        if event_type:
            query = query.where(AuditEvent.event_type == event_type)

        result = await session.execute(query)
        events = result.scalars().all()

        return {
            "events": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "actor_id": event.actor_id,
                    "channel_id": event.channel_id,
                    "thread_ts": event.thread_ts,
                    "result": event.result,
                    "created_at": event.created_at.isoformat(),
                }
                for event in events
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.get("/api/metrics_summary")
async def get_metrics_summary() -> dict[str, Any]:
    """Get summary of Prometheus metrics."""
    # Collect metrics from Prometheus registry
    metrics_data = {}

    # Get message metrics
    for metric in REGISTRY.collect():
        if metric.name.startswith("slack_rag_"):
            for sample in metric.samples:
                if sample.name not in metrics_data:
                    metrics_data[sample.name] = []
                metrics_data[sample.name].append(
                    {"labels": sample.labels, "value": sample.value}
                )

    return {
        "metrics": metrics_data,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/metrics")
async def metrics() -> Any:
    """Prometheus metrics endpoint."""
    return generate_latest(REGISTRY)


@app.get("/api/channel_stats")
async def get_channel_stats() -> dict[str, Any]:
    """Get statistics by channel."""
    async with AsyncSessionLocal() as session:
        # Conversations by channel
        channel_stats = await session.execute(
            select(
                Conversation.channel_id,
                func.count(Conversation.id).label("total"),
                func.count(
                    func.nullif(Conversation.status != ConversationStatus.ACTIVE, False)
                ).label("active"),
            ).group_by(Conversation.channel_id)
        )

        stats = []
        for row in channel_stats.all():
            stats.append(
                {
                    "channel_id": row[0],
                    "total_conversations": row[1],
                    "active_conversations": row[2],
                }
            )

        return {
            "channel_stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time log streaming."""
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and wait for client messages
            data = await websocket.receive_text()

            # Echo back (or handle client commands)
            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.exception("WebSocket error", error=str(e))
        manager.disconnect(websocket)


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time metrics updates."""
    await websocket.accept()

    try:
        while True:
            # Send metrics every 5 seconds
            stats = await get_stats()
            await websocket.send_json(
                {
                    "type": "stats_update",
                    "data": stats,
                }
            )
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("Metrics WebSocket error", error=str(e))


async def broadcast_log(log_entry: dict[str, Any]) -> None:
    """Broadcast log entry to all connected WebSocket clients.

    Args:
        log_entry: Log entry dictionary
    """
    await manager.broadcast(
        {
            "type": "log",
            "data": log_entry,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


def create_app() -> FastAPI:
    """Create and configure the FastAPI app.

    Returns:
        Configured FastAPI application
    """
    return app
