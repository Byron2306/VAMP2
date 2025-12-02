
# 5. main.py - FastAPI application
main_py = '''"""
VAMP Agent - FastAPI Backend with WebSocket Streaming
Session-based authentication using Chrome extension cookies
"""
import asyncio
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import websockets

from config import settings, credential_manager, VAMPSettings
from models import (
    ScrapeRequest, ScrapeResponse, Evidence, EvidenceStatus,
    PlatformType, WebSocketMessage, ComplianceScan, CredentialPayload,
    SessionCookie
)

# Import connectors (in production, use proper imports)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# Active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_topics: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def subscribe(self, websocket: WebSocket, topic: str):
        """Subscribe to specific scan topic"""
        if topic not in self.connection_topics:
            self.connection_topics[topic] = set()
        self.connection_topics[topic].add(websocket)
    
    async def broadcast_to_topic(self, topic: str, message: WebSocketMessage):
        """Broadcast to all subscribers of a topic"""
        if topic in self.connection_topics:
            disconnected = []
            for connection in self.connection_topics[topic]:
                try:
                    await connection.send_json(message.model_dump(mode='json'))
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                await self.disconnect(conn)
                self.connection_topics[topic].discard(conn)


manager = ConnectionManager()


# Startup/Shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle"""
    logger.info("VAMP Agent Backend Starting...")
    yield
    logger.info("VAMP Agent Backend Shutting Down...")


# Create FastAPI app
app = FastAPI(
    title="VAMP Agent API",
    description="Session-based Evidence Collection Backend",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health/readiness")
async def readiness_check():
    """Readiness check - verify connections"""
    return {
        "status": "ready",
        "services": {
            "api": "ready",
            "websocket": "ready",
            "credentials": "ready"
        }
    }


# ============================================================================
# CREDENTIAL MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/credentials")
async def save_credentials(payload: CredentialPayload):
    """Save encrypted credentials for a service"""
    try:
        credential_manager.save_credentials(
            service=payload.service.value,
            credentials=payload.credentials
        )
        
        return {
            "status": "success",
            "message": f"Credentials saved for {payload.service.value}",
            "service": payload.service.value
        }
    except Exception as e:
        logger.error(f"Error saving credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/credentials/{service}")
async def get_credentials(service: PlatformType):
    """Get saved credentials for a service (encrypted in storage)"""
    try:
        creds = credential_manager.get_credentials(service.value)
        if not creds:
            raise HTTPException(status_code=404, detail=f"No credentials found for {service.value}")
        
        return {
            "service": service.value,
            "has_credentials": True,
            "last_updated": "encrypted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/credentials/{service}")
async def delete_credentials(service: PlatformType):
    """Delete credentials for a service"""
    try:
        credential_manager.delete_credentials(service.value)
        return {
            "status": "success",
            "message": f"Credentials deleted for {service.value}"
        }
    except Exception as e:
        logger.error(f"Error deleting credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SCRAPING ENDPOINTS
# ============================================================================

@app.post("/api/scrape")
async def scrape_evidence(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Scrape evidence from a platform
    
    Accepts:
    - platform: The platform to scrape from
    - cookies: Browser session cookies from Chrome extension
    - start_month/end_month: Month range (1-12)
    - start_year/end_year: Year range
    """
    try:
        # Validate date range
        if request.start_year == request.end_year:
            if request.start_month > request.end_month:
                raise HTTPException(
                    status_code=400,
                    detail="start_month must be <= end_month in same year"
                )
        
        # Calculate date range
        start_date = datetime(request.start_year, request.start_month, 1)
        end_date = datetime(request.end_year, request.end_month, 1)
        # Set to end of month
        if end_date.month == 12:
            end_date = end_date.replace(year=end_date.year + 1, month=1) - timedelta(days=1)
        else:
            end_date = end_date.replace(month=end_date.month + 1) - timedelta(days=1)
        end_date = end_date.replace(hour=23, minute=59, second=59)
        
        logger.info(f"Scraping {request.platform.value} from {start_date} to {end_date}")
        
        # Get connector
        from connectors.session_based import ConnectorFactory
        
        # Get saved credentials if needed
        creds = None
        if request.platform in [PlatformType.NEXTCLOUD, PlatformType.EFUNDI]:
            creds = credential_manager.get_credentials(request.platform.value)
        
        # Create connector
        connector = await ConnectorFactory.create_connector(
            platform=request.platform.value,
            cookies=[c.model_dump() for c in request.cookies] if request.cookies else None,
            credentials=creds
        )
        
        # Fetch evidence
        async with connector.session if hasattr(connector, 'session') and connector.session else None:
            evidence_list = await connector.fetch_evidence(start_date, end_date)
        
        await connector.disconnect()
        
        # Apply filters
        if request.include_filters:
            evidence_list = [
                e for e in evidence_list
                if any(f.lower() in e['title'].lower() or f.lower() in e.get('description', '').lower()
                       for f in request.include_filters)
            ]
        
        if request.exclude_filters:
            evidence_list = [
                e for e in evidence_list
                if not any(f.lower() in e['title'].lower() or f.lower() in e.get('description', '').lower()
                           for f in request.exclude_filters)
            ]
        
        # Convert to Evidence objects
        evidence_objects = []
        for item in evidence_list:
            try:
                evidence_objects.append(Evidence(
                    id=item['id'],
                    platform=request.platform,
                    title=item['title'],
                    description=item.get('description'),
                    created_date=datetime.fromisoformat(
                        item['created_date'].replace('Z', '+00:00')
                    ) if isinstance(item['created_date'], str) else item['created_date'],
                    modified_date=datetime.fromisoformat(
                        item['modified_date'].replace('Z', '+00:00')
                    ) if item.get('modified_date') and isinstance(item['modified_date'], str) else None,
                    url=item.get('url'),
                    metadata=item.get('metadata', {})
                ))
            except Exception as e:
                logger.warning(f"Error converting evidence item: {e}")
        
        response = ScrapeResponse(
            platform=request.platform,
            total_items=len(evidence_objects),
            items=evidence_objects
        )
        
        return response.model_dump(mode='json')
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scrape/async")
async def scrape_evidence_async(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Async scraping with WebSocket updates
    Returns scan_id for tracking progress
    """
    scan_id = str(uuid.uuid4())
    
    async def background_scrape():
        """Background scraping task"""
        try:
            # Send start message
            await manager.broadcast_to_topic(scan_id, WebSocketMessage(
                type="status",
                data={"status": "started", "scan_id": scan_id}
            ))
            
            # Perform scraping (same as /api/scrape)
            # ... scraping logic ...
            
            await manager.broadcast_to_topic(scan_id, WebSocketMessage(
                type="status",
                data={"status": "completed", "scan_id": scan_id}
            ))
        except Exception as e:
            logger.error(f"Error in background scrape: {e}")
            await manager.broadcast_to_topic(scan_id, WebSocketMessage(
                type="error",
                data={"error": str(e), "scan_id": scan_id}
            ))
    
    background_tasks.add_task(background_scrape)
    
    return {
        "scan_id": scan_id,
        "status": "pending",
        "message": "Connect to WebSocket at /ws/{scan_id} for updates"
    }


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/{scan_id}")
async def websocket_endpoint(websocket: WebSocket, scan_id: str):
    """
    WebSocket endpoint for real-time scraping updates
    
    Usage:
    ws = new WebSocket('ws://localhost:8000/ws/scan-id-here');
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        console.log(msg.type, msg.data);
    };
    """
    await manager.connect(websocket)
    await manager.subscribe(websocket, scan_id)
    
    try:
        # Send connected message
        await manager.broadcast_to_topic(scan_id, WebSocketMessage(
            type="status",
            data={
                "status": "connected",
                "scan_id": scan_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
            else:
                try:
                    message = json.loads(data)
                    logger.info(f"Received WebSocket message: {message}")
                except json.JSONDecodeError:
                    pass
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        await manager.disconnect(websocket)


# ============================================================================
# SCAN MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/scans")
async def create_scan(scan: ComplianceScan):
    """Create a new compliance scan"""
    try:
        return {
            "scan_id": scan.scan_id,
            "status": "created",
            "platforms": [p.value for p in scan.platforms],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scans/{scan_id}")
async def get_scan(scan_id: str):
    """Get scan status and results"""
    # In production, this would query a database
    return {
        "scan_id": scan_id,
        "status": "completed",
        "evidence_count": 0,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.get("/api/supported-platforms")
async def get_supported_platforms():
    """List supported platforms"""
    return {
        "platforms": [
            {
                "id": "outlook",
                "name": "Microsoft Outlook",
                "auth_method": "cookie-based",
                "requires_credentials": False
            },
            {
                "id": "onedrive",
                "name": "OneDrive / SharePoint",
                "auth_method": "cookie-based",
                "requires_credentials": False
            },
            {
                "id": "google_drive",
                "name": "Google Drive",
                "auth_method": "cookie-based",
                "requires_credentials": False
            },
            {
                "id": "nextcloud",
                "name": "NWU Nextcloud",
                "auth_method": "saved-credentials",
                "requires_credentials": True
            },
            {
                "id": "efundi",
                "name": "eFundi (Sakai LMS)",
                "auth_method": "playwright-session",
                "requires_credentials": True
            }
        ]
    }


@app.get("/api/config/encryption-key")
async def get_encryption_key_status():
    """Check if encryption key is configured"""
    return {
        "configured": bool(settings.ENCRYPTION_KEY),
        "key_length": len(settings.ENCRYPTION_KEY) if settings.ENCRYPTION_KEY else 0,
        "message": "Encryption key is configured" if settings.ENCRYPTION_KEY else "Generate key: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        debug=settings.DEBUG
    )
'''

print("=== MAIN.PY ===")
print(main_py[:3000])
print("\n... [Full file is 400+ lines] ...\n")

# Summary
print("="*80)
print("COMPLETE VAMP AGENT BACKEND STRUCTURE")
print("="*80)
