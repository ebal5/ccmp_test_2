from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from .base import Base

class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"

class BufferStatus(str, Enum):
    GREEN = "green"  # 0-33% consumed
    YELLOW = "yellow"  # 34-66% consumed
    RED = "red"  # 67-100% consumed

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_date = Column(DateTime, nullable=True)
    target_end_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String, default=ProjectStatus.PLANNING)
    
    # CCPM specific fields
    project_buffer = Column(Float, default=0.0)  # Project buffer in hours
    buffer_consumption = Column(Float, default=0.0)  # Percentage of buffer consumed
    buffer_status = Column(String, default=BufferStatus.GREEN)
    
    # Relationships
    tasks = relationship("Task", back_populates="project")
    feeding_buffers = relationship("FeedingBuffer", back_populates="project")