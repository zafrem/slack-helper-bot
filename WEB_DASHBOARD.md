# Web Monitoring Dashboard

The Slack RAG Assistant includes a beautiful, real-time web dashboard for monitoring your bot's performance, viewing logs, and analyzing metrics.

## Features

### 📊 Dashboard (`http://localhost:8080`)

**Real-Time Statistics:**
- Total conversations
- Active conversations
- Helpful rate (user feedback)
- Total feedback received

**Analytics:**
- Question type distribution (bug, how-to, feature request, etc.)
- Recent conversations with status
- Channel statistics
- Visual progress bars

**Auto-Refresh:**
- Updates every 30 seconds
- WebSocket-based real-time updates
- Manual refresh button

### 📋 Logs Viewer (`http://localhost:8080/logs`)

**Real-Time Log Streaming:**
- Live WebSocket connection for instant log updates
- Color-coded log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Searchable log entries
- Filterable by log level

**Features:**
- Pause/Resume log streaming
- Clear logs
- Export logs as JSON
- Auto-scroll to latest entries
- Connection status indicator
- Dark theme optimized for readability

### 📈 Raw Metrics (`http://localhost:8080/metrics`)

**Prometheus Format:**
- Raw metrics in Prometheus exposition format
- Compatible with Grafana, Prometheus, and other tools
- All application metrics exposed

## Screenshots

### Dashboard
```
┌─────────────────────────────────────────────────────────┐
│  🤖 Slack RAG Assistant                      [prod]     │
│  Real-time Monitoring Dashboard • Version 0.1.0         │
└─────────────────────────────────────────────────────────┘

┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────┐
│ Total Conv.  │ │ Active Conv. │ │ Helpful Rate │ │...  │
│    1,234     │ │      42      │ │   87.5%      │ │     │
└──────────────┘ └──────────────┘ └──────────────┘ └─────┘

📊 Question Type Distribution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type          Count    Percentage
bug             456    ████████████████░░░░ 37%
how_to          321    ████████████░░░░░░░░ 26%
...

💬 Recent Conversations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#ID  Channel    Type      Status    Created    Jira
123  C12345...  bug       active    10:30 AM   SUP-456
...
```

### Logs Viewer
```
┌─────────────────────────────────────────────────────────┐
│  📋 Logs Viewer                                          │
└─────────────────────────────────────────────────────────┘

Filters: [Level: Info ▼] [Search: ___________] [Clear] [Pause]
                                          Connected ● 234 entries

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│ 10:30:45 [INFO   ] Message received
│ 10:30:46 [INFO   ] Classifying question type
│ 10:30:47 [INFO   ] RAG query completed
│ 10:30:48 [ERROR  ] Failed to connect to vector DB
│           Context: {"error": "timeout", "retry": 1}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## API Endpoints

### Public Endpoints

#### `GET /`
Main dashboard page (HTML)

#### `GET /logs`
Logs viewer page (HTML)

#### `GET /api/health`
Health check endpoint
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "0.1.0",
  "timestamp": "2025-10-14T12:00:00Z"
}
```

#### `GET /api/stats`
Overall statistics
```json
{
  "total_conversations": 1234,
  "active_conversations": 42,
  "total_feedback": 567,
  "helpful_count": 496,
  "helpful_rate": 87.48,
  "type_distribution": {
    "bug": 456,
    "how_to": 321,
    "feature_request": 234,
    "ops_action": 123,
    "other": 100
  },
  "timestamp": "2025-10-14T12:00:00Z"
}
```

#### `GET /api/recent_conversations?limit=20`
Recent conversations
```json
{
  "conversations": [
    {
      "id": 123,
      "channel_id": "C12345",
      "thread_ts": "1697123456.000100",
      "user_id": "U12345",
      "question_type": "bug",
      "status": "active",
      "created_at": "2025-10-14T10:30:00Z",
      "jira_key": "SUP-456"
    }
  ],
  "timestamp": "2025-10-14T12:00:00Z"
}
```

#### `GET /api/audit_events?limit=50&event_type=action_executed`
Audit events
```json
{
  "events": [
    {
      "id": 789,
      "event_type": "action_executed",
      "actor_id": "U12345",
      "channel_id": "C12345",
      "thread_ts": "1697123456.000100",
      "result": "success",
      "created_at": "2025-10-14T11:00:00Z"
    }
  ],
  "timestamp": "2025-10-14T12:00:00Z"
}
```

#### `GET /api/channel_stats`
Statistics by channel
```json
{
  "channel_stats": [
    {
      "channel_id": "C12345",
      "total_conversations": 567,
      "active_conversations": 23
    }
  ],
  "timestamp": "2025-10-14T12:00:00Z"
}
```

#### `GET /api/metrics_summary`
Prometheus metrics summary
```json
{
  "metrics": {
    "slack_rag_messages_received_total": [
      {"labels": {"channel_id": "C12345"}, "value": 1234}
    ]
  },
  "timestamp": "2025-10-14T12:00:00Z"
}
```

#### `GET /metrics`
Prometheus metrics (text format)
```
# HELP slack_rag_messages_received_total Total messages received
# TYPE slack_rag_messages_received_total counter
slack_rag_messages_received_total{channel_id="C12345",message_type="user_message"} 1234.0
...
```

### WebSocket Endpoints

#### `WS /ws/logs`
Real-time log streaming

**Client → Server:**
```json
"ping"  // Keep-alive
```

**Server → Client:**
```json
{
  "type": "log",
  "data": {
    "level": "INFO",
    "message": "Message processed",
    "context": {"conversation_id": 123}
  },
  "timestamp": "2025-10-14T12:00:00Z"
}
```

#### `WS /ws/metrics`
Real-time metrics updates (every 5 seconds)

**Server → Client:**
```json
{
  "type": "stats_update",
  "data": {
    "total_conversations": 1234,
    "active_conversations": 42,
    "helpful_rate": 87.48
  }
}
```

## Usage

### Starting the Dashboard

The web dashboard starts automatically when you run the bot:

```bash
# Standard start
python -m src.main

# Docker
docker-compose up -d
```

The dashboard will be available at:
- **Main Dashboard**: http://localhost:8080
- **Logs Viewer**: http://localhost:8080/logs
- **Raw Metrics**: http://localhost:8080/metrics
- **Health Check**: http://localhost:8080/api/health

### Accessing Remotely

For production deployments, configure a reverse proxy:

**Nginx Example:**
```nginx
server {
    listen 80;
    server_name bot-dashboard.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Add Authentication** (recommended for production):
```nginx
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8080;
    ...
}
```

### Embedding in Grafana

You can embed the dashboard metrics in Grafana:

1. Add Prometheus data source pointing to `http://localhost:9090/metrics`
2. Create dashboard with PromQL queries:
   ```promql
   rate(slack_rag_messages_received_total[5m])
   slack_rag_helpful_rate
   histogram_quantile(0.95, slack_rag_response_time_seconds)
   ```

### Monitoring from CLI

```bash
# Check health
curl http://localhost:8080/api/health

# Get stats
curl http://localhost:8080/api/stats | jq

# Get recent conversations
curl http://localhost:8080/api/recent_conversations?limit=10 | jq

# Stream logs with websocat
websocat ws://localhost:8080/ws/logs
```

## Customization

### Changing Dashboard Port

Edit `src/main.py`:
```python
config = uvicorn.Config(
    "src.web.app:app",
    host="0.0.0.0",
    port=8080,  # Change this
    log_level="info",
)
```

Or set via environment variable (future enhancement).

### Styling

The dashboard uses inline CSS for easy customization. Edit:
- `src/web/templates/dashboard.html` - Main dashboard styles
- `src/web/templates/logs.html` - Logs viewer styles

### Adding Custom Metrics

Add new metrics in `src/observability/metrics.py`:
```python
custom_metric = Counter(
    "slack_rag_custom_metric",
    "Description",
    ["label1", "label2"],
)
```

Then expose via API in `src/web/app.py`:
```python
@app.get("/api/custom_metrics")
async def get_custom_metrics():
    # Your logic here
    return {"data": ...}
```

## Security Considerations

### Production Deployment

1. **Add Authentication**
   - Use HTTP Basic Auth
   - Or integrate with OAuth/SSO
   - Or use API keys

2. **Enable HTTPS**
   - Use reverse proxy with TLS
   - Let's Encrypt certificates

3. **Rate Limiting**
   - Limit API requests per IP
   - Use nginx limit_req module

4. **Network Security**
   - Bind to localhost if using reverse proxy
   - Use firewall rules
   - VPN for remote access

5. **Content Security Policy**
   ```python
   @app.middleware("http")
   async def add_security_headers(request, call_next):
       response = await call_next(request)
       response.headers["X-Frame-Options"] = "DENY"
       response.headers["X-Content-Type-Options"] = "nosniff"
       return response
   ```

### Sensitive Data

The dashboard may display:
- Channel IDs
- User IDs
- Thread timestamps
- Message counts

**Does NOT display:**
- Actual message content (unless in logs)
- API keys or secrets
- Personal user information

Configure PII redaction in `.env`:
```bash
ENABLE_PII_REDACTION=true
```

## Performance

### Resource Usage

- **Memory**: ~50-100MB (dashboard + bot)
- **CPU**: Minimal (async I/O)
- **Network**: WebSocket connections = ~1KB/s per client

### Optimization

- Dashboard auto-refreshes every 30s (configurable)
- WebSocket connections limited to 100 concurrent (default)
- Logs buffer limited to 1000 entries per client
- Database queries cached for 5s

### Scaling

For high-traffic deployments:
1. Use separate server for dashboard
2. Add Redis for caching metrics
3. Use load balancer for multiple bot instances
4. Configure read replicas for database

## Troubleshooting

### Dashboard Not Loading

1. Check bot is running: `ps aux | grep python`
2. Check port is accessible: `curl http://localhost:8080/api/health`
3. Check logs: `docker-compose logs -f app`
4. Verify firewall rules

### WebSocket Connection Failed

1. Check WebSocket support in proxy
2. Verify Upgrade headers are forwarded
3. Check browser console for errors
4. Try different browser

### Metrics Not Updating

1. Verify Prometheus metrics endpoint: `curl http://localhost:9090/metrics`
2. Check database connectivity
3. Verify bot is processing messages
4. Check for errors in logs

### Slow Performance

1. Reduce auto-refresh interval
2. Limit log buffer size
3. Add database indexes
4. Enable query caching

## Development

### Running in Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn src.web.app:app --reload --port 8080

# In another terminal, run bot
python -m src.main
```

### Adding New Pages

1. Create template in `src/web/templates/`
2. Add route in `src/web/app.py`
3. Update navigation in templates

### Testing API Endpoints

```bash
# Install httpie
pip install httpie

# Test endpoints
http GET http://localhost:8080/api/stats
http GET http://localhost:8080/api/health
http GET "http://localhost:8080/api/recent_conversations?limit=5"
```

## Future Enhancements

- [ ] User authentication system
- [ ] Role-based access control
- [ ] Custom dashboard widgets
- [ ] Alert configuration UI
- [ ] Export reports (PDF, CSV)
- [ ] Dark/light theme toggle
- [ ] Mobile-responsive design
- [ ] Real-time chat with bot
- [ ] Knowledge base management UI
- [ ] A/B testing dashboard

---

**Need Help?** Check the main README.md or create an issue on GitHub.
