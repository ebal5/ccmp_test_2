from taipy.gui import Markdown, notify
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.base import get_db
from ..models import Project, Task, ProjectStatus, BufferStatus
from ..controllers import ProjectController, TaskController
from ..utils import calculate_critical_chain, identify_feeding_chains
from .layout import create_page_layout

# Initialize controllers
project_controller = ProjectController()
task_controller = TaskController()

# Projects content
projects_content = """
# Projects

<|tabs|
<|tab|label=Project List|
<|layout|columns=3 1|
<|{projects}|table|width=100%|selected={selected_project}|on_selection_change=on_project_selected|>

<|card|
<|New Project|button|on_action=on_new_project|>

<|part|render={selected_project is not None}|
## Selected Project

**Project:** <|{selected_project["name"] if selected_project else ""}|text|>

**Status:** <|{selected_project["status"] if selected_project else ""}|text|>

<|Edit Project|button|on_action=on_edit_project|>
<|Delete Project|button|on_action=on_delete_project|>
<|View Details|button|on_action=on_view_project_details|>
|>
<|card|>
|>
|>

<|tab|label=Project Details|active={project_id is not None}|
<|part|render={current_project is not None}|
# Project: <|{current_project["name"]}|text|>

<|layout|columns=1 1|
<|card|
## Basic Information

**ID:** <|{current_project["id"]}|text|>

**Description:** <|{current_project["description"]}|text|>

**Status:** <|{current_project["status"]}|text|>

**Start Date:** <|{current_project["start_date"]}|text|>

**Target End Date:** <|{current_project["target_end_date"]}|text|>

**Actual End Date:** <|{current_project["actual_end_date"]}|text|>
<|card|>

<|card|
## Buffer Information

**Project Buffer:** <|{current_project["project_buffer"]}|text|> hours

**Buffer Consumption:** <|{current_project["buffer_consumption"]}|text|>%

**Buffer Status:** <|{current_project["buffer_status"]}|text|>

<|Calculate Buffer Consumption|button|on_action=on_calculate_buffer|>
<|card|>
|>

<|layout|columns=1 1 1|
<|Activate Project|button|on_action=on_activate_project|active={current_project["status"] != "active"}|>
<|Complete Project|button|on_action=on_complete_project|active={current_project["status"] == "active"}|>
<|Back to List|button|on_action=on_back_to_list|>
|>

## Project Tasks
<|{project_tasks}|table|width=100%|>

## Critical Chain
<|{critical_chain_tasks}|table|width=100%|>

<|Calculate Critical Chain|button|on_action=on_calculate_critical_chain|>
|>

<|part|render={current_project is None}|
No project selected. <|Back to List|button|on_action=on_back_to_list|>
|>
|>

<|tab|label=New/Edit Project|active={is_editing}|
<|card|
# <|{editing_mode}|text|> Project

<|layout|columns=1 1|
<|
**Name:** <|{edit_project["name"]}|input|>

**Description:** <|{edit_project["description"]}|input|multiline=true|>

**Status:**
<|{edit_project["status"]}|selector|lov={project_statuses}|>
|>

<|
**Start Date:** <|{edit_project["start_date"]}|date|>

**Target End Date:** <|{edit_project["target_end_date"]}|date|>

**Project Buffer (hours):** <|{edit_project["project_buffer"]}|number|>
|>
|>

<|layout|columns=1 1 1|
<|Save|button|on_action=on_save_project|>
<|Cancel|button|on_action=on_cancel_edit|>
|>
<|card|>
|>
|>
"""

# Create the projects page
projects_page = create_page_layout(projects_content)

# Data for the projects page
projects = []
selected_project = None
current_project = None
project_tasks = []
critical_chain_tasks = []
project_id = None
is_editing = False
editing_mode = "New"
edit_project = {
    "id": None,
    "name": "",
    "description": "",
    "status": ProjectStatus.PLANNING,
    "start_date": None,
    "target_end_date": None,
    "project_buffer": 0.0
}
project_statuses = [status.value for status in ProjectStatus]

def on_init(state):
    """Initialize the projects state"""
    # Check if project_id is provided in URL
    if hasattr(state, "client_id"):
        from taipy.gui import get_state_id
        state_id = get_state_id(state)
        if state_id and "project_id" in state_id:
            state.project_id = state_id["project_id"]
    
    update_projects_data(state)
    
    # Load project details if project_id is provided
    if state.project_id:
        load_project_details(state, state.project_id)

def update_projects_data(state):
    """Update projects data from the database"""
    db = next(get_db())
    
    # Get all projects
    projects_db = db.query(Project).order_by(Project.updated_at.desc()).all()
    
    state.projects = [{
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "buffer_status": project.buffer_status,
        "buffer_consumption": project.buffer_consumption,
        "start_date": project.start_date.strftime("%Y-%m-%d") if project.start_date else None,
        "target_end_date": project.target_end_date.strftime("%Y-%m-%d") if project.target_end_date else None
    } for project in projects_db]

def load_project_details(state, project_id):
    """Load project details"""
    db = next(get_db())
    project = project_controller.get(db, project_id)
    
    if project:
        # Format dates
        start_date = project.start_date.strftime("%Y-%m-%d") if project.start_date else "Not set"
        target_end_date = project.target_end_date.strftime("%Y-%m-%d") if project.target_end_date else "Not set"
        actual_end_date = project.actual_end_date.strftime("%Y-%m-%d") if project.actual_end_date else "Not completed"
        
        # Set current project
        state.current_project = {
            "id": project.id,
            "name": project.name,
            "description": project.description or "",
            "status": project.status,
            "start_date": start_date,
            "target_end_date": target_end_date,
            "actual_end_date": actual_end_date,
            "project_buffer": project.project_buffer,
            "buffer_consumption": project.buffer_consumption,
            "buffer_status": project.buffer_status
        }
        
        # Get project tasks
        tasks = db.query(Task).filter(Task.project_id == project_id).all()
        state.project_tasks = [{
            "id": task.id,
            "name": task.name,
            "status": task.status,
            "priority": task.priority,
            "estimated_time": task.estimated_time,
            "buffer_time": task.buffer_time,
            "actual_time": task.actual_time or 0,
            "completion_percentage": task.completion_percentage,
            "is_critical_chain": task.is_critical_chain
        } for task in tasks]
        
        # Get critical chain tasks
        critical_tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.is_critical_chain == True
        ).all()
        
        state.critical_chain_tasks = [{
            "id": task.id,
            "name": task.name,
            "status": task.status,
            "estimated_time": task.estimated_time,
            "buffer_time": task.buffer_time,
            "actual_time": task.actual_time or 0,
            "completion_percentage": task.completion_percentage
        } for task in critical_tasks]
    else:
        state.current_project = None
        state.project_tasks = []
        state.critical_chain_tasks = []

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

def on_new_project(state):
    """Create a new project"""
    state.edit_project = {
        "id": None,
        "name": "",
        "description": "",
        "status": ProjectStatus.PLANNING,
        "start_date": None,
        "target_end_date": None,
        "project_buffer": 0.0
    }
    state.editing_mode = "New"
    state.is_editing = True

def on_edit_project(state):
    """Edit the selected project"""
    if state.selected_project:
        db = next(get_db())
        project = project_controller.get(db, state.selected_project["id"])
        
        if project:
            # Convert dates to strings for the date picker
            start_date = project.start_date.strftime("%Y-%m-%d") if project.start_date else None
            target_end_date = project.target_end_date.strftime("%Y-%m-%d") if project.target_end_date else None
            
            state.edit_project = {
                "id": project.id,
                "name": project.name,
                "description": project.description or "",
                "status": project.status,
                "start_date": start_date,
                "target_end_date": target_end_date,
                "project_buffer": project.project_buffer
            }
            state.editing_mode = "Edit"
            state.is_editing = True

def on_delete_project(state):
    """Delete the selected project"""
    if state.selected_project:
        db = next(get_db())
        project = project_controller.delete(db, state.selected_project["id"])
        
        # Update projects data
        update_projects_data(state)
        state.selected_project = None
        
        # Show notification
        notify(state, "success", f"Project '{project.name}' deleted")

def on_save_project(state):
    """Save the project"""
    db = next(get_db())
    
    # Convert dates
    start_date = None
    if state.edit_project["start_date"]:
        if isinstance(state.edit_project["start_date"], str):
            start_date = datetime.strptime(state.edit_project["start_date"], "%Y-%m-%d")
        else:
            start_date = state.edit_project["start_date"]
            
    target_end_date = None
    if state.edit_project["target_end_date"]:
        if isinstance(state.edit_project["target_end_date"], str):
            target_end_date = datetime.strptime(state.edit_project["target_end_date"], "%Y-%m-%d")
        else:
            target_end_date = state.edit_project["target_end_date"]
    
    # Prepare project data
    project_data = {
        "name": state.edit_project["name"],
        "description": state.edit_project["description"],
        "status": state.edit_project["status"],
        "start_date": start_date,
        "target_end_date": target_end_date,
        "project_buffer": state.edit_project["project_buffer"]
    }
    
    if state.edit_project["id"]:
        # Update existing project
        project = project_controller.get(db, state.edit_project["id"])
        project = project_controller.update(db, project, project_data)
        
        # Show notification
        notify(state, "success", f"Project '{project.name}' updated")
    else:
        # Create new project
        project = project_controller.create(db, project_data)
        
        # Show notification
        notify(state, "success", f"Project '{project.name}' created")
    
    # Update projects data
    update_projects_data(state)
    state.is_editing = False
    
    # If this was a new project, select it
    if not state.edit_project["id"]:
        for i, p in enumerate(state.projects):
            if p["id"] == project.id:
                state.selected_project = state.projects[i]
                break

def on_cancel_edit(state):
    """Cancel project editing"""
    state.is_editing = False

def on_view_project_details(state):
    """View project details"""
    if state.selected_project:
        state.project_id = state.selected_project["id"]
        load_project_details(state, state.project_id)
        from taipy.gui import navigate
        navigate(state, f"/projects?project_id={state.project_id}")

def on_back_to_list(state):
    """Go back to project list"""
    state.project_id = None
    state.current_project = None
    from taipy.gui import navigate
    navigate(state, "/projects")

def on_activate_project(state):
    """Activate the current project"""
    if state.current_project:
        db = next(get_db())
        project = project_controller.update_project_status(db, state.current_project["id"], ProjectStatus.ACTIVE)
        
        # Reload project details
        load_project_details(state, state.current_project["id"])
        
        # Update projects data
        update_projects_data(state)
        
        # Show notification
        notify(state, "success", f"Project '{project.name}' activated")

def on_complete_project(state):
    """Complete the current project"""
    if state.current_project:
        db = next(get_db())
        project = project_controller.update_project_status(db, state.current_project["id"], ProjectStatus.COMPLETED)
        
        # Reload project details
        load_project_details(state, state.current_project["id"])
        
        # Update projects data
        update_projects_data(state)
        
        # Show notification
        notify(state, "success", f"Project '{project.name}' completed")

def on_calculate_buffer(state):
    """Calculate buffer consumption for the current project"""
    if state.current_project:
        db = next(get_db())
        buffer_consumption = project_controller.calculate_project_buffer_consumption(db, state.current_project["id"])
        
        # Reload project details
        load_project_details(state, state.current_project["id"])
        
        # Show notification
        notify(state, "success", f"Buffer consumption calculated: {buffer_consumption:.2f}%")

def on_calculate_critical_chain(state):
    """Calculate critical chain for the current project"""
    if state.current_project:
        db = next(get_db())
        
        # Calculate critical chain
        from ..utils.critical_chain import calculate_critical_chain
        critical_chain_tasks = calculate_critical_chain(db, state.current_project["id"])
        
        # Reload project details
        load_project_details(state, state.current_project["id"])
        
        # Show notification
        notify(state, "success", f"Critical chain calculated with {len(critical_chain_tasks)} tasks")