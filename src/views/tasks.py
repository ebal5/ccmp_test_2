from taipy.gui import Markdown, notify
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.base import get_db
from ..models import Task, Project, TimeEntry, TaskStatus, TaskPriority
from ..controllers import TaskController, ProjectController, TimeEntryController
from .layout import create_page_layout

# Initialize controllers
task_controller = TaskController()
project_controller = ProjectController()
time_entry_controller = TimeEntryController()

# Tasks content
tasks_content = """
# Tasks

<|tabs|
<|tab|label=Task List|
<|layout|columns=3 1|
<|{tasks}|table|width=100%|selected={selected_task}|on_selection_change=on_task_selected|>

<|card|
<|New Task|button|on_action=on_new_task|>

<|part|render={selected_task is not None}|
## Selected Task

**Task:** <|{selected_task["name"] if selected_task else ""}|text|>

**Status:** <|{selected_task["status"] if selected_task else ""}|text|>

<|Edit Task|button|on_action=on_edit_task|>
<|Delete Task|button|on_action=on_delete_task|>
|>
<|card|>
|>
|>

<|tab|label=Task Details|active={task_id is not None}|
<|part|render={current_task is not None}|
# Task: <|{current_task["name"]}|text|>

<|layout|columns=1 1|
<|card|
## Basic Information

**ID:** <|{current_task["id"]}|text|>

**Description:** <|{current_task["description"]}|text|>

**Status:** <|{current_task["status"]}|text|>

**Priority:** <|{current_task["priority"]}|text|>

**Project:** <|{current_task["project_name"]}|text|>

**Is Critical Chain:** <|{current_task["is_critical_chain"]}|text|>
<|card|>

<|card|
## Time Information

**Estimated Time:** <|{current_task["estimated_time"]}|text|> hours

**Buffer Time:** <|{current_task["buffer_time"]}|text|> hours

**Actual Time:** <|{current_task["actual_time"]}|text|> hours

**Completion:** <|{current_task["completion_percentage"]}|text|>%

**Buffer Consumption:** <|{current_task["buffer_consumption"]}|text|>%

**Start Date:** <|{current_task["start_date"]}|text|>

**End Date:** <|{current_task["end_date"]}|text|>

**Due Date:** <|{current_task["due_date"]}|text|>
<|card|>
|>

<|layout|columns=1 1 1|
<|Start Task|button|on_action=on_start_current_task|active={current_task["status"] != "in_progress" and current_task["status"] != "completed"}|>
<|Complete Task|button|on_action=on_complete_current_task|active={current_task["status"] == "in_progress"}|>
<|Back to List|button|on_action=on_back_to_list|>
|>

## Time Entries
<|{task_time_entries}|table|width=100%|>
|>

<|part|render={current_task is None}|
No task selected. <|Back to List|button|on_action=on_back_to_list|>
|>
|>

<|tab|label=New/Edit Task|active={is_editing}|
<|card|
# <|{editing_mode}|text|> Task

<|layout|columns=1 1|
<|
**Name:** <|{edit_task["name"]}|input|>

**Description:** <|{edit_task["description"]}|input|multiline=true|>

**Status:**
<|{edit_task["status"]}|selector|lov={task_statuses}|>

**Priority:**
<|{edit_task["priority"]}|selector|lov={task_priorities}|>

**Project:**
<|{edit_task["project_id"]}|selector|lov={project_options}|>
|>

<|
**Estimated Time (hours):** <|{edit_task["estimated_time"]}|number|>

**Buffer Time (hours):** <|{edit_task["buffer_time"]}|number|>

**Due Date:** <|{edit_task["due_date"]}|date|>

**Is Critical Chain:** <|{edit_task["is_critical_chain"]}|toggle|>

**Dependencies:**
<|{edit_task["dependencies"]}|selector|lov={task_options}|multiple=true|>
|>
|>

<|layout|columns=1 1 1|
<|Save|button|on_action=on_save_task|>
<|Cancel|button|on_action=on_cancel_edit|>
|>
<|card|>
|>
|>
"""

# Create the tasks page
tasks_page = create_page_layout(tasks_content)

# Data for the tasks page
tasks = []
selected_task = None
current_task = None
task_time_entries = []
task_id = None
is_editing = False
editing_mode = "New"
edit_task = {
    "id": None,
    "name": "",
    "description": "",
    "status": TaskStatus.NOT_STARTED,
    "priority": TaskPriority.MEDIUM,
    "project_id": None,
    "estimated_time": 1.0,
    "buffer_time": 0.5,
    "due_date": None,
    "is_critical_chain": False,
    "dependencies": []
}
task_statuses = [status.value for status in TaskStatus]
task_priorities = [priority.value for priority in TaskPriority]
project_options = []
task_options = []

def on_init(state):
    """Initialize the tasks state"""
    # Check if task_id is provided in URL
    if hasattr(state, "client_id"):
        from taipy.gui import get_state_id
        state_id = get_state_id(state)
        if state_id and "task_id" in state_id:
            state.task_id = state_id["task_id"]
    
    update_tasks_data(state)
    update_dropdown_options(state)
    
    # Load task details if task_id is provided
    if state.task_id:
        load_task_details(state, state.task_id)

def update_tasks_data(state):
    """Update tasks data from the database"""
    db = next(get_db())
    
    # Get all tasks
    tasks_db = db.query(Task).order_by(Task.updated_at.desc()).all()
    
    state.tasks = [{
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "priority": task.priority,
        "estimated_time": task.estimated_time,
        "buffer_time": task.buffer_time,
        "actual_time": task.actual_time,
        "completion_percentage": task.completion_percentage,
        "project_id": task.project_id,
        "project_name": task.project.name if task.project else "None",
        "is_critical_chain": task.is_critical_chain
    } for task in tasks_db]

def update_dropdown_options(state):
    """Update dropdown options for projects and tasks"""
    db = next(get_db())
    
    # Get projects for dropdown
    projects_db = db.query(Project).all()
    state.project_options = [{"id": None, "label": "None"}] + [
        {"id": project.id, "label": project.name}
        for project in projects_db
    ]
    
    # Get tasks for dependencies dropdown
    tasks_db = db.query(Task).all()
    state.task_options = [
        {"id": task.id, "label": task.name}
        for task in tasks_db
    ]

def load_task_details(state, task_id):
    """Load task details"""
    db = next(get_db())
    task = task_controller.get(db, task_id)
    
    if task:
        # Get project name
        project_name = task.project.name if task.project else "None"
        
        # Format dates
        start_date = task.start_date.strftime("%Y-%m-%d %H:%M") if task.start_date else "Not started"
        end_date = task.end_date.strftime("%Y-%m-%d %H:%M") if task.end_date else "Not completed"
        due_date = task.due_date.strftime("%Y-%m-%d") if task.due_date else "No due date"
        
        # Get time entries
        time_entries = time_entry_controller.get_by_task(db, task_id)
        state.task_time_entries = [{
            "id": entry.id,
            "start_time": entry.start_time.strftime("%Y-%m-%d %H:%M"),
            "end_time": entry.end_time.strftime("%Y-%m-%d %H:%M") if entry.end_time else "Active",
            "duration": f"{entry.duration:.2f} hours" if entry.duration else "In progress"
        } for entry in time_entries]
        
        # Set current task
        state.current_task = {
            "id": task.id,
            "name": task.name,
            "description": task.description or "",
            "status": task.status,
            "priority": task.priority,
            "project_id": task.project_id,
            "project_name": project_name,
            "estimated_time": task.estimated_time,
            "buffer_time": task.buffer_time,
            "actual_time": task.actual_time or 0,
            "completion_percentage": task.completion_percentage,
            "buffer_consumption": task.buffer_consumption,
            "is_critical_chain": task.is_critical_chain,
            "start_date": start_date,
            "end_date": end_date,
            "due_date": due_date,
            "dependencies": [dep.id for dep in task.dependencies]
        }
    else:
        state.current_task = None
        state.task_time_entries = []

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

def on_new_task(state):
    """Create a new task"""
    state.edit_task = {
        "id": None,
        "name": "",
        "description": "",
        "status": TaskStatus.NOT_STARTED,
        "priority": TaskPriority.MEDIUM,
        "project_id": None,
        "estimated_time": 1.0,
        "buffer_time": 0.5,
        "due_date": None,
        "is_critical_chain": False,
        "dependencies": []
    }
    state.editing_mode = "New"
    state.is_editing = True

def on_edit_task(state):
    """Edit the selected task"""
    if state.selected_task:
        db = next(get_db())
        task = task_controller.get(db, state.selected_task["id"])
        
        if task:
            # Convert due date to string for the date picker
            due_date = task.due_date.strftime("%Y-%m-%d") if task.due_date else None
            
            state.edit_task = {
                "id": task.id,
                "name": task.name,
                "description": task.description or "",
                "status": task.status,
                "priority": task.priority,
                "project_id": task.project_id,
                "estimated_time": task.estimated_time,
                "buffer_time": task.buffer_time,
                "due_date": due_date,
                "is_critical_chain": task.is_critical_chain,
                "dependencies": [dep.id for dep in task.dependencies]
            }
            state.editing_mode = "Edit"
            state.is_editing = True

def on_delete_task(state):
    """Delete the selected task"""
    if state.selected_task:
        db = next(get_db())
        task = task_controller.delete(db, state.selected_task["id"])
        
        # Update tasks data
        update_tasks_data(state)
        state.selected_task = None
        
        # Show notification
        notify(state, "success", f"Task '{task.name}' deleted")

def on_save_task(state):
    """Save the task"""
    db = next(get_db())
    
    # Convert due date
    due_date = None
    if state.edit_task["due_date"]:
        if isinstance(state.edit_task["due_date"], str):
            due_date = datetime.strptime(state.edit_task["due_date"], "%Y-%m-%d")
        else:
            due_date = state.edit_task["due_date"]
    
    # Prepare task data
    task_data = {
        "name": state.edit_task["name"],
        "description": state.edit_task["description"],
        "status": state.edit_task["status"],
        "priority": state.edit_task["priority"],
        "project_id": state.edit_task["project_id"],
        "estimated_time": state.edit_task["estimated_time"],
        "buffer_time": state.edit_task["buffer_time"],
        "due_date": due_date,
        "is_critical_chain": state.edit_task["is_critical_chain"]
    }
    
    if state.edit_task["id"]:
        # Update existing task
        task = task_controller.get(db, state.edit_task["id"])
        task = task_controller.update(db, task, task_data)
        
        # Update dependencies
        task.dependencies = []
        for dep_id in state.edit_task["dependencies"]:
            dep_task = task_controller.get(db, dep_id)
            if dep_task:
                task.dependencies.append(dep_task)
        
        db.add(task)
        db.commit()
        
        # Show notification
        notify(state, "success", f"Task '{task.name}' updated")
    else:
        # Create new task
        task = task_controller.create(db, task_data)
        
        # Add dependencies
        for dep_id in state.edit_task["dependencies"]:
            dep_task = task_controller.get(db, dep_id)
            if dep_task:
                task.dependencies.append(dep_task)
        
        db.add(task)
        db.commit()
        
        # Show notification
        notify(state, "success", f"Task '{task.name}' created")
    
    # Update tasks data
    update_tasks_data(state)
    update_dropdown_options(state)
    state.is_editing = False
    
    # If this was a new task, select it
    if not state.edit_task["id"]:
        for i, t in enumerate(state.tasks):
            if t["id"] == task.id:
                state.selected_task = state.tasks[i]
                break

def on_cancel_edit(state):
    """Cancel task editing"""
    state.is_editing = False

def on_start_current_task(state):
    """Start the current task"""
    if state.current_task:
        db = next(get_db())
        task = task_controller.start_task(db, state.current_task["id"])
        
        # Start time tracking
        time_entry = time_entry_controller.start_timer(db, task_id=state.current_task["id"])
        
        # Reload task details
        load_task_details(state, state.current_task["id"])
        
        # Update tasks data
        update_tasks_data(state)
        
        # Show notification
        notify(state, "success", f"Task '{task.name}' started")

def on_complete_current_task(state):
    """Complete the current task"""
    if state.current_task:
        db = next(get_db())
        
        # Stop any active time entries for this task
        active_entries = db.query(TimeEntry).filter(
            TimeEntry.task_id == state.current_task["id"],
            TimeEntry.end_time == None
        ).all()
        
        for entry in active_entries:
            time_entry_controller.stop_timer(db, entry.id)
        
        # Mark task as complete
        task = task_controller.complete_task(db, state.current_task["id"])
        
        # Reload task details
        load_task_details(state, state.current_task["id"])
        
        # Update tasks data
        update_tasks_data(state)
        
        # Show notification
        notify(state, "success", f"Task '{task.name}' completed")

def on_back_to_list(state):
    """Go back to task list"""
    state.task_id = None
    state.current_task = None
    from taipy.gui import navigate
    navigate(state, "/tasks")