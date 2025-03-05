from sqlalchemy import Column, Integer, String, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base
from .notification import NotificationType, NotificationChannel

class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template details
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Template content
    notification_type = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    title_template = Column(String, nullable=False)
    message_template = Column(String, nullable=False)
    
    # Rich formatting options (for platforms that support it)
    rich_format = Column(JSON, nullable=True)  # JSON structure for rich formatting
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)