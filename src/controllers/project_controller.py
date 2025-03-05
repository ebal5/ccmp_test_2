from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import Project, Task, ProjectStatus, BufferStatus
from .base_controller import BaseController
from .task_controller import TaskController

class ProjectController(BaseController[Project, Dict[str, Any]]):
    def __init__(self):
        super().__init__(Project)
        self.task_controller = TaskController()
    
    def get_active_projects(self, db: Session) -> List[Project]:
        """Get all active projects"""
        return db.query(Project).filter(Project.status == ProjectStatus.ACTIVE).all()
    
    def calculate_project_buffer_consumption(self, db: Session, project_id: int) -> float:
        """Calculate the buffer consumption for a project"""
        project = self.get(db, project_id)
        if not project or not project.project_buffer:
            return 0.0
            
        # Get all critical chain tasks
        critical_tasks = self.task_controller.get_critical_chain_tasks(db, project_id)
        if not critical_tasks:
            return 0.0
            
        # Calculate total estimated time for critical chain
        total_estimated = sum(task.estimated_time for task in critical_tasks)
        
        # Calculate total actual time for completed tasks
        completed_tasks = [t for t in critical_tasks if t.status == ProjectStatus.COMPLETED]
        total_actual_completed = sum(task.actual_time or 0 for task in completed_tasks)
        
        # Calculate total estimated time for completed tasks
        total_estimated_completed = sum(task.estimated_time for task in completed_tasks)
        
        # Calculate buffer consumption
        if total_estimated_completed > 0:
            # Calculate completion percentage of critical chain
            chain_completion = total_estimated_completed / total_estimated
            
            # Calculate buffer consumption
            if total_actual_completed > total_estimated_completed:
                buffer_used = total_actual_completed - total_estimated_completed
                buffer_consumption = min(buffer_used / project.project_buffer * 100, 100.0)
                
                # Update project buffer consumption
                project.buffer_consumption = buffer_consumption
                
                # Update buffer status
                if buffer_consumption <= 33.0:
                    project.buffer_status = BufferStatus.GREEN
                elif buffer_consumption <= 66.0:
                    project.buffer_status = BufferStatus.YELLOW
                else:
                    project.buffer_status = BufferStatus.RED
                    
                db.add(project)
                db.commit()
                db.refresh(project)
                
                return buffer_consumption
                
        return project.buffer_consumption or 0.0
    
    def update_project_status(self, db: Session, project_id: int, status: ProjectStatus) -> Project:
        """Update the status of a project"""
        project = self.get(db, project_id)
        if project:
            project.status = status
            
            # If completing the project, set the actual end date
            if status == ProjectStatus.COMPLETED:
                project.actual_end_date = datetime.utcnow()
                
            db.add(project)
            db.commit()
            db.refresh(project)
            
        return project