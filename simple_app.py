import os
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
<|{tasks}|table|width=100%|selected={selected_task}|on_selection_change=on_task_selected|>

## Projects
<|{projects}|table|width=100%|selected={selected_project}|on_selection_change=on_project_selected|>

<|layout|columns=1 1|
<|card|
## Task Details
<|part|render={selected_task is not None}|
**Task:** <|{selected_task["name"] if selected_task else ""}|text|>

**Status:** <|{selected_task["status"] if selected_task else ""}|text|>

**Estimated Time:** <|{selected_task["estimated_time"] if selected_task else 0}|text|> hours

<|Start Task|button|on_action=on_start_task|active={selected_task is not None and selected_task["status"] != "in_progress"}|>
<|Complete Task|button|on_action=on_complete_task|active={selected_task is not None and selected_task["status"] == "in_progress"}|>
|>
<|part|render={selected_task is None}|
No task selected
|>
|>

<|card|
## Project Details
<|part|render={selected_project is not None}|
**Project:** <|{selected_project["name"] if selected_project else ""}|text|>

**Status:** <|{selected_project["status"] if selected_project else ""}|text|>

**Buffer Status:** <|{selected_project["buffer_status"] if selected_project else ""}|text|>
|>
<|part|render={selected_project is None}|
No project selected
|>
|>
|>

<|Refresh Data|button|on_action=on_refresh|>
"""

# Initialize state variables
tasks = []
projects = []
selected_task = None
selected_project = None

def update_data(state):
    """Update data from the database"""
    db = next(get_db())
    
    # Get tasks
    tasks_db = db.query(Task).all()
    state.tasks = [{
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
    state.projects = [{
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "buffer_status": project.buffer_status,
        "buffer_consumption": project.buffer_consumption
    } for project in projects_db]

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
        if 0 <= index < len(state.tasks):
            state.selected_task = state.tasks[index]
        else:
            state.selected_task = None
    else:
        state.selected_task = None

def on_project_selected(state, action, payload):
    """Handle project selection"""
    if payload and "index" in payload:
        index = payload["index"]
        if 0 <= index < len(state.projects):
            state.selected_project = state.projects[index]
        else:
            state.selected_project = None
    else:
        state.selected_project = None

def on_start_task(state):
    """Start the selected task"""
    if state.selected_task:
        db = next(get_db())
        task = db.query(Task).filter(Task.id == state.selected_task["id"]).first()
        
        if task:
            task.status = TaskStatus.IN_PROGRESS
            task.start_date = datetime.utcnow()
            db.add(task)
            db.commit()
            
            # Update data
            update_data(state)
            
            # Update selected task
            for i, t in enumerate(state.tasks):
                if t["id"] == state.selected_task["id"]:
                    state.selected_task = state.tasks[i]
                    break
            
            # Show notification
            notify(state, "success", f"Task '{task.name}' started")

def on_complete_task(state):
    """Complete the selected task"""
    if state.selected_task:
        db = next(get_db())
        task = db.query(Task).filter(Task.id == state.selected_task["id"]).first()
        
        if task:
            task.status = TaskStatus.COMPLETED
            task.end_date = datetime.utcnow()
            task.completion_percentage = 100.0
            db.add(task)
            db.commit()
            
            # Update data
            update_data(state)
            
            # Update selected task
            for i, t in enumerate(state.tasks):
                if t["id"] == state.selected_task["id"]:
                    state.selected_task = state.tasks[i]
                    break
            
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