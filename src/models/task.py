from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from .base import Base

# Task dependency association table
task_dependencies = Table(
    'task_dependencies',
    Base.metadata,
    Column('dependent_task_id', Integer, ForeignKey('tasks.id'), primary_key=True),
    Column('dependency_task_id', Integer, ForeignKey('tasks.id'), primary_key=True)
)

class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Time estimates
    estimated_time = Column(Float, nullable=False)  # 50% probability estimate in hours
    buffer_time = Column(Float, nullable=False, default=0.0)  # Buffer time in hours
    actual_time = Column(Float, nullable=True)  # Actual time spent in hours
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    
    # Status and priority
    status = Column(String, default=TaskStatus.NOT_STARTED)
    priority = Column(String, default=TaskPriority.MEDIUM)
    
    # Project relationship
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    project = relationship("Project", back_populates="tasks")
    
    # Task dependencies
    dependencies = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin=(task_dependencies.c.dependent_task_id == id),
        secondaryjoin=(task_dependencies.c.dependency_task_id == id),
        backref="dependent_tasks"
    )
    
    # CCPM specific fields
    is_critical_chain = Column(Boolean, default=False)
    buffer_consumption = Column(Float, default=0.0)  # Percentage of buffer consumed
    completion_percentage = Column(Float, default=0.0)  # Percentage of task completed