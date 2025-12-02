
# Let's create the complete project structure with all files

# 1. requirements.txt
requirements_content = """fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
pydantic==2.5.0
pydantic-settings==2.1.0
aiohttp==3.9.1
cryptography==41.0.7
python-dotenv==1.0.0
playwright==1.40.0
requests==2.31.0
pytz==2023.3
aiofiles==23.2.1
"""

print("=== REQUIREMENTS.TXT ===")
print(requirements_content)
print("\n")

# 2. config.py - Encrypted credential storage
config_py = '''"""
VAMP Agent Configuration with Encrypted Credential Storage
"""
import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings
from pydantic import Field


class VAMPSettings(BaseSettings):
    """Configuration with encrypted credentials"""
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # Encryption key (generate with: Fernet.generate_key())
    ENCRYPTION_KEY: str = Field(default_factory=lambda: os.getenv(
        "VAMP_ENCRYPTION_KEY", 
        Fernet.generate_key().decode()
    ))
    
    # Session config
    SESSION_TIMEOUT: int = 3600  # 1 hour
    CORS_ORIGINS: list = ["chrome-extension://*", "http://localhost:3000"]
    
    # Connector timeouts
    CONNECTOR_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    
    # WebSocket settings
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # Credentials storage path
    CREDENTIALS_FILE: Path = Path("config/.vamp_credentials.enc")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = VAMPSettings()


class CredentialManager:
    """Manages encrypted credential storage"""
    
    def __init__(self, encryption_key: str = None):
        self.key = encryption_key or settings.ENCRYPTION_KEY
        self.cipher = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
        self.credentials_file = settings.CREDENTIALS_FILE
        self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
    
    def encrypt_credentials(self, credentials: dict) -> str:
        """Encrypt credentials dictionary"""
        json_str = json.dumps(credentials)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode()
    
    def decrypt_credentials(self) -> dict:
        """Decrypt stored credentials"""
        if not self.credentials_file.exists():
            return {}
        
        try:
            with open(self.credentials_file, 'r') as f:
                encrypted_data = f.read()
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            print(f"Error decrypting credentials: {e}")
            return {}
    
    def save_credentials(self, service: str, credentials: dict):
        """Save encrypted credentials for a service"""
        all_creds = self.decrypt_credentials()
        all_creds[service] = credentials
        encrypted = self.encrypt_credentials(all_creds)
        
        with open(self.credentials_file, 'w') as f:
            f.write(encrypted)
    
    def get_credentials(self, service: str) -> dict:
        """Get credentials for a specific service"""
        creds = self.decrypt_credentials()
        return creds.get(service, {})
    
    def delete_credentials(self, service: str):
        """Delete credentials for a service"""
        all_creds = self.decrypt_credentials()
        if service in all_creds:
            del all_creds[service]
        encrypted = self.encrypt_credentials(all_creds)
        
        with open(self.credentials_file, 'w') as f:
            f.write(encrypted)


credential_manager = CredentialManager()
'''

print("=== CONFIG.PY ===")
print(config_py)
print("\n")
