# VAMP Agent Backend - Complete Deployment Guide

**FastAPI Session-Based Evidence Collection System**

---

## 📋 Quick Reference

| Component | Status | Details |
|-----------|--------|---------|
| **main.py** | ✅ Ready | 400+ lines, complete FastAPI app |
| **config.py** | ✅ Ready | Encryption & credential management |
| **models.py** | ✅ Ready | Pydantic schemas for all endpoints |
| **connectors/session_based.py** | ✅ Ready | 5 platform connectors (350+ lines) |
| **Chrome Extension** | ✅ Ready | Cookie collection & month selector |
| **WebSocket Streaming** | ✅ Ready | Real-time scan updates |
| **Encrypted Credentials** | ✅ Ready | Fernet encryption at rest |
| **API Documentation** | ✅ Ready | Swagger UI + ReDoc |

---

## 🎯 What You Get

### Backend Features

```
✓ FastAPI framework (async/await)
✓ 8 HTTP endpoints (REST API)
✓ 1 WebSocket endpoint (real-time)
✓ 5 platform connectors (Outlook, OneDrive, Google Drive, Nextcloud, eFundi)
✓ Session-based auth (no OAuth)
✓ Encrypted credential storage (Fernet)
✓ CORS middleware for cross-origin
✓ Background task support
✓ Date range filtering
✓ Include/exclude text filters
✓ Connection manager for WebSocket broadcast
✓ Comprehensive error handling
✓ Detailed logging
✓ Swagger API documentation
```

### Chrome Extension Features

```
✓ Month/year date range selector
✓ Multi-platform checkbox selector
✓ Cookie collection from browser
✓ HTTP POST to backend
✓ Status display (success/error/loading)
✓ Backend connection check
✓ Real-time WebSocket integration
```

### Security Features

```
✓ Fernet (AES-128) encryption
✓ CORS restrictions
✓ Session-based (no exposed tokens)
✓ Encrypted credential file
✓ Error messages don't leak data
✓ HTTPS ready
```

---

## 🚀 5-Minute Setup

### Step 1: Create Project Structure

```bash
mkdir vamp-backend
cd vamp-backend

# Create directories
mkdir -p config connectors chrome_extension tests

# Create __init__.py files
touch connectors/__init__.py
touch tests/__init__.py
```

### Step 2: Copy Files

Copy these files to vamp-backend/:
1. `main.py` - FastAPI application
2. `config.py` - Encryption & settings
3. `models.py` - Pydantic models
4. `requirements.txt` - Python dependencies
5. `.env.example` - Environment template

Copy to `connectors/`:
6. `session_based.py` - Platform connectors

Copy to `chrome_extension/`:
7. `manifest.json` - Extension config
8. `popup.html` - Extension UI
9. `popup.js` - Extension logic

### Step 3: Setup Python

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Output example:
```
gvty9_6h-JNmz9kU4X-QbKjY8_VlH2Z1xU0v2p5kL9Q=
```

### Step 5: Create .env

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and set VAMP_ENCRYPTION_KEY
# VAMP_ENCRYPTION_KEY=gvty9_6h-JNmz9kU4X-QbKjY8_VlH2Z1xU0v2p5kL9Q=
```

### Step 6: Start Backend

```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 7: Load Chrome Extension

1. Open `chrome://extensions/`
2. Enable "Developer mode" (toggle top-right)
3. Click "Load unpacked"
4. Select `chrome_extension/` folder
5. Done! Extension appears in toolbar

---

## 📡 API Endpoints (Quick Reference)

### Health & Status

```bash
GET /health
# Returns: {"status": "healthy", "timestamp": "...", "version": "1.0.0"}

GET /health/readiness
# Returns: {"status": "ready", "services": {...}}

GET /api/config/encryption-key
# Returns: {"configured": true, "key_length": 44}
```

### Credential Management

```bash
# Save credentials
POST /api/credentials
{
    "service": "nextcloud",
    "credentials": {"username": "...", "password": "...", "base_url": "..."}
}

# Check if credentials exist
GET /api/credentials/{service}
# Returns: {"service": "nextcloud", "has_credentials": true}

# Delete credentials
DELETE /api/credentials/{service}
```

### Scraping (Synchronous)

```bash
POST /api/scrape
{
    "platform": "outlook",
    "cookies": [...],
    "start_month": 1,
    "end_month": 6,
    "start_year": 2025,
    "end_year": 2025,
    "include_filters": ["compliance"],
    "exclude_filters": ["spam"]
}

# Returns: {"platform": "outlook", "total_items": 42, "items": [...]}
```

### Scraping (Asynchronous)

```bash
POST /api/scrape/async
{
    "platform": "google_drive",
    "cookies": [...],
    "start_month": 3,
    "end_month": 9,
    "start_year": 2025,
    "end_year": 2025
}

# Returns: {"scan_id": "uuid-here", "status": "pending"}
# Connect to: ws://localhost:8000/ws/uuid-here
```

### WebSocket Updates

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scan-id-here');

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    // msg.type: "status" | "progress" | "evidence" | "error"
    // msg.data: type-specific data
    // msg.timestamp: ISO timestamp
};
```

### Platform Info

```bash
GET /api/supported-platforms
# Returns: {"platforms": [{"id": "outlook", "name": "...", ...}]}
```

---

## 🔐 Session-Based Authentication

### How It Works

```
1. User logs into platform in browser (Outlook, Google Drive, etc)
   → Browser stores session cookies
   
2. User opens VAMP Chrome extension
   → Clicks "Start Scan"
   
3. Extension collects cookies from logged-in platforms
   → chrome.cookies.getAll({domain: '.outlook.com'})
   
4. Extension sends cookies to backend
   → POST /api/scrape with cookies array
   
5. Backend uses cookies to authenticate API calls
   → Makes request as logged-in user
   → No new login needed
   
6. API returns evidence items
   → Backend returns Evidence objects with metadata
   
7. Real-time updates via WebSocket
   → Client sees progress in real-time
```

### Cookie Requirements

- **Outlook**: Authentication token or session cookie
- **OneDrive**: Microsoft auth cookie
- **Google Drive**: Google session cookie (HSID, SID, etc)
- **Nextcloud**: Saved username/password (no cookies)
- **eFundi**: Playwright browser session (no cookies)

---

## 🧠 Understanding the Architecture

### Request Flow

```
Chrome Extension
    ↓ (month selector, platform choice, cookies)
[popup.js]
    ↓ fetch() POST /api/scrape
HTTP Request (JSON payload)
    ↓
[main.py]
    ↓ (parses ScrapeRequest)
Route handler (/api/scrape)
    ↓ (creates connector)
[connectors/session_based.py]
    ↓ (uses cookies to authenticate)
Platform API (Outlook, Google Drive, etc)
    ↓ (returns data)
Connector filters by date range
    ↓
[main.py] (converts to Evidence objects)
    ↓ HTTP Response (JSON)
Chrome Extension
    ↓ Display results
User Interface
```

### Component Responsibility

```
main.py
  → FastAPI app setup
  → HTTP endpoints
  → WebSocket management
  → Request validation (Pydantic)

config.py
  → Environment variables
  → Encryption key management
  → Credential storage/retrieval
  → Settings class

models.py
  → Request schemas (ScrapeRequest, etc)
  → Response schemas (ScrapeResponse, etc)
  → Data models (Evidence, etc)
  → Validation rules

connectors/session_based.py
  → OutlookConnector (Outlook emails)
  → OneDriveConnector (OneDrive files)
  → GoogleDriveConnector (Google Drive files)
  → NextcloudConnector (NWU Nextcloud files)
  → EFundiConnector (Sakai LMS activity)
  → ConnectorFactory (creates connectors)
  → Base SessionConnector (shared methods)

chrome_extension/
  → popup.html (UI form)
  → popup.js (logic & communication)
  → manifest.json (extension config)
```

---

## 🔧 Configuration

### Default Settings (config.py)

```python
# API
API_HOST = "0.0.0.0"
API_PORT = 8000
DEBUG = False

# Session
SESSION_TIMEOUT = 3600  # 1 hour

# Connectors
CONNECTOR_TIMEOUT = 30
MAX_RETRIES = 3

# WebSocket
WS_HEARTBEAT_INTERVAL = 30

# CORS
CORS_ORIGINS = ["chrome-extension://*", "http://localhost:3000"]

# Paths
CREDENTIALS_FILE = Path("config/.vamp_credentials.enc")
```

### Override with .env

Create `.env` file to override any setting:

```bash
API_PORT=9000                        # Change port
DEBUG=True                           # Enable debug
SESSION_TIMEOUT=7200                 # 2 hours
CONNECTOR_TIMEOUT=60                 # 60 seconds
CORS_ORIGINS=["https://yourdomain"]  # Custom CORS
```

---

## 📊 Example Workflow

### Scenario: Compliance Audit for Q2 2025

1. **User Setup**
   ```bash
   cd vamp-backend
   source venv/bin/activate
   python main.py
   # Backend runs at http://localhost:8000
   ```

2. **Extension Setup**
   - Open chrome://extensions/
   - Load unpacked chrome_extension/ folder

3. **Login to Platforms**
   - User logs into Outlook (browser stores cookies)
   - User logs into Google Drive (browser stores cookies)
   - User saves Nextcloud credentials in VAMP settings

4. **Start Scan**
   - Extension: Set start_month=4, end_month=6 (Q2)
   - Extension: Select platforms (Outlook, Google Drive, Nextcloud)
   - Extension: Click "Start Scan"

5. **Backend Processing**
   - Backend receives POST /api/scrape
   - Creates OutlookConnector with cookies
   - Queries Outlook: `createdDateTime >= 2025-04-01`
   - Filters results: April, May, June only
   - Applies include/exclude filters if specified
   - Converts to Evidence objects
   - Repeats for Google Drive, Nextcloud

6. **WebSocket Updates** (if async)
   - Extension connects: `ws://localhost:8000/ws/scan-id`
   - Receives: {"type": "status", "data": {"status": "started"}}
   - Receives: {"type": "progress", "data": {"percentage": 25}}
   - Receives: {"type": "evidence", "data": {...}}
   - Receives: {"type": "status", "data": {"status": "completed"}}

7. **Results**
   - Total: 127 items collected
   - Outlook: 45 emails
   - Google Drive: 52 files
   - Nextcloud: 30 files
   - Display in extension UI

---

## 🚀 Production Deployment

### Requirements

- Python 3.8+
- PostgreSQL (optional, for persistence)
- Reverse proxy (nginx)
- SSL certificate

### Deployment Steps

1. **Create Production Environment**
   ```bash
   python -m venv vamp-prod
   source vamp-prod/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

2. **Generate Secure Encryption Key**
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. **Create Production .env**
   ```bash
   VAMP_ENCRYPTION_KEY=<secure_key>
   API_HOST=127.0.0.1  # Only local
   API_PORT=8000
   DEBUG=False
   CORS_ORIGINS=["https://yourdomain.com", "https://extension.url"]
   ```

4. **Run with Gunicorn**
   ```bash
   gunicorn main:app \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 127.0.0.1:8000 \
     --timeout 60 \
     --access-logfile /var/log/vamp/access.log \
     --error-logfile /var/log/vamp/error.log
   ```

5. **Nginx Reverse Proxy**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name api.vamp.yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomain/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain/privkey.pem;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

6. **Systemd Service** (optional)
   ```ini
   [Unit]
   Description=VAMP Backend
   After=network.target
   
   [Service]
   User=vamp
   WorkingDirectory=/home/vamp/vamp-backend
   Environment="PATH=/home/vamp/vamp-prod/bin"
   ExecStart=/home/vamp/vamp-prod/bin/gunicorn main:app \
       --workers 4 --worker-class uvicorn.workers.UvicornWorker \
       --bind 127.0.0.1:8000
   
   [Install]
   WantedBy=multi-user.target
   ```

---

## 🧪 Testing

### Unit Tests (Optional)

Create `tests/test_connectors.py`:

```python
import pytest
from datetime import datetime
from connectors.session_based import OutlookConnector

@pytest.mark.asyncio
async def test_outlook_connector_init():
    connector = OutlookConnector(cookies={'test': 'value'})
    assert connector.cookies == {'test': 'value'}

@pytest.mark.asyncio
async def test_outlook_fetch_evidence():
    connector = OutlookConnector(cookies={})
    # Mock API call
    evidence = await connector.fetch_evidence(
        datetime(2025, 1, 1),
        datetime(2025, 12, 31)
    )
    assert isinstance(evidence, list)
```

Run tests:
```bash
pip install pytest pytest-asyncio
pytest tests/
```

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health | jq

# Platforms
curl http://localhost:8000/api/supported-platforms | jq

# Encryption status
curl http://localhost:8000/api/config/encryption-key | jq

# Swagger UI
open http://localhost:8000/docs
```

---

## 📈 Monitoring & Logs

### Log Locations

```
Console output: STDOUT (when running with --reload)
Production logs: /var/log/vamp/
  - access.log: HTTP request logs
  - error.log: Application errors
```

### Viewing Logs

```bash
# Real-time logs
tail -f /var/log/vamp/error.log

# Recent errors
tail -50 /var/log/vamp/error.log | grep ERROR

# Filter by platform
grep "outlook" /var/log/vamp/error.log
```

### Performance Metrics

Add to requirements for monitoring:

```bash
pip install prometheus-client
```

Metrics:
- Request count and latency
- WebSocket connections
- Evidence items processed
- API errors by platform

---

## 🔒 Security Checklist

- [ ] VAMP_ENCRYPTION_KEY is secret (not in git)
- [ ] DEBUG=False in production
- [ ] CORS_ORIGINS set to specific domains
- [ ] HTTPS enabled (not HTTP)
- [ ] Credentials file permissions: 600
- [ ] Database password secure
- [ ] Logs don't contain sensitive data
- [ ] Session timeout appropriate
- [ ] Rate limiting configured
- [ ] API key rotation plan exists
- [ ] Backup strategy for credentials

---

## 🚨 Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Must be 3.8+

# Check dependencies
pip list | grep -E "fastapi|uvicorn"

# Check port in use
lsof -i :8000

# Start with verbose output
python -u main.py 2>&1 | tee app.log
```

### Extension not connecting

```bash
# Check BACKEND_URL in popup.js
grep "BACKEND_URL" chrome_extension/popup.js

# Check CORS in .env
grep "CORS" .env

# Browser console (F12 → Console tab)
# Look for CORS errors
```

### No evidence returned

```bash
# Check date range
# Ensure start_month <= end_month (same year)

# Check cookies
# User must be logged into platform

# Check logs
tail -f /var/log/vamp/error.log

# Test endpoint manually
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "outlook",
    "cookies": [],
    "start_month": 1,
    "end_month": 12,
    "start_year": 2025,
    "end_year": 2025
  }'
```

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **Cryptography (Fernet)**: https://cryptography.io/
- **Chrome Extensions**: https://developer.chrome.com/docs/extensions/
- **WebSocket**: https://websockets.readthedocs.io/

---

## ✅ Deployment Checklist

- [ ] All 9 files copied to vamp-backend/
- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] requirements.txt installed
- [ ] Encryption key generated and set in .env
- [ ] .env file created (from .env.example)
- [ ] Backend starts without errors
- [ ] Chrome extension loads without errors
- [ ] Health endpoint returns 200
- [ ] API documentation loads (http://localhost:8000/docs)
- [ ] Extension can communicate with backend
- [ ] Successful test scrape with at least one platform
- [ ] WebSocket connection works (test at /ws/test-id)

---

## 🎉 You're Ready!

Your VAMP Agent Backend is now deployed and ready to collect evidence. 🧛‍♂️

**Next Steps:**
1. Test with real platform cookies
2. Set up Nextcloud/eFundi credentials
3. Run compliance scan for a date range
4. Verify evidence collection
5. Export results

**Questions?** Check the README.md or review inline code comments.

---

**Happy Scanning! 🧛‍♂️**

*VAMP Agent Backend - Evidence Collection Made Simple*
