from taipy.gui import Markdown, notify
from sqlalchemy.orm import Session

from ..models.base import get_db
from ..models import Task, Project, TimeEntry, TaskStatus, ProjectStatus, BufferStatus
from ..controllers import TaskController, ProjectController, TimeEntryController
from .layout import create_page_layout

# Initialize controllers
task_controller = TaskController()
project_controller = ProjectController()
time_entry_controller = TimeEntryController()

# Dashboard content
dashboard_content = """
# Dashboard

<|layout|columns=1 1 1|
<|card|
## Active Tasks
<|{active_tasks}|table|width=100%|selected={selected_task}|on_selection_change=on_task_selected|>
|>

<|card|
## Projects Status
<|{projects}|table|width=100%|selected={selected_project}|on_selection_change=on_project_selected|>
|>

<|card|
## Time Tracking
<|{time_entries}|table|width=100%|>
|>
|>

<|layout|columns=1 1|
<|card|
## Task Details
<|part|render={selected_task is not None}|
**Task:** <|{selected_task["name"] if selected_task else ""}|text|>

**Status:** <|{selected_task["status"] if selected_task else ""}|text|>

**Estimated Time:** <|{selected_task["estimated_time"] if selected_task else 0}|text|> hours

**Buffer:** <|{selected_task["buffer_time"] if selected_task else 0}|text|> hours

**Actual Time:** <|{selected_task["actual_time"] if selected_task else 0}|text|> hours

**Completion:** <|{selected_task["completion_percentage"] if selected_task else 0}|text|>%

<|layout|columns=1 1 1|
<|Start Task|button|on_action=on_start_task|active={selected_task is not None and selected_task["status"] != "in_progress"}|>
<|Complete Task|button|on_action=on_complete_task|active={selected_task is not None and selected_task["status"] == "in_progress"}|>
<|View Details|button|on_action=on_view_task_details|active={selected_task is not None}|>
|>
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

**Buffer Consumption:** <|{selected_project["buffer_consumption"] if selected_project else 0}|text|>%

<|View Details|button|on_action=on_view_project_details|active={selected_project is not None}|>
|>
<|part|render={selected_project is None}|
No project selected
|>
|>
|>

<|card|
## Active Timer
<|part|render={active_timer is not None}|
**Task:** <|{active_timer_task["name"] if active_timer_task else ""}|text|>

**Started:** <|{active_timer["start_time"] if active_timer else ""}|text|>

**Duration:** <|{active_timer_duration}|text|> minutes

<|Stop Timer|button|on_action=on_stop_timer|>
|>
<|part|render={active_timer is None}|
No active timer
|>
|>
"""

# Create the dashboard page
dashboard_page = create_page_layout(dashboard_content)

# Data for the dashboard
active_tasks = []
projects = []
time_entries = []
selected_task = None
selected_project = None
active_timer = None
active_timer_task = None
active_timer_duration = 0

def on_init(state):
    """Initialize the dashboard state"""
    update_dashboard_data(state)

def update_dashboard_data(state):
    """Update dashboard data from the database"""
    db = next(get_db())
    
    # Get active tasks
    active_tasks_db = db.query(Task).filter(
        Task.status.in_([TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS])
    ).order_by(Task.priority.desc()).limit(10).all()
    
    state.active_tasks = [{
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "priority": task.priority,
        "estimated_time": task.estimated_time,
        "buffer_time": task.buffer_time,
        "actual_time": task.actual_time,
        "completion_percentage": task.completion_percentage
    } for task in active_tasks_db]
    
    # Get projects
    projects_db = db.query(Project).order_by(Project.updated_at.desc()).limit(10).all()
    
    state.projects = [{
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "buffer_status": project.buffer_status,
        "buffer_consumption": project.buffer_consumption
    } for project in projects_db]
    
    # Get recent time entries
    time_entries_db = db.query(TimeEntry).order_by(TimeEntry.start_time.desc()).limit(10).all()
    
    state.time_entries = [{
        "id": entry.id,
        "task_id": entry.task_id,
        "category": entry.category,
        "start_time": entry.start_time.strftime("%Y-%m-%d %H:%M"),
        "end_time": entry.end_time.strftime("%Y-%m-%d %H:%M") if entry.end_time else "Active",
        "duration": f"{entry.duration:.2f} hours" if entry.duration else "In progress"
    } for entry in time_entries_db]
    
    # Get active timer
    active_timer_db = db.query(TimeEntry).filter(TimeEntry.end_time == None).first()
    
    if active_timer_db:
        state.active_timer = {
            "id": active_timer_db.id,
            "task_id": active_timer_db.task_id,
            "category": active_timer_db.category,
            "start_time": active_timer_db.start_time.strftime("%Y-%m-%d %H:%M")
        }
        
        # Get task for active timer
        if active_timer_db.task_id:
            task = db.query(Task).filter(Task.id == active_timer_db.task_id).first()
            if task:
                state.active_timer_task = {
                    "id": task.id,
                    "name": task.name
                }
                
        # Calculate duration
        import datetime
        duration_seconds = (datetime.datetime.utcnow() - active_timer_db.start_time).total_seconds()
        state.active_timer_duration = round(duration_seconds / 60, 1)
    else:
        state.active_timer = None
        state.active_timer_task = None
        state.active_timer_duration = 0

def on_task_selected(state, action, payload):
    """Handle task selection"""
    if payload and "index" in payload:
        index = payload["index"]
        if 0 <= index < len(state.active_tasks):
            state.selected_task = state.active_tasks[index]
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
        task = task_controller.start_task(db, state.selected_task["id"])
        
        # Start time tracking
        time_entry = time_entry_controller.start_timer(db, task_id=state.selected_task["id"])
        
        # Update dashboard data
        update_dashboard_data(state)
        
        # Show notification
        notify(state, "success", f"Task '{task.name}' started")

def on_complete_task(state):
    """Complete the selected task"""
    if state.selected_task:
        db = next(get_db())
        
        # Stop any active time entries for this task
        active_entries = db.query(TimeEntry).filter(
            TimeEntry.task_id == state.selected_task["id"],
            TimeEntry.end_time == None
        ).all()
        
        for entry in active_entries:
            time_entry_controller.stop_timer(db, entry.id)
        
        # Mark task as complete
        task = task_controller.complete_task(db, state.selected_task["id"])
        
        # Update dashboard data
        update_dashboard_data(state)
        
        # Show notification
        notify(state, "success", f"Task '{task.name}' completed")

def on_stop_timer(state):
    """Stop the active timer"""
    if state.active_timer:
        db = next(get_db())
        time_entry = time_entry_controller.stop_timer(db, state.active_timer["id"])
        
        # Update dashboard data
        update_dashboard_data(state)
        
        # Show notification
        notify(state, "success", "Timer stopped")

def on_view_task_details(state):
    """View task details"""
    if state.selected_task:
        from taipy.gui import navigate
        navigate(state, f"/tasks?task_id={state.selected_task['id']}")

def on_view_project_details(state):
    """View project details"""
    if state.selected_project:
        from taipy.gui import navigate
        navigate(state, f"/projects?project_id={state.selected_project['id']}")