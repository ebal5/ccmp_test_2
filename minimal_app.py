import os
import pandas as pd
from taipy.gui import Gui, notify
from sqlalchemy.orm import Session
from datetime import datetime

# Import database initialization
from src.database import init_db
from src.models.base import get_db
from src.models import Task, Project, TimeEntry, TaskStatus, ProjectStatus

# Initialize the database
init_db()

# Dashboard page
dashboard_page = """
# CCPM Task Manager

## Tasks
<|{tasks_df}|table|width=100%|selected={selected_task_index}|on_selection_change=on_task_selected|>

<|part|render={selected_task_index is not None}|
### Task Actions
<|Start Task|button|on_action=on_start_task|active={selected_task_status != "in_progress" and selected_task_status != "completed"}|>
<|Complete Task|button|on_action=on_complete_task|active={selected_task_status == "in_progress"}|>
|>

## Projects
<|{projects_df}|table|width=100%|>

<|Refresh Data|button|on_action=on_refresh|>
"""

# Initialize state variables
tasks_df = pd.DataFrame()
projects_df = pd.DataFrame()
selected_task_index = None
selected_task_id = None
selected_task_status = None

def update_data(state):
    """Update data from the database"""
    db = next(get_db())
    
    # Get tasks
    tasks_db = db.query(Task).all()
    tasks_data = [{
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "estimated_time": task.estimated_time,
        "buffer_time": task.buffer_time,
        "actual_time": task.actual_time or 0,
        "completion_percentage": task.completion_percentage
    } for task in tasks_db]
    
    # Get projects
    projects_db = db.query(Project).all()
    projects_data = [{
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "buffer_status": project.buffer_status,
        "buffer_consumption": project.buffer_consumption
    } for project in projects_db]
    
    # Convert to pandas DataFrames
    state.tasks_df = pd.DataFrame(tasks_data)
    state.projects_df = pd.DataFrame(projects_data)

def on_init(state):
    """Initialize the state"""
    # Create some sample data if none exists
    db = next(get_db())
    
    # Check if we have any projects
    if db.query(Project).count() == 0:
        # Create a sample project
        project = Project(
            name="Sample Project",
            description="A sample project for testing",
            status=ProjectStatus.ACTIVE,
            project_buffer=10.0
        )
        db.add(project)
        db.commit()
        
        # Create some sample tasks
        tasks = [
            Task(
                name="Task 1",
                description="Sample task 1",
                status=TaskStatus.NOT_STARTED,
                estimated_time=5.0,
                buffer_time=2.0,
                project_id=project.id
            ),
            Task(
                name="Task 2",
                description="Sample task 2",
                status=TaskStatus.NOT_STARTED,
                estimated_time=3.0,
                buffer_time=1.0,
                project_id=project.id
            )
        ]
        
        for task in tasks:
            db.add(task)
        
        db.commit()
    
    # Update data
    update_data(state)

def on_task_selected(state, action, payload):
    """Handle task selection"""
    if payload and "index" in payload:
        index = payload["index"]
        if 0 <= index < len(state.tasks_df):
            state.selected_task_index = index
            state.selected_task_id = state.tasks_df.iloc[index]["id"]
            state.selected_task_status = state.tasks_df.iloc[index]["status"]
        else:
            state.selected_task_index = None
            state.selected_task_id = None
            state.selected_task_status = None
    else:
        state.selected_task_index = None
        state.selected_task_id = None
        state.selected_task_status = None

def on_start_task(state):
    """Start the selected task"""
    if state.selected_task_id is not None:
        db = next(get_db())
        task = db.query(Task).filter(Task.id == state.selected_task_id).first()
        
        if task:
            task.status = TaskStatus.IN_PROGRESS
            task.start_date = datetime.utcnow()
            db.add(task)
            db.commit()
            
            # Update data
            update_data(state)
            
            # Update selected task status
            if state.selected_task_index is not None and state.selected_task_index < len(state.tasks_df):
                state.selected_task_status = state.tasks_df.iloc[state.selected_task_index]["status"]
            
            # Show notification
            notify(state, "success", f"Task '{task.name}' started")

def on_complete_task(state):
    """Complete the selected task"""
    if state.selected_task_id is not None:
        db = next(get_db())
        task = db.query(Task).filter(Task.id == state.selected_task_id).first()
        
        if task:
            task.status = TaskStatus.COMPLETED
            task.end_date = datetime.utcnow()
            task.completion_percentage = 100.0
            db.add(task)
            db.commit()
            
            # Update data
            update_data(state)
            
            # Update selected task status
            if state.selected_task_index is not None and state.selected_task_index < len(state.tasks_df):
                state.selected_task_status = state.tasks_df.iloc[state.selected_task_index]["status"]
            
            # Show notification
            notify(state, "success", f"Task '{task.name}' completed")

def on_refresh(state):
    """Refresh data"""
    update_data(state)
    notify(state, "info", "Data refreshed")

# Create the GUI
gui = Gui(pages={"/": dashboard_page})

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 50725))
    
    # Run the GUI
    gui.run(title="CCPM Task Manager", 
            dark_mode=True,
            host="0.0.0.0", 
            port=port,
            debug=True,
            allow_iframe=True,
            cors_policy="*")