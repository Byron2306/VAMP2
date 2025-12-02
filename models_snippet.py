
# 3. models.py - Evidence and request schemas
models_py = '''"""
VAMP Agent Data Models and Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class PlatformType(str, Enum):
    """Supported platforms"""
    OUTLOOK = "outlook"
    ONEDRIVE = "onedrive"
    GOOGLE_DRIVE = "google_drive"
    NEXTCLOUD = "nextcloud"
    EFUNDI = "efundi"


class EvidenceStatus(str, Enum):
    """Evidence processing status"""
    COLLECTED = "collected"
    FILTERED = "filtered"
    CLASSIFIED = "classified"
    ARCHIVED = "archived"


class Evidence(BaseModel):
    """Evidence item from connected platforms"""
    id: str
    platform: PlatformType
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    created_date: datetime
    modified_date: Optional[datetime] = None
    url: Optional[str] = None
    status: EvidenceStatus = EvidenceStatus.COLLECTED
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg-12345",
                "platform": "outlook",
                "title": "Policy Compliance Review",
                "description": "Email regarding policy updates",
                "created_date": "2025-12-02T10:30:00Z",
                "url": "https://outlook.com/...",
                "status": "collected",
                "metadata": {"sender": "admin@nwu.ac.za"}
            }
        }


class SessionCookie(BaseModel):
    """Browser session cookie from Chrome extension"""
    name: str
    value: str
    domain: str
    path: str = "/"
    secure: bool = False
    httpOnly: bool = False
    expires: Optional[float] = None


class ScrapeRequest(BaseModel):
    """Request to scrape evidence from platforms"""
    platform: PlatformType
    cookies: List[SessionCookie] = Field(default_factory=list)
    start_month: int = Field(..., ge=1, le=12)
    end_month: int = Field(..., ge=1, le=12)
    start_year: int = Field(default=2025)
    end_year: int = Field(default=2025)
    include_filters: Optional[List[str]] = None
    exclude_filters: Optional[List[str]] = None


class ScrapeResponse(BaseModel):
    """Response with collected evidence"""
    platform: PlatformType
    total_items: int
    items: List[Evidence]
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebSocketMessage(BaseModel):
    """Real-time WebSocket message"""
    type: str  # "status", "evidence", "progress", "error"
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ComplianceScan(BaseModel):
    """Compliance scan configuration"""
    scan_id: str
    platforms: List[PlatformType]
    start_month: int
    end_month: int
    start_year: int
    end_year: int
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    evidence_count: int = 0
    errors: List[str] = Field(default_factory=list)


class CredentialPayload(BaseModel):
    """Payload for saving service credentials"""
    service: PlatformType
    credentials: Dict[str, str]  # username, password, etc.
    description: Optional[str] = None
'''

print("=== MODELS.PY ===")
print(models_py)
print("\n\n")

# 4. connectors/session_based.py
session_based_py = '''"""
Session-based connectors using browser cookies and saved credentials
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
import aiohttp
import asyncio
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


class SessionConnector(ABC):
    """Base class for session-based connectors"""
    
    def __init__(self, cookies: Dict[str, str] = None, timeout: int = 30):
        self.cookies = cookies or {}
        self.timeout = timeout
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _build_cookie_dict(self, cookies_list: List[Dict]) -> Dict:
        """Build cookie dictionary from list of cookie objects"""
        cookie_dict = {}
        for cookie in cookies_list:
            cookie_dict[cookie.get('name')] = cookie.get('value')
        return cookie_dict
    
    def _filter_by_date_range(self, items: List[Dict], start_date: datetime, 
                              end_date: datetime, date_field: str = 'created_date') -> List[Dict]:
        """Filter items by date range"""
        filtered = []
        for item in items:
            try:
                item_date = item.get(date_field)
                if isinstance(item_date, str):
                    item_date = datetime.fromisoformat(item_date.replace('Z', '+00:00'))
                
                if start_date <= item_date <= end_date:
                    filtered.append(item)
            except Exception as e:
                logger.warning(f"Error parsing date for item: {e}")
        return filtered
    
    @abstractmethod
    async def connect(self):
        """Establish connection"""
        pass
    
    @abstractmethod
    async def fetch_evidence(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch evidence items"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close connection"""
        pass


class OutlookConnector(SessionConnector):
    """Outlook connector using session cookies"""
    
    BASE_URL = "https://outlook.office365.com/api/v2.0"
    
    async def connect(self):
        """Connect using cookies"""
        logger.info("Connecting to Outlook via session cookies")
    
    async def fetch_evidence(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch emails from Outlook"""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        try:
            # Filter emails by date range
            filter_query = f"receivedDateTime ge {start_date.isoformat()} and receivedDateTime le {end_date.isoformat()}"
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Make authenticated request with cookies
            url = f"{self.BASE_URL}/me/mailFolders/inbox/messages"
            params = {
                '$filter': filter_query,
                '$top': 100,
                '$select': 'id,subject,receivedDateTime,sentDateTime,from,bodyPreview'
            }
            
            async with self.session.get(url, headers=headers, cookies=self.cookies, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    messages = data.get('value', [])
                    
                    evidence_items = []
                    for msg in messages:
                        evidence_items.append({
                            'id': msg.get('id'),
                            'platform': 'outlook',
                            'title': msg.get('subject', 'Untitled'),
                            'description': msg.get('bodyPreview'),
                            'created_date': msg.get('receivedDateTime'),
                            'url': f"https://outlook.office365.com/mail/inbox/{msg.get('id')}",
                            'metadata': {
                                'sender': msg.get('from', {}).get('emailAddress', {}).get('address', 'unknown'),
                                'categories': msg.get('categories', [])
                            }
                        })
                    
                    return evidence_items
                else:
                    logger.error(f"Outlook API error: {resp.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error fetching Outlook evidence: {e}")
            return []
    
    async def disconnect(self):
        """Close connection"""
        logger.info("Disconnecting from Outlook")


class OneDriveConnector(SessionConnector):
    """OneDrive/SharePoint connector using session cookies"""
    
    BASE_URL = "https://graph.microsoft.com/v1.0"
    
    async def connect(self):
        """Connect using cookies"""
        logger.info("Connecting to OneDrive via session cookies")
    
    async def fetch_evidence(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch files from OneDrive"""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Get recent files
            url = f"{self.BASE_URL}/me/drive/recent"
            
            async with self.session.get(url, headers=headers, cookies=self.cookies) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    files = data.get('value', [])
                    
                    evidence_items = []
                    for file in files:
                        created = file.get('createdDateTime', '')
                        modified = file.get('lastModifiedDateTime', '')
                        
                        try:
                            created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                            if start_date <= created_dt <= end_date:
                                evidence_items.append({
                                    'id': file.get('id'),
                                    'platform': 'onedrive',
                                    'title': file.get('name', 'Untitled'),
                                    'description': f"File in {file.get('parentReference', {}).get('path', '/')}",
                                    'created_date': created,
                                    'modified_date': modified,
                                    'url': file.get('webUrl'),
                                    'metadata': {
                                        'size': file.get('size'),
                                        'file_type': file.get('file', {}).get('mimeType', 'unknown')
                                    }
                                })
                        except:
                            pass
                    
                    return evidence_items
                else:
                    logger.error(f"OneDrive API error: {resp.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error fetching OneDrive evidence: {e}")
            return []
    
    async def disconnect(self):
        """Close connection"""
        logger.info("Disconnecting from OneDrive")


class GoogleDriveConnector(SessionConnector):
    """Google Drive connector using session cookies"""
    
    BASE_URL = "https://www.googleapis.com/drive/v3"
    
    async def connect(self):
        """Connect using cookies"""
        logger.info("Connecting to Google Drive via session cookies")
    
    async def fetch_evidence(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch files from Google Drive"""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Query files by creation date
            query = f"createdTime >= \\'{start_date.isoformat()}Z\\' and createdTime <= \\'{end_date.isoformat()}Z\\'"
            url = f"{self.BASE_URL}/files"
            params = {
                'q': query,
                'pageSize': 100,
                'fields': 'files(id,name,createdTime,modifiedTime,webViewLink,mimeType,size)'
            }
            
            async with self.session.get(url, headers=headers, cookies=self.cookies, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    files = data.get('files', [])
                    
                    evidence_items = []
                    for file in files:
                        evidence_items.append({
                            'id': file.get('id'),
                            'platform': 'google_drive',
                            'title': file.get('name', 'Untitled'),
                            'description': f"Type: {file.get('mimeType', 'unknown')}",
                            'created_date': file.get('createdTime'),
                            'modified_date': file.get('modifiedTime'),
                            'url': file.get('webViewLink'),
                            'metadata': {
                                'size': file.get('size'),
                                'mime_type': file.get('mimeType')
                            }
                        })
                    
                    return evidence_items
                else:
                    logger.error(f"Google Drive API error: {resp.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error fetching Google Drive evidence: {e}")
            return []
    
    async def disconnect(self):
        """Close connection"""
        logger.info("Disconnecting from Google Drive")


class NextcloudConnector(SessionConnector):
    """NWU Nextcloud connector using saved credentials"""
    
    def __init__(self, base_url: str, username: str, password: str, timeout: int = 30):
        super().__init__(timeout=timeout)
        self.base_url = base_url
        self.username = username
        self.password = password
    
    async def connect(self):
        """Connect to Nextcloud"""
        logger.info(f"Connecting to Nextcloud at {self.base_url}")
    
    async def fetch_evidence(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch files from Nextcloud"""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        try:
            # Basic auth header
            import base64
            auth_str = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth_str}',
                'Accept': 'application/json'
            }
            
            # Fetch recent files
            url = f"{self.base_url}/ocs/v2.php/apps/files/api/v1/files"
            params = {'format': 'json'}
            
            async with self.session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    files = data.get('ocs', {}).get('data', [])
                    
                    evidence_items = []
                    for file in files:
                        created = file.get('timestamp', '')
                        try:
                            created_dt = datetime.fromtimestamp(int(created) / 1000)
                            if start_date <= created_dt <= end_date:
                                evidence_items.append({
                                    'id': file.get('id'),
                                    'platform': 'nextcloud',
                                    'title': file.get('name', 'Untitled'),
                                    'created_date': created_dt.isoformat(),
                                    'url': f"{self.base_url}/f/{file.get('id')}",
                                    'metadata': {
                                        'size': file.get('size'),
                                        'owner': file.get('ownerDisplayName')
                                    }
                                })
                        except:
                            pass
                    
                    return evidence_items
                else:
                    logger.error(f"Nextcloud API error: {resp.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error fetching Nextcloud evidence: {e}")
            return []
    
    async def disconnect(self):
        """Close connection"""
        logger.info("Disconnecting from Nextcloud")


class EFundiConnector(SessionConnector):
    """eFundi (Sakai LMS) connector using Playwright"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        super().__init__(timeout=timeout)
        self.base_url = base_url
        self.browser = None
        self.context = None
    
    async def connect(self):
        """Connect using Playwright with existing browser session"""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            
            # Connect to existing Chrome instance
            logger.info("Connecting to eFundi via Playwright")
        except Exception as e:
            logger.error(f"Error initializing Playwright: {e}")
    
    async def fetch_evidence(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch activity from eFundi"""
        try:
            # This would use Playwright to navigate eFundi
            # For now, returning mock data structure
            logger.info(f"Fetching eFundi evidence from {start_date} to {end_date}")
            
            evidence_items = [
                {
                    'id': 'efundi-001',
                    'platform': 'efundi',
                    'title': 'Course Announcement',
                    'description': 'Important course update',
                    'created_date': start_date.isoformat(),
                    'url': f"{self.base_url}/portal",
                    'metadata': {'course': 'COMP101', 'type': 'announcement'}
                }
            ]
            
            return evidence_items
        
        except Exception as e:
            logger.error(f"Error fetching eFundi evidence: {e}")
            return []
    
    async def disconnect(self):
        """Close browser and context"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Disconnecting from eFundi")


class ConnectorFactory:
    """Factory for creating appropriate connectors"""
    
    @staticmethod
    async def create_connector(platform: str, cookies: List[Dict] = None, 
                               credentials: Dict = None, config_manager=None):
        """Create connector based on platform"""
        
        if platform == 'outlook':
            connector = OutlookConnector(cookies={c['name']: c['value'] for c in (cookies or [])})
        
        elif platform == 'onedrive':
            connector = OneDriveConnector(cookies={c['name']: c['value'] for c in (cookies or [])})
        
        elif platform == 'google_drive':
            connector = GoogleDriveConnector(cookies={c['name']: c['value'] for c in (cookies or [])})
        
        elif platform == 'nextcloud':
            creds = credentials or {}
            connector = NextcloudConnector(
                base_url=creds.get('base_url', 'https://nextcloud.nwu.ac.za'),
                username=creds.get('username', ''),
                password=creds.get('password', '')
            )
        
        elif platform == 'efundi':
            creds = credentials or {}
            connector = EFundiConnector(
                base_url=creds.get('base_url', 'https://efundi.nwu.ac.za')
            )
        
        else:
            raise ValueError(f"Unknown platform: {platform}")
        
        await connector.connect()
        return connector
'''

print("=== CONNECTORS/SESSION_BASED.PY ===")
print(session_based_py[:2000])
print("\n... [Full file is 300+ lines] ...\n")
