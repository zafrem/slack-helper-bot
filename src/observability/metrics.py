"""Prometheus metrics configuration."""

from prometheus_client import Counter, Gauge, Histogram, start_http_server

from src.config.settings import Settings


# Message metrics
messages_received_total = Counter(
    "slack_rag_messages_received_total",
    "Total messages received",
    ["channel_id", "message_type"],
)

messages_processed_total = Counter(
    "slack_rag_messages_processed_total",
    "Total messages processed",
    ["channel_id", "status"],
)

# Response metrics
response_time_seconds = Histogram(
    "slack_rag_response_time_seconds",
    "Response time in seconds",
    ["channel_id", "response_type"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

first_response_time_seconds = Histogram(
    "slack_rag_first_response_time_seconds",
    "First response time in seconds",
    ["channel_id"],
    buckets=[1.0, 3.0, 5.0, 10.0, 15.0, 30.0, 60.0],
)

# RAG metrics
rag_queries_total = Counter(
    "slack_rag_queries_total",
    "Total RAG queries",
    ["channel_id", "index"],
)

rag_query_duration_seconds = Histogram(
    "slack_rag_query_duration_seconds",
    "RAG query duration in seconds",
    ["channel_id", "index"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

rag_documents_retrieved = Histogram(
    "slack_rag_documents_retrieved",
    "Number of documents retrieved",
    ["channel_id", "index"],
    buckets=[1, 3, 5, 10, 20],
)

# Classification metrics
classification_total = Counter(
    "slack_rag_classification_total",
    "Total classifications",
    ["channel_id", "question_type"],
)

classification_duration_seconds = Histogram(
    "slack_rag_classification_duration_seconds",
    "Classification duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
)

# Action metrics
actions_requested_total = Counter(
    "slack_rag_actions_requested_total",
    "Total actions requested",
    ["channel_id", "action_name"],
)

actions_approved_total = Counter(
    "slack_rag_actions_approved_total",
    "Total actions approved",
    ["channel_id", "action_name"],
)

actions_executed_total = Counter(
    "slack_rag_actions_executed_total",
    "Total actions executed",
    ["channel_id", "action_name", "status"],
)

action_duration_seconds = Histogram(
    "slack_rag_action_duration_seconds",
    "Action execution duration in seconds",
    ["channel_id", "action_name"],
    buckets=[0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
)

# Feedback metrics
feedback_total = Counter(
    "slack_rag_feedback_total",
    "Total feedback received",
    ["channel_id", "rating"],
)

helpful_rate = Gauge(
    "slack_rag_helpful_rate",
    "Percentage of helpful responses",
    ["channel_id"],
)

# Jira metrics
jira_issues_created_total = Counter(
    "slack_rag_jira_issues_created_total",
    "Total Jira issues created",
    ["channel_id", "issue_type"],
)

jira_issues_updated_total = Counter(
    "slack_rag_jira_issues_updated_total",
    "Total Jira issues updated",
    ["channel_id"],
)

# Escalation metrics
escalations_total = Counter(
    "slack_rag_escalations_total",
    "Total escalations",
    ["channel_id", "reason"],
)

# Error metrics
errors_total = Counter(
    "slack_rag_errors_total",
    "Total errors",
    ["component", "error_type"],
)

# Active conversations
active_conversations = Gauge(
    "slack_rag_active_conversations",
    "Number of active conversations",
    ["channel_id"],
)


def setup_metrics(settings: Settings) -> None:
    """Start Prometheus metrics server.

    Args:
        settings: Application settings
    """
    start_http_server(settings.metrics_port)
