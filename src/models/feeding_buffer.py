from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base
from .project import BufferStatus

class FeedingBuffer(Base):
    __tablename__ = "feeding_buffers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Buffer size and consumption
    buffer_size = Column(Float, nullable=False)  # Buffer size in hours
    buffer_consumption = Column(Float, default=0.0)  # Percentage of buffer consumed
    buffer_status = Column(String, default=BufferStatus.GREEN)
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    project = relationship("Project", back_populates="feeding_buffers")
    
    # Merge point task (where non-critical path joins critical path)
    merge_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)