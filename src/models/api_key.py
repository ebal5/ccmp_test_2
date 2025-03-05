from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import secrets

from .base import Base

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # API key details
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    key = Column(String, nullable=False, index=True, unique=True)
    
    # Permissions
    permissions = Column(JSON, nullable=True)  # JSON array of allowed operations
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    @staticmethod
    def generate_key():
        return secrets.token_urlsafe(32)