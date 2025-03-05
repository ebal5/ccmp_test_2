from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from .base import Base

class NotificationType(str, Enum):
    TASK_STATUS_CHANGE = "task_status_change"
    BUFFER_ALERT = "buffer_alert"
    DEADLINE_ALERT = "deadline_alert"
    DEPENDENCY_RESOLVED = "dependency_resolved"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

class NotificationChannel(str, Enum):
    DISCORD = "discord"
    SLACK = "slack"
    TEAMS = "teams"
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Notification details
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    data = Column(JSON, nullable=True)  # Additional data in JSON format
    
    # Delivery information
    channel = Column(String, nullable=False)
    recipient = Column(String, nullable=False)  # Channel ID, webhook URL, etc.
    status = Column(String, default=NotificationStatus.PENDING)
    error_message = Column(String, nullable=True)
    
    # Related entities
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    # Retry information
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)