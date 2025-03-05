from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models import TimeEntry, Task
from .base_controller import BaseController
from .task_controller import TaskController

class TimeEntryController(BaseController[TimeEntry, Dict[str, Any]]):
    def __init__(self):
        super().__init__(TimeEntry)
        self.task_controller = TaskController()
    
    def get_by_task(self, db: Session, task_id: int) -> List[TimeEntry]:
        """Get all time entries for a specific task"""
        return db.query(TimeEntry).filter(TimeEntry.task_id == task_id).all()
    
    def get_by_date_range(self, db: Session, start_date: datetime, end_date: datetime) -> List[TimeEntry]:
        """Get all time entries within a date range"""
        return db.query(TimeEntry).filter(
            TimeEntry.start_time >= start_date,
            TimeEntry.start_time <= end_date
        ).all()
    
    def get_by_category(self, db: Session, category: str) -> List[TimeEntry]:
        """Get all time entries for a specific category"""
        return db.query(TimeEntry).filter(TimeEntry.category == category).all()
    
    def start_timer(self, db: Session, task_id: Optional[int] = None, category: Optional[str] = None) -> TimeEntry:
        """Start a new time entry"""
        # Check if there's an active timer
        active_timer = self._get_active_timer(db)
        if active_timer:
            # Stop the active timer first
            self.stop_timer(db, active_timer.id)
        
        # Create a new time entry
        time_entry = TimeEntry(
            task_id=task_id,
            category=category,
            start_time=datetime.utcnow()
        )
        
        db.add(time_entry)
        db.commit()
        db.refresh(time_entry)
        
        # If this is for a task, mark the task as in progress
        if task_id:
            self.task_controller.start_task(db, task_id)
            
        return time_entry
    
    def stop_timer(self, db: Session, time_entry_id: int) -> TimeEntry:
        """Stop an active time entry"""
        time_entry = self.get(db, time_entry_id)
        if time_entry and not time_entry.end_time:
            time_entry.end_time = datetime.utcnow()
            
            # Calculate duration in hours
            duration = (time_entry.end_time - time_entry.start_time).total_seconds() / 3600
            time_entry.duration = duration
            
            db.add(time_entry)
            db.commit()
            db.refresh(time_entry)
            
            # Update task actual time if this is a task time entry
            if time_entry.task_id:
                self._update_task_actual_time(db, time_entry.task_id)
                
        return time_entry
    
    def _get_active_timer(self, db: Session) -> Optional[TimeEntry]:
        """Get the currently active time entry, if any"""
        return db.query(TimeEntry).filter(TimeEntry.end_time == None).first()
    
    def _update_task_actual_time(self, db: Session, task_id: int) -> None:
        """Update the actual time for a task based on its time entries"""
        task = self.task_controller.get(db, task_id)
        if task:
            # Get all time entries for this task
            time_entries = self.get_by_task(db, task_id)
            
            # Calculate total duration
            total_duration = sum(entry.duration or 0 for entry in time_entries if entry.duration)
            
            # Update task actual time
            task.actual_time = total_duration
            db.add(task)
            db.commit()
            
            # Recalculate buffer consumption
            self.task_controller.calculate_buffer_consumption(db, task_id)