# Test Coverage Report

## Current Coverage Status

### Summary
- **Total Modules**: 34 Python files
- **Modules with Tests**: 1 (3% coverage)
- **Missing Tests**: 33 modules (97% need tests)

---

## 📊 Coverage by Component

### ✅ Tested Components (3%)

| Module | Test File | Coverage | Status |
|--------|-----------|----------|--------|
| `src/classifier/question_classifier.py` | `tests/unit/test_classifier.py` | 3 tests | ✅ Good |

**Tests:**
- ✅ Bug detection
- ✅ How-to detection
- ✅ Error fallback

---

### 🚧 Components Needing Tests (97%)

#### High Priority - Core Business Logic

| Module | Lines | Complexity | Priority | Status |
|--------|-------|------------|----------|--------|
| `src/slack/services/conversation_service.py` | ~200 | High | Critical | ❌ No tests |
| `src/slack/services/message_processor.py` | ~80 | Medium | Critical | ❌ No tests |
| `src/slack/services/action_service.py` | ~70 | Medium | High | ❌ No tests |
| `src/config/channel_config.py` | ~150 | Medium | High | ❌ No tests |
| `src/rag/rag_pipeline.py` | ~60 | Medium | High | ❌ No tests |

#### Medium Priority - Integrations

| Module | Lines | Complexity | Priority | Status |
|--------|-------|------------|----------|--------|
| `src/integrations/jira_client.py` | ~100 | Medium | Medium | ❌ No tests |
| `src/integrations/email_client.py` | ~80 | Low | Medium | ❌ No tests |
| `src/slack/handlers/message.py` | ~120 | High | Medium | ❌ No tests |
| `src/slack/handlers/reaction.py` | ~80 | Medium | Medium | ❌ No tests |
| `src/slack/handlers/action.py` | ~100 | Medium | Medium | ❌ No tests |

#### Lower Priority - Infrastructure

| Module | Lines | Complexity | Priority | Status |
|--------|-------|------------|----------|--------|
| `src/config/settings.py` | ~100 | Low | Low | ❌ No tests |
| `src/models/base.py` | ~80 | Low | Low | ❌ No tests |
| `src/models/conversation.py` | ~80 | Low | Low | ❌ No tests |
| `src/models/action.py` | ~50 | Low | Low | ❌ No tests |
| `src/models/feedback.py` | ~40 | Low | Low | ❌ No tests |
| `src/models/audit.py` | ~30 | Low | Low | ❌ No tests |
| `src/observability/logging.py` | ~80 | Low | Low | ❌ No tests |
| `src/observability/metrics.py` | ~150 | Low | Low | ❌ No tests |

#### Web Dashboard

| Module | Lines | Complexity | Priority | Status |
|--------|-------|------------|----------|--------|
| `src/web/app.py` | ~350 | High | Medium | ❌ No tests |

---

## 📋 Recommended Test Plan

### Phase 1: Critical Business Logic (Week 1)

**Priority 1: Conversation Service**
```python
tests/unit/test_conversation_service.py
- test_get_or_create_conversation_new()
- test_get_or_create_conversation_existing()
- test_save_message()
- test_update_conversation_type()
- test_update_conversation_summary()
- test_mark_first_response()
- test_find_conversation_by_message()
- test_save_feedback()
```

**Priority 2: Message Processor**
```python
tests/unit/test_message_processor.py
- test_process_message_basic()
- test_process_message_with_files()
- test_process_message_error_handling()
```

**Priority 3: Channel Config**
```python
tests/unit/test_channel_config.py
- test_load_config()
- test_get_channel_config()
- test_is_channel_enabled()
- test_list_channels()
- test_reload()
- test_create_default_config()
```

### Phase 2: Handlers & Integrations (Week 2)

**Slack Handlers**
```python
tests/unit/test_message_handler.py
tests/unit/test_reaction_handler.py
tests/unit/test_action_handler.py
```

**External Integrations**
```python
tests/unit/test_jira_client.py
- test_create_issue()
- test_create_issue_failure()
- test_update_issue()
- test_client_not_initialized()

tests/unit/test_email_client.py
- test_send_escalation()
- test_send_escalation_failure()
```

### Phase 3: Web Dashboard (Week 3)

**FastAPI Application**
```python
tests/unit/test_web_app.py
- test_dashboard_endpoint()
- test_logs_endpoint()
- test_health_check()
- test_stats_endpoint()
- test_recent_conversations()
- test_audit_events()
- test_channel_stats()
- test_websocket_logs()
- test_websocket_metrics()

tests/integration/test_web_api.py
- test_api_flow()
- test_websocket_connection()
```

### Phase 4: Models & Infrastructure (Week 4)

**Database Models**
```python
tests/unit/test_models.py
- test_conversation_model()
- test_message_model()
- test_action_run_model()
- test_feedback_model()
- test_audit_event_model()
```

**Configuration**
```python
tests/unit/test_settings.py
- test_settings_from_env()
- test_settings_validation()
- test_settings_defaults()
```

### Phase 5: Integration Tests (Week 5)

```python
tests/integration/test_slack_flow.py
- test_message_to_response_flow()
- test_feedback_flow()
- test_action_approval_flow()

tests/integration/test_database.py
- test_conversation_lifecycle()
- test_query_performance()

tests/integration/test_external_services.py
- test_jira_integration()
- test_email_integration()
```

---

## 🎯 Coverage Goals

### Short Term (1-2 weeks)
- [ ] Achieve 50% line coverage
- [ ] Test all critical paths
- [ ] Test error handling

### Medium Term (1 month)
- [ ] Achieve 70% line coverage
- [ ] Complete unit tests for all services
- [ ] Add integration tests

### Long Term (2-3 months)
- [ ] Achieve 85%+ line coverage
- [ ] Complete E2E tests
- [ ] Performance tests
- [ ] Load tests

---

## 🔧 Testing Tools Setup

### Current Tools
- ✅ pytest
- ✅ pytest-asyncio
- ✅ pytest-cov
- ✅ pytest-mock

### Additional Recommendations
```bash
pip install pytest-xdist      # Parallel test execution
pip install pytest-timeout    # Test timeouts
pip install faker             # Fake data generation
pip install freezegun         # Time mocking
pip install responses         # HTTP mocking
```

---

## 📝 Test Examples

### Example 1: Testing Conversation Service

```python
# tests/unit/test_conversation_service.py
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.slack.services.conversation_service import ConversationService
from src.models.conversation import Conversation, ConversationStatus, QuestionType

@pytest.fixture
async def conversation_service():
    return ConversationService()

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.__aenter__.return_value = session
    session.__aexit__.return_value = None
    return session

@pytest.mark.asyncio
async def test_get_or_create_conversation_new(conversation_service, mock_session):
    """Test creating a new conversation."""
    with patch('src.slack.services.conversation_service.AsyncSessionLocal', return_value=mock_session):
        # Mock database query returning None (no existing conversation)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Test
        conv = await conversation_service.get_or_create_conversation(
            channel_id="C123",
            thread_ts="1234567890.123456",
            user_id="U123"
        )

        # Assertions
        assert mock_session.add.called
        assert mock_session.commit.called

@pytest.mark.asyncio
async def test_save_message(conversation_service, mock_session):
    """Test saving a message."""
    with patch('src.slack.services.conversation_service.AsyncSessionLocal', return_value=mock_session):
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        message = await conversation_service.save_message(
            conversation_id=1,
            ts="1234567890.123456",
            user_id="U123",
            text="Test message"
        )

        assert mock_session.add.called
        assert mock_session.commit.called
```

### Example 2: Testing Channel Config

```python
# tests/unit/test_channel_config.py
import pytest
import yaml
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.config.channel_config import ChannelConfigManager, ChannelConfig

@pytest.fixture
def temp_config_file():
    """Create a temporary config file."""
    config_data = {
        'channels': [
            {
                'channel_id': 'C123',
                'name': 'test-channel',
                'rag_index': 'test-index',
                'enabled': True,
            }
        ]
    }

    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        yield f.name

    Path(f.name).unlink()

def test_load_config(temp_config_file):
    """Test loading configuration from file."""
    manager = ChannelConfigManager(temp_config_file)

    assert len(manager.list_channels()) == 1
    config = manager.get_channel_config('C123')
    assert config is not None
    assert config.name == 'test-channel'

def test_is_channel_enabled(temp_config_file):
    """Test checking if channel is enabled."""
    manager = ChannelConfigManager(temp_config_file)

    assert manager.is_channel_enabled('C123') is True
    assert manager.is_channel_enabled('C999') is False
```

### Example 3: Testing Web API

```python
# tests/unit/test_web_app.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.web.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

@pytest.mark.asyncio
async def test_stats_endpoint(client):
    """Test stats endpoint."""
    with patch('src.web.app.AsyncSessionLocal') as mock_session:
        # Mock database responses
        mock_session.return_value.__aenter__.return_value.execute = AsyncMock()

        response = client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "helpful_rate" in data
```

### Example 4: Testing Jira Integration

```python
# tests/unit/test_jira_client.py
import pytest
from unittest.mock import MagicMock, patch

from src.integrations.jira_client import JiraClient
from src.config.settings import Settings

@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.jira_url = "https://test.atlassian.net"
    settings.jira_username = "test@example.com"
    settings.jira_api_token = MagicMock()
    settings.jira_api_token.get_secret_value.return_value = "test-token"
    settings.jira_project_key = "TEST"
    settings.jira_issue_type = "Task"
    return settings

@pytest.mark.asyncio
async def test_create_issue_success(mock_settings):
    """Test successful issue creation."""
    with patch('src.integrations.jira_client.JIRA') as mock_jira:
        # Mock Jira client
        mock_issue = MagicMock()
        mock_issue.key = "TEST-123"
        mock_jira.return_value.create_issue.return_value = mock_issue

        client = JiraClient(mock_settings)
        issue_key = await client.create_issue(
            summary="Test Issue",
            description="Test Description"
        )

        assert issue_key == "TEST-123"
        mock_jira.return_value.create_issue.assert_called_once()

@pytest.mark.asyncio
async def test_create_issue_failure(mock_settings):
    """Test issue creation failure."""
    with patch('src.integrations.jira_client.JIRA') as mock_jira:
        mock_jira.return_value.create_issue.side_effect = Exception("API Error")

        client = JiraClient(mock_settings)
        issue_key = await client.create_issue(
            summary="Test Issue",
            description="Test Description"
        )

        assert issue_key is None
```

---

## 🚀 Quick Start: Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_classifier.py

# Run with verbose output
pytest -v

# Run in parallel (faster)
pytest -n auto

# Run only failed tests
pytest --lf

# Run tests matching pattern
pytest -k "test_classifier"
```

## 📈 Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Generate terminal report
pytest --cov=src --cov-report=term-missing

# Generate XML report (for CI)
pytest --cov=src --cov-report=xml
```

---

## 🎯 Next Steps

1. **Immediate (This Week)**
   - [ ] Create `tests/unit/test_conversation_service.py`
   - [ ] Create `tests/unit/test_channel_config.py`
   - [ ] Create `tests/unit/test_message_processor.py`
   - [ ] Aim for 30% coverage

2. **Short Term (Next 2 Weeks)**
   - [ ] Add tests for all handlers
   - [ ] Add tests for integrations
   - [ ] Add tests for web API
   - [ ] Aim for 50% coverage

3. **Medium Term (Next Month)**
   - [ ] Add integration tests
   - [ ] Add E2E tests
   - [ ] Add performance tests
   - [ ] Aim for 70% coverage

4. **Long Term (Next Quarter)**
   - [ ] Achieve 85%+ coverage
   - [ ] Add load tests
   - [ ] Add security tests
   - [ ] Set up CI/CD with coverage gates

---

## 📚 Resources

- **pytest Documentation**: https://docs.pytest.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **Testing FastAPI**: https://fastapi.tiangolo.com/tutorial/testing/
- **Testing SQLAlchemy**: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites

---

**Note**: This is a living document. Update as tests are added and coverage improves.
