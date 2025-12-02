# VAMP Agent FastAPI Backend - Complete Setup Guide

**Session-Based Evidence Collection with Chrome Extension Integration**

---

## 📋 Project Structure

```
vamp-backend/
├── main.py                          # FastAPI application
├── config.py                        # Configuration & encryption
├── models.py                        # Pydantic schemas
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables
├── .env.example                    # Example env file
├── config/
│   └── .vamp_credentials.enc       # Encrypted credentials (auto-generated)
├── connectors/
│   ├── __init__.py
│   └── session_based.py            # Cookie-based connectors
├── tests/
│   └── test_connectors.py
├── chrome_extension/
│   ├── manifest.json               # Extension manifest
│   ├── popup.html                  # Extension UI
│   ├── popup.js                    # Extension logic
│   └── background.js               # Background service worker
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Create project directory
mkdir vamp-backend && cd vamp-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Encryption Key

```python
from cryptography.fernet import Fernet

# Generate and save encryption key
key = Fernet.generate_key()
print(key.decode())  # Save this to .env

# Output example: gvty9_6h-JNmz9kU4X-QbKjY8_VlH2Z1xU0v2p5kL9Q=
```

### 3. Create .env File

```bash
# .env
VAMP_ENCRYPTION_KEY=your_generated_key_here
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
SESSION_TIMEOUT=3600
CONNECTOR_TIMEOUT=30
```

### 4. Start Backend Server

```bash
python main.py

# Or with uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend runs at: `http://localhost:8000`

---

## 📡 API Endpoints

### Health Check

```bash
GET /health
GET /health/readiness
```

### Credential Management

```bash
# Save credentials for Nextcloud/eFundi
POST /api/credentials
{
    "service": "nextcloud",
    "credentials": {
        "username": "user@nwu.ac.za",
        "password": "your_password",
        "base_url": "https://nextcloud.nwu.ac.za"
    }
}

# Get credential status
GET /api/credentials/{service}

# Delete credentials
DELETE /api/credentials/{service}
```

### Web Scraping

```bash
# Synchronous scraping with cookies
POST /api/scrape
{
    "platform": "outlook",
    "cookies": [
        {
            "name": "Authorization",
            "value": "Bearer token...",
            "domain": ".outlook.com",
            "path": "/",
            "secure": true,
            "httpOnly": true
        }
    ],
    "start_month": 1,
    "end_month": 12,
    "start_year": 2025,
    "end_year": 2025,
    "include_filters": ["compliance", "policy"],
    "exclude_filters": ["spam", "delete"]
}

# Async scraping with WebSocket updates
POST /api/scrape/async
{
    "platform": "google_drive",
    "cookies": [...],
    "start_month": 1,
    "end_month": 6,
    "start_year": 2025,
    "end_year": 2025
}

# Returns: { "scan_id": "uuid-here", "status": "pending" }
```

### WebSocket Real-Time Updates

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/scan-id-here');

ws.onopen = () => {
    console.log('Connected');
    ws.send('ping');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Type:', message.type);   // "status", "evidence", "progress", "error"
    console.log('Data:', message.data);
    console.log('Timestamp:', message.timestamp);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};
```

### Platform Info

```bash
GET /api/supported-platforms
```

Response:
```json
{
    "platforms": [
        {
            "id": "outlook",
            "name": "Microsoft Outlook",
            "auth_method": "cookie-based",
            "requires_credentials": false
        },
        {
            "id": "nextcloud",
            "name": "NWU Nextcloud",
            "auth_method": "saved-credentials",
            "requires_credentials": true
        },
        ...
    ]
}
```

---

## 🔐 Session-Based Authentication

### Flow

1. **Chrome Extension** collects browser cookies from active sessions
2. **Extension sends cookies** to FastAPI backend in `/api/scrape` request
3. **Backend uses cookies** to make authenticated API calls
4. **No OAuth needed** - leverages existing browser sessions

### Supported Platforms

| Platform | Auth Method | Cookie Domain |
|----------|-------------|---------------|
| Outlook | Cookie-based | `.outlook.com` |
| OneDrive | Cookie-based | `.onedrive.live.com` |
| Google Drive | Cookie-based | `.drive.google.com` |
| Nextcloud (NWU) | Saved credentials | `nextcloud.nwu.ac.za` |
| eFundi | Playwright session | `efundi.nwu.ac.za` |

---

## 💻 Chrome Extension Installation

### 1. Create Extension Folder Structure

```
chrome_extension/
├── manifest.json
├── popup.html
├── popup.js
└── background.js  (optional)
```

### 2. Load Extension in Chrome

1. Open `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select the `chrome_extension/` folder
5. Extension appears in Chrome toolbar

### 3. Configure Extension

Edit `popup.js`:
```javascript
const BACKEND_URL = 'http://localhost:8000';  // Change if backend on different host
```

### 4. Use Extension

1. Click extension icon in toolbar
2. Select date range (start/end month & year)
3. Choose platforms to scan
4. Click **Start Scan**
5. Watch status updates in real-time

---

## 🔒 Encrypted Credential Storage

### Why Encryption?

- Credentials stored encrypted at rest
- Only decrypt when needed
- Fernet (AES-128) encryption
- Separate encryption key per environment

### How It Works

```python
from config import credential_manager

# Save credentials
credential_manager.save_credentials('nextcloud', {
    'username': 'user@nwu.ac.za',
    'password': 'secure_password',
    'base_url': 'https://nextcloud.nwu.ac.za'
})

# Retrieve credentials
creds = credential_manager.get_credentials('nextcloud')
# Returns: {'username': '...', 'password': '...', 'base_url': '...'}

# Delete credentials
credential_manager.delete_credentials('nextcloud')
```

### Storage Location

Encrypted credentials stored in: `config/.vamp_credentials.enc`

---

## 📊 Evidence Model

Each evidence item includes:

```python
{
    "id": "msg-12345",                          # Unique identifier
    "platform": "outlook",                      # Source platform
    "title": "Policy Compliance Review",        # Evidence title
    "description": "Email about policy updates",# Brief description
    "created_date": "2025-12-02T10:30:00Z",    # Creation timestamp
    "modified_date": "2025-12-02T14:00:00Z",   # Last modified
    "url": "https://outlook.com/...",          # Direct link to item
    "status": "collected",                      # State (collected, filtered, classified)
    "metadata": {                               # Platform-specific data
        "sender": "admin@nwu.ac.za",
        "categories": ["compliance", "important"]
    }
}
```

---

## 🧪 Testing

### Test Health Endpoint

```bash
curl http://localhost:8000/health
```

### Test Scraping (with sample cookies)

```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "outlook",
    "cookies": [
      {"name": "test_cookie", "value": "test_value", "domain": ".outlook.com", "path": "/"}
    ],
    "start_month": 1,
    "end_month": 12,
    "start_year": 2025,
    "end_year": 2025
  }'
```

### Test WebSocket

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/test-scan-id"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            print(json.loads(message))

asyncio.run(test_websocket())
```

---

## 🛠️ Connectors Reference

### OutlookConnector

```python
from connectors.session_based import OutlookConnector

connector = OutlookConnector(
    cookies={'auth_token': 'value', ...}
)
await connector.connect()
evidence = await connector.fetch_evidence(start_date, end_date)
await connector.disconnect()
```

**Fetches:**
- Emails by date range
- Subject, preview, sender
- Message categories

### OneDriveConnector

**Fetches:**
- Recent files from OneDrive
- File metadata (size, type)
- Modified dates

### GoogleDriveConnector

**Fetches:**
- Files by creation date range
- MIME type and size
- Web view links

### NextcloudConnector

```python
from connectors.session_based import NextcloudConnector

connector = NextcloudConnector(
    base_url='https://nextcloud.nwu.ac.za',
    username='user@nwu.ac.za',
    password='password'
)
```

**Fetches:**
- Files from Nextcloud shares
- File metadata
- Owner information

### EFundiConnector

```python
from connectors.session_based import EFundiConnector

connector = EFundiConnector(
    base_url='https://efundi.nwu.ac.za'
)
```

**Uses:**
- Playwright for browser automation
- Existing browser session
- No separate credentials

---

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Encryption
VAMP_ENCRYPTION_KEY=<your_fernet_key>

# Timeouts
SESSION_TIMEOUT=3600          # Session validity (seconds)
CONNECTOR_TIMEOUT=30          # API request timeout (seconds)
MAX_RETRIES=3                 # Retry attempts

# CORS
CORS_ORIGINS=["http://localhost:3000", "chrome-extension://*"]
```

### Pydantic Settings

Edit `config.py`:

```python
class VAMPSettings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    SESSION_TIMEOUT: int = 3600
    CONNECTOR_TIMEOUT: int = 30
    # ... more settings
```

---

## 📈 Real-Time WebSocket Example

### Frontend (React/Vue)

```javascript
// Connect to scan
const ws = new WebSocket(`ws://localhost:8000/ws/${scanId}`);

ws.onmessage = (event) => {
    const { type, data, timestamp } = JSON.parse(event.data);
    
    switch(type) {
        case 'status':
            console.log('Scan Status:', data.status);
            break;
        case 'evidence':
            console.log('Evidence Found:', data.evidence);
            setEvidenceList(prev => [...prev, data.evidence]);
            break;
        case 'progress':
            setProgress(data.percentage);
            break;
        case 'error':
            console.error('Scan Error:', data.error);
            break;
    }
};

ws.onclose = () => console.log('Connection closed');
```

---

## 🐛 Troubleshooting

### Extension Not Connecting

1. Check `BACKEND_URL` in `popup.js` matches backend host
2. Verify CORS origins in `.env` include extension ID
3. Check browser console for errors (F12 → Console)

### Cookies Not Found

1. User must be logged into platform in browser
2. Verify correct domain in `getDomainForPlatform()`
3. Check cookie permissions in `manifest.json`

### Backend Won't Start

1. Verify Python version: `python --version` (3.8+)
2. Check dependencies: `pip list | grep fastapi`
3. Verify port 8000 is available: `netstat -an | grep 8000`

### No Evidence Returned

1. Check date range includes data in platform
2. Verify cookies are valid (not expired)
3. Check backend logs for API errors
4. Test platform API directly with curl

### WebSocket Disconnects

1. Ensure firewall allows WebSocket on port 8000
2. Check browser console for connection errors
3. Verify client sends ping periodically: `ws.send('ping')`

---

## 📚 Additional Resources

- **FastAPI Docs:** http://localhost:8000/docs (Swagger UI)
- **FastAPI ReDoc:** http://localhost:8000/redoc
- **Chrome Extensions Docs:** https://developer.chrome.com/docs/extensions/
- **Pydantic Validation:** https://docs.pydantic.dev/
- **Fernet Encryption:** https://cryptography.io/en/latest/

---

## 🔄 Next Steps

1. **Database Integration** - Add PostgreSQL for scan history
2. **Evidence Classification** - Implement policy-matching logic
3. **Report Generation** - Create PDF compliance reports
4. **Authentication** - Add FastAPI security (JWT tokens)
5. **Monitoring** - Add Prometheus metrics
6. **Testing** - Write comprehensive unit tests

---

## 📝 License

VAMP Agent Backend © 2025 - Northwest University

---

**Happy Scanning! 🧛‍♂️**
