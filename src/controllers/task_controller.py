from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import Task, TaskStatus
from .base_controller import BaseController

class TaskController(BaseController[Task, Dict[str, Any]]):
    def __init__(self):
        super().__init__(Task)
    
    def get_by_project(self, db: Session, project_id: int) -> List[Task]:
        """Get all tasks for a specific project"""
        return db.query(Task).filter(Task.project_id == project_id).all()
    
    def get_by_status(self, db: Session, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status"""
        return db.query(Task).filter(Task.status == status).all()
    
    def get_critical_chain_tasks(self, db: Session, project_id: int) -> List[Task]:
        """Get all tasks in the critical chain for a project"""
        return db.query(Task).filter(
            Task.project_id == project_id,
            Task.is_critical_chain == True
        ).all()
    
    def start_task(self, db: Session, task_id: int) -> Task:
        """Mark a task as started and record the start time"""
        task = self.get(db, task_id)
        if task and task.status != TaskStatus.IN_PROGRESS:
            task.status = TaskStatus.IN_PROGRESS
            task.start_date = datetime.utcnow()
            db.add(task)
            db.commit()
            db.refresh(task)
        return task
    
    def complete_task(self, db: Session, task_id: int) -> Task:
        """Mark a task as completed and record the end time"""
        task = self.get(db, task_id)
        if task and task.status != TaskStatus.COMPLETED:
            task.status = TaskStatus.COMPLETED
            task.end_date = datetime.utcnow()
            task.completion_percentage = 100.0
            db.add(task)
            db.commit()
            db.refresh(task)
        return task
    
    def update_progress(self, db: Session, task_id: int, completion_percentage: float) -> Task:
        """Update the completion percentage of a task"""
        task = self.get(db, task_id)
        if task:
            task.completion_percentage = min(max(completion_percentage, 0.0), 100.0)
            db.add(task)
            db.commit()
            db.refresh(task)
        return task
    
    def calculate_buffer_consumption(self, db: Session, task_id: int) -> float:
        """Calculate the buffer consumption for a task"""
        task = self.get(db, task_id)
        if not task or not task.estimated_time or not task.buffer_time:
            return 0.0
            
        # If task is completed, use actual time
        if task.status == TaskStatus.COMPLETED and task.actual_time:
            # If actual time exceeds estimated time, calculate buffer consumption
            if task.actual_time > task.estimated_time:
                buffer_used = task.actual_time - task.estimated_time
                buffer_consumption = min(buffer_used / task.buffer_time * 100, 100.0)
                task.buffer_consumption = buffer_consumption
                db.add(task)
                db.commit()
                db.refresh(task)
                return buffer_consumption
            return 0.0  # No buffer consumed if completed under estimated time
            
        # For in-progress tasks, estimate buffer consumption based on completion percentage
        if task.status == TaskStatus.IN_PROGRESS and task.completion_percentage > 0:
            # Estimate total time based on current progress
            if task.completion_percentage < 100:
                estimated_total_time = (task.actual_time or 0) / (task.completion_percentage / 100)
                if estimated_total_time > task.estimated_time:
                    projected_buffer_used = estimated_total_time - task.estimated_time
                    buffer_consumption = min(projected_buffer_used / task.buffer_time * 100, 100.0)
                    task.buffer_consumption = buffer_consumption
                    db.add(task)
                    db.commit()
                    db.refresh(task)
                    return buffer_consumption
                    
        return task.buffer_consumption or 0.0