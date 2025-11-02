# 🚀 Quick Start: Web Dashboard

Get your monitoring dashboard up and running in 5 minutes!

## Prerequisites

- Python 3.11+ installed
- Git installed
- 5 minutes of your time

## Step 1: Clone & Setup (1 minute)

```bash
cd slack-helper-bot
./scripts/setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Configure (2 minutes)

### Option A: Just Dashboard (No Slack)

Create `.env` with minimal config:
```bash
cat > .env << 'EOF'
# Minimal config for dashboard testing
SLACK_BOT_TOKEN=xoxb-dummy
SLACK_APP_TOKEN=xapp-dummy
SLACK_SIGNING_SECRET=dummy
DATABASE_URL=sqlite+aiosqlite:///./test.db
EOF
```

Initialize database:
```bash
alembic upgrade head
```

### Option B: Full Bot + Dashboard

Follow the main README.md to configure Slack tokens.

## Step 3: Start Dashboard (30 seconds)

```bash
python -m src.main
```

You should see:
```
INFO Starting Slack RAG Assistant version=0.1.0
INFO Application setup complete
INFO Starting Slack bot and web dashboard
INFO Services started web_dashboard=http://localhost:8080 metrics=http://localhost:9090/metrics
```

## Step 4: Access Dashboard (30 seconds)

Open your browser to:

### Main Dashboard
**URL**: http://localhost:8080

Features:
- ✅ Real-time statistics
- ✅ Question type distribution
- ✅ Recent conversations
- ✅ Channel stats
- ✅ Auto-refresh every 30s

### Logs Viewer
**URL**: http://localhost:8080/logs

Features:
- ✅ Live log streaming
- ✅ Filter by level
- ✅ Search logs
- ✅ Export as JSON
- ✅ Pause/resume

### Prometheus Metrics
**URL**: http://localhost:9090/metrics

Features:
- ✅ Raw metrics format
- ✅ Grafana compatible
- ✅ All bot metrics

## Step 5: Test It Out (1 minute)

### Add Sample Data

Run this Python script to add sample conversations:

```python
import asyncio
from datetime import datetime
from src.models.base import AsyncSessionLocal
from src.models.conversation import Conversation, ConversationStatus, QuestionType

async def add_sample_data():
    async with AsyncSessionLocal() as session:
        # Add sample conversations
        conversations = [
            Conversation(
                channel_id="C_TEST001",
                thread_ts="1697123456.000100",
                user_id="U_TEST001",
                question_type=QuestionType.BUG,
                status=ConversationStatus.ACTIVE,
                summary="App crashes on startup",
            ),
            Conversation(
                channel_id="C_TEST002",
                thread_ts="1697123457.000100",
                user_id="U_TEST002",
                question_type=QuestionType.HOW_TO,
                status=ConversationStatus.RESOLVED,
                summary="How to deploy to production?",
            ),
            Conversation(
                channel_id="C_TEST001",
                thread_ts="1697123458.000100",
                user_id="U_TEST003",
                question_type=QuestionType.FEATURE_REQUEST,
                status=ConversationStatus.ACTIVE,
                summary="Add dark mode support",
                jira_key="FEAT-123",
            ),
        ]

        for conv in conversations:
            session.add(conv)

        await session.commit()
        print("✅ Added 3 sample conversations")

asyncio.run(add_sample_data())
```

Save as `add_samples.py` and run:
```bash
python add_samples.py
```

### Refresh Dashboard

Go to http://localhost:8080 and click "🔄 Refresh"

You should now see:
- 3 total conversations
- 2 active conversations
- Type distribution chart
- Recent conversations table

## Docker Quick Start

Prefer Docker? Here's the fastest way:

```bash
# 1. Create .env file (see Step 2 above)

# 2. Start with docker-compose
docker-compose up -d

# 3. Wait 10 seconds for startup

# 4. Open dashboard
open http://localhost:8080
```

Check logs:
```bash
docker-compose logs -f app
```

Stop:
```bash
docker-compose down
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or change port in src/main.py
```

### Dashboard Shows No Data

```bash
# Check database
sqlite3 slack_rag_assistant.db "SELECT COUNT(*) FROM conversations;"

# Add sample data (see Step 5)
python add_samples.py
```

### WebSocket Not Connecting

```bash
# Check browser console for errors
# Verify bot is running
ps aux | grep python

# Test WebSocket manually
pip install websockets
python -c "
import asyncio
import websockets

async def test():
    uri = 'ws://localhost:8080/ws/logs'
    async with websockets.connect(uri) as ws:
        print('Connected!')
        await ws.send('ping')
        response = await ws.recv()
        print(f'Response: {response}')

asyncio.run(test())
"
```

### Can't Access Dashboard

```bash
# Check if server is listening
netstat -an | grep 8080

# Try localhost explicitly
curl http://127.0.0.1:8080/api/health

# Check firewall
sudo ufw status
```

## Next Steps

### Integrate with Slack

1. Create Slack app at https://api.slack.com/apps
2. Configure tokens in `.env`
3. Install bot to workspace
4. Send messages in configured channels
5. Watch dashboard update in real-time!

### Add Grafana Dashboard

```bash
# Start Prometheus + Grafana
docker run -d -p 9090:9090 prom/prometheus
docker run -d -p 3000:3000 grafana/grafana

# Configure Prometheus scrape target:
# - http://host.docker.internal:9090/metrics

# Import Grafana dashboard
# - Dashboard ID: Create custom
# - Data source: Prometheus
# - Queries: Use slack_rag_* metrics
```

### Customize Dashboard

Edit templates:
```bash
# Main dashboard
vi src/web/templates/dashboard.html

# Logs viewer
vi src/web/templates/logs.html

# Add custom CSS/JS as needed
```

### Add Authentication

```python
# In src/web/app.py
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@app.get("/")
async def dashboard(credentials: HTTPBasicCredentials = Depends(security)):
    # Verify credentials
    if credentials.username != "admin" or credentials.password != "secret":
        raise HTTPException(401, "Invalid credentials")
    # ... rest of code
```

## Production Deployment

### Using Nginx

```nginx
server {
    listen 80;
    server_name dashboard.example.com;

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

### Using Caddy

```
dashboard.example.com {
    reverse_proxy localhost:8080
}
```

### Environment Variables

Add to `.env`:
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@host/db
```

## Tips & Tricks

### Auto-Start on Boot (systemd)

```bash
sudo tee /etc/systemd/system/slack-rag-bot.service << 'EOF'
[Unit]
Description=Slack RAG Assistant
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/slack-helper-bot
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m src.main
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable slack-rag-bot
sudo systemctl start slack-rag-bot
```

### Monitor with tmux

```bash
# Create session
tmux new -s bot

# Split windows
Ctrl+B then %  # Vertical split
Ctrl+B then "  # Horizontal split

# Window 1: Run bot
python -m src.main

# Window 2: Watch logs
tail -f bot.log

# Window 3: Monitor
watch -n 2 curl -s http://localhost:8080/api/stats | jq
```

### Backup Database

```bash
# SQLite
sqlite3 slack_rag_assistant.db .dump > backup.sql

# PostgreSQL
pg_dump slack_rag_assistant > backup.sql
```

## Resources

- **Main README**: [README.md](README.md)
- **Dashboard Guide**: [WEB_DASHBOARD.md](WEB_DASHBOARD.md)
- **Implementation Guide**: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- **API Docs**: http://localhost:8080/docs (FastAPI auto-generated)

## Support

Having issues? Try:
1. Check this guide again
2. Read [WEB_DASHBOARD.md](WEB_DASHBOARD.md)
3. Check GitHub issues
4. Create new issue with logs

---

**Enjoy your monitoring dashboard! 📊**
