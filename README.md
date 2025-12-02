# 🧛 VAMP Agent Backend
**FastAPI Session-Based Evidence Collection System**

Session-based authentication with Chrome extension integration. No OAuth flows, no external AI APIs—pure logic gates and browser cookies.

---

## 🎯 Overview

VAMP Agent Backend is a production-ready FastAPI application for collecting evidence across multiple platforms (Outlook, OneDrive, Google Drive, Nextcloud, eFundi) using existing browser sessions. Built for NWU compliance auditing.

### Key Benefits

- ✅ **No OAuth complexity** - Uses existing browser cookies
- ✅ **No API keys** - Session-based authentication
- ✅ **No external AI** - Pure logic-gate processing
- ✅ **Real-time WebSocket** - Live scan updates
- ✅ **Encrypted credentials** - Fernet encryption at rest
- ✅ **Multi-platform** - 5 connected platforms
- ✅ **Chrome extension** - One-click activation
- ✅ **Date range filtering** - Month/year selectors

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CHROME BROWSER                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────────────────────┐     │
│  │   Platform   │      │  VAMP Chrome Extension       │     │
│  │   Sessions   │◄─────┤  - Date Selector             │     │
│  │              │      │  - Platform Chooser          │     │
│  │  Outlook     │      │  - Cookie Collector          │     │
│  │  OneDrive    │      │  - WebSocket Client          │     │
│  │  G Drive     │      └──────────────────────────────┘     │
│  └──────────────┘                     │                      │
│                                       │ HTTP POST + Cookies  │
└───────────────────────────────────────┼──────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND (Port 8000)               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  HTTP Endpoints                                      │    │
│  │  • /api/scrape (POST) - Sync scraping              │    │
│  │  • /api/scrape/async (POST) - Async scraping       │    │
│  │  • /api/credentials/* - Credential mgmt            │    │
│  │  • /health - Health checks                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  WebSocket Endpoints                                │    │
│  │  • /ws/{scan_id} - Real-time updates               │    │
│  │    - status, progress, evidence, errors            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────────────────┐    │
│  │   Connectors     │  │  Config & Encryption         │    │
│  │  ────────────    │  │  ──────────────────          │    │
│  │  • Outlook       │  │  • Fernet encryption         │    │
│  │  • OneDrive      │  │  • Credential storage        │    │
│  │  • Google Drive  │  │  • Settings management       │    │
│  │  • Nextcloud     │  │  • CORS configuration        │    │
│  │  • eFundi        │  └──────────────────────────────┘    │
│  └──────────────────┘                                       │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────────────────┐    │
│  │   Models         │  │  Evidence Processing         │    │
│  │  ────────────    │  │  ──────────────────────      │    │
│  │  • Evidence      │  │  • Date range filtering      │    │
│  │  • SessionCookie │  │  • Include/exclude filters   │    │
│  │  • ScrapeRequest │  │  • Status tracking           │    │
│  │  • WebSocket Msg │  │  • Error handling            │    │
│  └──────────────────┘  └──────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │
         ├─► Microsoft API (Outlook, OneDrive) - with cookies
         ├─► Google Drive API - with cookies
         ├─► NWU Nextcloud API - with saved credentials
         └─► Sakai/eFundi - Playwright browser automation
```

---

## 📁 File Structure

```
vamp-backend/
├── main.py                              # FastAPI application (400+ lines)
├── config.py                            # Configuration & encryption (150+ lines)
├── models.py                            # Pydantic models (120+ lines)
├── requirements.txt                     # Python dependencies
├── .env                                 # Environment config (create from .env.example)
├── .env.example                         # Example environment file
│
├── config/
│   └── .vamp_credentials.enc            # Encrypted credentials (auto-created)
│
├── connectors/
│   ├── __init__.py
│   └── session_based.py                 # 5 platform connectors (350+ lines)
│
├── chrome_extension/
│   ├── manifest.json                    # Extension configuration
│   ├── popup.html                       # Extension UI (month selector, platforms)
│   └── popup.js                         # Extension logic (cookie collection)
│
├── tests/
│   └── test_connectors.py               # Unit tests (optional)
│
└── README.md                            # This file
```

---

## 🚀 Quick Start (5 Minutes)

### 1. Setup Python Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate              # macOS/Linux
# or
venv\Scripts\activate                 # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output key.

### 3. Create .env File

```bash
# .env
VAMP_ENCRYPTION_KEY=<paste_your_key_here>
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
SESSION_TIMEOUT=3600
CONNECTOR_TIMEOUT=30
```

### 4. Start Backend

```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend available at: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 5. Install Chrome Extension

1. Open `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select `chrome_extension/` folder
5. Extension appears in toolbar

---

## 📡 API Usage Examples

### Example 1: Scrape Outlook (Synchronous)

```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "outlook",
    "cookies": [
      {
        "name": "Authorization",
        "value": "Bearer eyJ0eXAi...",
        "domain": ".outlook.com",
        "path": "/",
        "secure": true,
        "httpOnly": true
      }
    ],
    "start_month": 1,
    "end_month": 6,
    "start_year": 2025,
    "end_year": 2025,
    "include_filters": ["compliance", "policy"]
  }'
```

### Example 2: Async Scraping with WebSocket

```bash
# Request scan
curl -X POST http://localhost:8000/api/scrape/async \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "google_drive",
    "cookies": [...],
    "start_month": 3,
    "end_month": 9,
    "start_year": 2025,
    "end_year": 2025
  }'

# Returns:
# {
#   "scan_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "pending",
#   "message": "Connect to /ws/550e8400-e29b-41d4-a716-446655440000"
# }

# Connect to WebSocket for updates
websocat ws://localhost:8000/ws/550e8400-e29b-41d4-a716-446655440000
```

### Example 3: Save Nextcloud Credentials

```bash
curl -X POST http://localhost:8000/api/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "service": "nextcloud",
    "credentials": {
      "username": "user@nwu.ac.za",
      "password": "secure_password",
      "base_url": "https://nextcloud.nwu.ac.za"
    }
  }'
```

---

## 🔐 Session-Based Authentication Flow

```
User Workflow:
┌─────────────┐
│ 1. User     │
│ logs into   │ Credentials entered directly into platform browser
│ Outlook,    │
│ etc via     │ Browser stores session cookies
│ browser     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 2. Extension│
│ collects    │ chrome.cookies.getAll({domain: '.outlook.com'})
│ cookies     │ Returns all cookies for logged-in session
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 3. Send to  │ POST /api/scrape with cookies array
│ Backend     │ No manual token entry needed
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 4. Backend  │
│ uses cookies│ Makes authenticated API calls using existing session
│ to auth     │ Reuses browser session—no new login
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 5. Evidence │
│ returned    │ JSON array of Evidence objects
└─────────────┘

Key Advantages:
✓ No OAuth flows—use existing browser session
✓ No API keys to manage
✓ No token refresh logic
✓ User already logged in—just reuse those cookies
✓ Works with 2FA (cookies already have MFA proof)
```

---

## 🎯 Supported Platforms

| Platform | Auth | Connector | Status |
|----------|------|-----------|--------|
| **Outlook** | Cookie | HTTP API | ✅ Ready |
| **OneDrive** | Cookie | Microsoft Graph | ✅ Ready |
| **Google Drive** | Cookie | Google Drive API | ✅ Ready |
| **NWU Nextcloud** | Credentials | HTTP Basic Auth | ✅ Ready |
| **eFundi (Sakai)** | Session | Playwright WebDriver | ✅ Ready |

---

## 🔄 Request/Response Flow

### ScrapeRequest Schema

```python
{
    "platform": "outlook|onedrive|google_drive|nextcloud|efundi",
    "cookies": [                      # From Chrome extension
        {
            "name": str,
            "value": str,
            "domain": str,
            "path": str,              # Default: "/"
            "secure": bool,           # Default: False
            "httpOnly": bool,         # Default: False
            "expires": float|null     # Optional
        }
    ],
    "start_month": 1-12,              # Required
    "end_month": 1-12,                # Required
    "start_year": int,                # Default: 2025
    "end_year": int,                  # Default: 2025
    "include_filters": ["compliance"], # Optional - OR logic
    "exclude_filters": ["spam"]       # Optional - OR logic
}
```

### ScrapeResponse Schema

```python
{
    "platform": "outlook",
    "total_items": 42,
    "items": [
        {
            "id": "msg-001",
            "platform": "outlook",
            "title": "Policy Update",
            "description": "Email about compliance",
            "created_date": "2025-03-15T10:30:00Z",
            "modified_date": "2025-03-15T14:00:00Z",
            "url": "https://outlook.com/mail/...",
            "status": "collected",
            "metadata": {
                "sender": "admin@nwu.ac.za",
                "categories": ["compliance"]
            }
        },
        ...
    ],
    "errors": [],
    "timestamp": "2025-12-02T17:30:00Z"
}
```

### WebSocket Message Schema

```python
{
    "type": "status|progress|evidence|error",
    "data": {
        # Type-specific data
        "status": "started|running|completed|failed",
        "percentage": 0-100,
        "evidence": {...},
        "error": "error message"
    },
    "timestamp": "2025-12-02T17:30:00Z"
}
```

---

## 🛠️ Configuration

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0              # Listen on all interfaces
API_PORT=8000                 # FastAPI port
DEBUG=False                   # Disable debug mode in production

# Encryption
VAMP_ENCRYPTION_KEY=<key>     # Generate: Fernet.generate_key()

# Timeouts
SESSION_TIMEOUT=3600          # Session validity (seconds)
CONNECTOR_TIMEOUT=30          # API request timeout
MAX_RETRIES=3                 # Retry failed requests

# CORS
CORS_ORIGINS=["http://localhost:3000", "chrome-extension://*"]

# Paths
CREDENTIALS_FILE=config/.vamp_credentials.enc
```

### In Code (config.py)

```python
from config import settings

print(settings.API_HOST)           # "0.0.0.0"
print(settings.API_PORT)           # 8000
print(settings.SESSION_TIMEOUT)    # 3600
```

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
# {"status": "healthy", "timestamp": "...", "version": "1.0.0"}
```

### List Platforms
```bash
curl http://localhost:8000/api/supported-platforms | jq
```

### Check Encryption Key
```bash
curl http://localhost:8000/api/config/encryption-key
```

### Swagger UI
```
http://localhost:8000/docs
```

---

## 🔒 Security Features

✅ **Encrypted Credential Storage**
- Fernet (AES-128) encryption
- Credentials stored in `config/.vamp_credentials.enc`
- Decrypted only on demand
- Unique key per environment

✅ **Session-Based Authentication**
- No API keys or tokens to manage
- Reuses existing browser sessions
- Works with 2FA (cookies have proof)
- Cookie expiration handled automatically

✅ **CORS Configuration**
- Restricted to known origins
- Chrome extension origin supported
- Frontend origin configurable

✅ **Error Handling**
- Exceptions caught and logged
- Generic error messages to client
- Detailed logs for debugging
- No sensitive data in responses

---

## 📊 Connector Details

### OutlookConnector
- **Auth**: Browser cookies
- **Scope**: Email inbox, calendar
- **Returns**: Messages with subject, preview, sender
- **API**: Microsoft Graph v2.0

### OneDriveConnector
- **Auth**: Browser cookies
- **Scope**: Recent files, shares
- **Returns**: Files with metadata, size, dates
- **API**: Microsoft Graph v1.0

### GoogleDriveConnector
- **Auth**: Browser cookies
- **Scope**: My Drive, shared files
- **Returns**: Files with MIME type, size, URLs
- **API**: Google Drive v3

### NextcloudConnector
- **Auth**: Saved credentials (username/password)
- **Scope**: User shares, public files
- **Returns**: File metadata with owner info
- **API**: HTTP Basic Auth

### EFundiConnector
- **Auth**: Playwright browser session
- **Scope**: Course files, announcements
- **Returns**: Activity with course context
- **API**: Sakai/eFundi WebDriver

---

## 🚀 Deployment

### Development
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Gunicorn)
```bash
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 --timeout 30
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t vamp-backend .
docker run -p 8000:8000 -e VAMP_ENCRYPTION_KEY=$KEY vamp-backend
```

---

## 📝 Logging

Logs to console with format:
```
2025-12-02 17:30:45 - vamp.main - INFO - Scraping outlook from 2025-01-01 to 2025-06-30
2025-12-02 17:30:46 - vamp.connectors - INFO - Connecting to Outlook via session cookies
2025-12-02 17:30:48 - vamp.connectors - INFO - Fetched 42 emails from Outlook
```

Configure logging in `main.py`:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## 🐛 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Port 8000 in use | Another service using port | `lsof -i :8000` then kill process |
| Extension not connecting | Wrong BACKEND_URL | Edit `popup.js` with correct host |
| No cookies found | User not logged in | Log into platform in browser first |
| Credentials not saving | Missing encryption key | Generate and set VAMP_ENCRYPTION_KEY |
| WebSocket closes | Firewall blocking | Open port 8000, allow WebSocket in firewall |
| Evidence list empty | Date range outside data | Adjust start_month/end_month to match data |
| API returns 500 | Backend error | Check logs: `tail -f logs/app.log` |

---

## 📚 API Reference

See full API docs at:
```
http://localhost:8000/docs
```

Or in ReDoc format:
```
http://localhost:8000/redoc
```

---

## 🔄 Next Implementations

- [ ] PostgreSQL for scan history
- [ ] Evidence classification (regex/NLP rules)
- [ ] PDF report generation
- [ ] JWT authentication for frontend
- [ ] Scan scheduling (APScheduler)
- [ ] Prometheus metrics
- [ ] Full test suite
- [ ] Rate limiting
- [ ] Data export (CSV, JSON, XML)
- [ ] Evidence tagging system
- [ ] Dashboard frontend (React/Vue)
- [ ] Compliance scoring logic

---

## 👨‍💻 Development

### Local Development Setup

```bash
# Clone repo
git clone https://github.com/yourusername/vamp-backend.git
cd vamp-backend

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > .env.key

# Create .env
echo "VAMP_ENCRYPTION_KEY=$(cat .env.key)" > .env

# Run tests
pytest tests/

# Start dev server
uvicorn main:app --reload
```

### Code Style

```bash
# Format code
black *.py connectors/

# Check linting
pylint *.py connectors/

# Type checking
mypy --ignore-missing-imports main.py config.py models.py
```

---

## 📄 License

VAMP Agent Backend © 2025 Northwest University

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Support

For issues and questions:
- 📝 Create an issue on GitHub
- 💬 Contact: dev@nwu.ac.za
- 📚 Docs: See README and inline code comments

---

**Happy Scanning! 🧛‍♂️**

*VAMP Agent Backend - Evidence Collection Made Simple*
