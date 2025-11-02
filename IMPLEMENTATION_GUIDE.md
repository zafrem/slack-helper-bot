# Slack RAG Assistant - Implementation Guide

This guide will help you complete and deploy the Slack RAG Assistant.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Slack Workspace                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Slack Bot (Socket Mode)                   │
│  ┌──────────────┬──────────────┬─────────────────────────┐ │
│  │   Messages   │  Reactions   │      Actions            │ │
│  └──────┬───────┴──────┬───────┴──────────┬──────────────┘ │
└─────────┼──────────────┼───────────────────┼────────────────┘
          │              │                   │
          ▼              ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                     Message Processor                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Extract Images (OCR) → 2. Classify Question      │  │
│  │  3. Generate Summary     → 4. User Confirmation      │  │
│  │  5. RAG Answer / Action  → 6. Post Response          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────┬──────────────┬─────────────────┬─────────────────┬───┘
      │              │                 │                 │
      ▼              ▼                 ▼                 ▼
┌──────────┐  ┌──────────┐  ┌─────────────┐  ┌──────────────┐
│   RAG    │  │Classifier│  │   Actions   │  │ Integrations │
│ Pipeline │  │ + LLM    │  │  Executor   │  │ Jira + Email │
└──────────┘  └──────────┘  └─────────────┘  └──────────────┘
      │              │                 │                 │
      ▼              ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                       PostgreSQL Database                    │
│  Conversations | Messages | Actions | Feedback | Audit      │
└─────────────────────────────────────────────────────────────┘
```

## Current Implementation Status

### ✅ Completed Components

1. **Project Structure**: Complete with all directories and packages
2. **Configuration System**: Settings, channel configs, templates
3. **Database Models**: Conversations, messages, actions, feedback, audit
4. **Slack Integration**: Event handlers for messages, reactions, actions
5. **Observability**: Structured logging, Prometheus metrics
6. **Integrations**: Jira and Email clients (basic implementation)
7. **Classification**: Question type classifier
8. **Docker Setup**: Dockerfile and docker-compose.yml

### 🚧 Components Needing Completion

The following components have placeholder implementations and need to be completed:

#### 1. Message Processor (`src/slack/services/message_processor.py`)

**TODO: Line 43-51**
```python
# Implement full message processing pipeline:
# 1. Extract text from images (if any)
# 2. Classify the question type
# 3. Generate summary using template
# 4. Request user confirmation
# 5. If confirmed, generate RAG answer or execute action
# 6. Post response in thread
```

**Implementation Steps:**
- Add image processing service using OCR (pytesseract)
- Integrate question classifier
- Add template rendering service (Jinja2)
- Create confirmation UI with Slack blocks
- Connect to RAG pipeline for answers
- Link to action executor for ops requests

#### 2. RAG Pipeline (`src/rag/rag_pipeline.py`)

**TODO: Lines 31-44**
```python
# Implement RAG pipeline:
# 1. Generate embeddings for the question
# 2. Search vector store for similar documents
# 3. Filter by similarity threshold
# 4. Prepare context with retrieved documents
# 5. Generate answer using LLM with context
# 6. Extract citations from retrieved docs
```

**Implementation Steps:**
- Choose and implement vector store client (Pinecone/ChromaDB/FAISS)
- Add embeddings generation (OpenAI/Anthropic)
- Implement semantic search
- Create context preparation with retrieved docs
- Add LLM answer generation with citations
- Implement confidence scoring

#### 3. Action Service (`src/slack/services/action_service.py`)

**TODO: Lines 34-40, 56-67**

**Implementation Steps:**
- Add authorization checks (verify approver permissions)
- Create action registry/whitelist system
- Implement action execution framework
- Add progress streaming to Slack thread
- Implement rollback mechanisms
- Add audit logging for all actions

#### 4. Template Service (New File Needed)

Create `src/templates/template_service.py`:

```python
class TemplateService:
    """Service for rendering question type templates."""

    def render_summary(
        self,
        question_type: QuestionType,
        context: dict,
    ) -> str:
        """Render summary template based on question type."""
        # Load appropriate Jinja2 template
        # Extract relevant information from message
        # Render template with context
        # Return formatted summary
```

#### 5. Image Processing Service (New File Needed)

Create `src/utils/image_processor.py`:

```python
class ImageProcessor:
    """Service for processing images and extracting text."""

    async def process_image(
        self,
        image_url: str,
        slack_token: str,
    ) -> str:
        """Download image from Slack and extract text via OCR."""
        # Download image using Slack API
        # Run OCR using pytesseract
        # Apply PII redaction if enabled
        # Return extracted text
```

#### 6. Action Executor Framework (New File Needed)

Create `src/actions/executor.py`:

```python
class ActionExecutor:
    """Framework for executing approved actions."""

    def register_action(self, name: str, handler: Callable):
        """Register an action handler."""

    async def execute(
        self,
        action_name: str,
        parameters: dict,
        progress_callback: Callable,
    ) -> ActionResult:
        """Execute an action with progress updates."""
```

#### 7. PII Redaction Service (New File Needed)

Create `src/security/pii_redactor.py`:

```python
class PIIRedactor:
    """Service for detecting and redacting PII."""

    def __init__(self):
        # Initialize Presidio analyzer
        pass

    def redact(self, text: str) -> str:
        """Detect and redact PII from text."""
        # Use Presidio to detect PII
        # Redact sensitive information
        # Return cleaned text
```

## Quick Start Guide

### 1. Initial Setup

```bash
# Clone the repository
cd slack-helper-bot

# Run setup script
./scripts/setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Environment

Edit `.env` file with your credentials:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret

# LLM Provider (choose one)
OPENAI_API_KEY=sk-your-key
# OR
ANTHROPIC_API_KEY=sk-ant-your-key

# Vector Database (choose one)
PINECONE_API_KEY=your-key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=slack-rag-assistant

# Jira (optional)
JIRA_URL=https://your-domain.atlassian.net
JIRA_API_TOKEN=your-token

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Configure Channels

Edit `config/channels.yaml`:

```yaml
channels:
  - channel_id: C12345ABCDE  # Get from Slack
    name: engineering-support
    rag_index: kb-engineering
    retrieval_params:
      top_k: 5
      similarity_threshold: 0.7
    approvers:
      - U111111  # User IDs from Slack
      - U222222
    sla_minutes: 120
    first_response_minutes: 15
    policies:
      pii_redaction: true
      action_whitelist:
        - restart_service
        - flush_cache
    enabled: true
```

### 4. Set Up Slack App

1. Go to https://api.slack.com/apps
2. Create a new app "From manifest"
3. Use this manifest:

```yaml
display_information:
  name: RAG Assistant
  description: AI-powered support assistant
  background_color: "#4A154B"
features:
  bot_user:
    display_name: RAG Assistant
    always_online: true
oauth_config:
  scopes:
    bot:
      - channels:history
      - channels:read
      - chat:write
      - files:read
      - reactions:read
      - users:read
      - app_mentions:read
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.channels
      - reaction_added
  interactivity:
    is_enabled: true
  socket_mode_enabled: true
```

4. Install app to workspace
5. Copy tokens to `.env`

### 5. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Or with Docker
docker-compose up -d postgres
```

### 6. Run the Bot

```bash
# Development
python -m src.main

# Or with Docker
docker-compose up -d
```

### 7. Monitor

```bash
# View logs
docker-compose logs -f app

# Check metrics
curl http://localhost:9090/metrics
```

## Development Workflow

### Adding a New Action

1. Define action handler in `src/actions/handlers/`:

```python
async def restart_service(params: dict) -> ActionResult:
    """Restart a service."""
    service_name = params["service_name"]
    # Implementation
    return ActionResult(success=True, output="Service restarted")
```

2. Register in action executor
3. Add to channel's `action_whitelist`
4. Create action template in `config/templates/`

### Adding a New Knowledge Base

1. Prepare documents
2. Generate embeddings
3. Upload to vector store with index name
4. Configure channel to use that index

### Customizing Templates

Edit templates in `config/templates/`:
- `bug.jinja2`
- `how_to.jinja2`
- `feature_request.jinja2`
- `action.jinja2`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_classifier.py

# Run integration tests
pytest tests/integration/
```

## Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set strong `ENCRYPTION_KEY` and `SECRET_KEY`
- [ ] Configure proper `DATABASE_URL`
- [ ] Enable TLS for all external connections
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Set up backup strategy for database
- [ ] Review and test rollback procedures
- [ ] Configure rate limiting
- [ ] Review PII redaction rules
- [ ] Set up secret rotation schedule

### Docker Deployment

```bash
# Build image
docker build -t slack-rag-assistant:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Kubernetes Deployment

Create Kubernetes manifests in `k8s/`:
- `deployment.yaml`
- `service.yaml`
- `configmap.yaml`
- `secret.yaml`

## Troubleshooting

### Bot Not Responding

1. Check bot is running: `docker-compose ps`
2. Check logs: `docker-compose logs -f app`
3. Verify Slack tokens in `.env`
4. Check channel is enabled in `config/channels.yaml`
5. Verify bot has permissions in Slack

### Database Errors

1. Check database connection: `DATABASE_URL` in `.env`
2. Run migrations: `alembic upgrade head`
3. Check database logs: `docker-compose logs -f postgres`

### RAG Not Working

1. Verify vector DB credentials
2. Check index exists and has data
3. Verify embeddings model is accessible
4. Check retrieval parameters in channel config

### Actions Failing

1. Check action is whitelisted
2. Verify user is in approvers list
3. Check action handler implementation
4. Review action execution logs

## Performance Tuning

### Database

- Add indexes for frequently queried fields
- Use connection pooling
- Configure appropriate pool size
- Enable query logging in development

### RAG

- Adjust `top_k` based on quality/speed tradeoff
- Fine-tune `similarity_threshold`
- Cache frequently asked questions
- Batch embeddings generation

### Rate Limiting

- Configure per-user and per-channel limits
- Implement exponential backoff for retries
- Add circuit breakers for external services

## Security Best Practices

1. **Secrets Management**: Use environment variables or secret managers
2. **PII Redaction**: Enable and test PII redaction
3. **Access Control**: Regularly review approver lists
4. **Audit Logging**: Enable and monitor all audit events
5. **Encryption**: Use TLS for all connections
6. **Input Validation**: Validate all user inputs
7. **Action Approval**: Never bypass approval gates
8. **Regular Updates**: Keep dependencies updated

## Next Steps

1. Complete TODO items in core services
2. Add comprehensive test coverage
3. Set up CI/CD pipeline
4. Create runbooks for common scenarios
5. Document all custom actions
6. Set up monitoring dashboards
7. Conduct security review
8. Perform load testing
9. Create user documentation
10. Plan knowledge base ingestion strategy

## Support & Resources

- **Documentation**: This guide and inline code comments
- **Issues**: Report bugs and feature requests on GitHub
- **Community**: Join our Slack channel (if available)
- **Contributing**: See CONTRIBUTING.md (if created)

## License

See [LICENSE](LICENSE) file for details.
