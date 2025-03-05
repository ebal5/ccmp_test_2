from taipy.gui import Markdown, notify
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.base import get_db
from ..models import Project, Task, FeedingBuffer, BufferStatus
from ..controllers import ProjectController, TaskController
from ..utils import calculate_project_buffer, calculate_feeding_buffer, calculate_buffer_status, calculate_estimated_completion_date
from .layout import create_page_layout

# Initialize controllers
project_controller = ProjectController()
task_controller = TaskController()

# Buffer management content
buffer_management_content = """
# Buffer Management

<|tabs|
<|tab|label=Project Buffers|
<|{projects}|table|width=100%|selected={selected_project}|on_selection_change=on_project_selected|>

<|part|render={selected_project is not None}|
<|card|
## Project Buffer: <|{selected_project["name"] if selected_project else ""}|text|>

<|layout|columns=1 1 1|
<|card|
**Buffer Size:** <|{selected_project["project_buffer"] if selected_project else 0}|text|> hours

**Buffer Consumption:** <|{selected_project["buffer_consumption"] if selected_project else 0}|text|>%

**Buffer Status:** <|{selected_project["buffer_status"] if selected_project else ""}|text|>
<|card|>

<|card|
<|{buffer_chart}|chart|type=gauge|value={selected_project["buffer_consumption"] if selected_project else 0}|min=0|max=100|
ranges={[
    {"min": 0, "max": 33, "color": "green"},
    {"min": 33, "max": 66, "color": "yellow"},
    {"min": 66, "max": 100, "color": "red"}
]}|>
<|card|>

<|card|
**Target End Date:** <|{selected_project["target_end_date"] if selected_project else ""}|text|>

**Estimated Completion:** <|{selected_project["estimated_completion"] if selected_project else ""}|text|>

<|Calculate Estimated Completion|button|on_action=on_calculate_completion|>
<|card|>
|>
<|card|>

<|card|
## Buffer Management Actions

<|layout|columns=1 1 1|
<|Calculate Buffer Consumption|button|on_action=on_calculate_buffer|>
<|Recalculate Project Buffer|button|on_action=on_recalculate_buffer|>
<|View Project Details|button|on_action=on_view_project|>
|>
<|card|>
|>

<|part|render={selected_project is None}|
No project selected
|>
|>

<|tab|label=Feeding Buffers|
<|{feeding_buffers}|table|width=100%|selected={selected_feeding_buffer}|on_selection_change=on_feeding_buffer_selected|>

<|part|render={selected_feeding_buffer is not None}|
<|card|
## Feeding Buffer: <|{selected_feeding_buffer["name"] if selected_feeding_buffer else ""}|text|>

<|layout|columns=1 1 1|
<|card|
**Buffer Size:** <|{selected_feeding_buffer["buffer_size"] if selected_feeding_buffer else 0}|text|> hours

**Buffer Consumption:** <|{selected_feeding_buffer["buffer_consumption"] if selected_feeding_buffer else 0}|text|>%

**Buffer Status:** <|{selected_feeding_buffer["buffer_status"] if selected_feeding_buffer else ""}|text|>
<|card|>

<|card|
<|{feeding_buffer_chart}|chart|type=gauge|value={selected_feeding_buffer["buffer_consumption"] if selected_feeding_buffer else 0}|min=0|max=100|
ranges={[
    {"min": 0, "max": 33, "color": "green"},
    {"min": 33, "max": 66, "color": "yellow"},
    {"min": 66, "max": 100, "color": "red"}
]}|>
<|card|>

<|card|
**Project:** <|{selected_feeding_buffer["project_name"] if selected_feeding_buffer else ""}|text|>

**Merge Task:** <|{selected_feeding_buffer["merge_task_name"] if selected_feeding_buffer else ""}|text|>

<|Delete Feeding Buffer|button|on_action=on_delete_feeding_buffer|>
<|card|>
|>
<|card|>
|>

<|part|render={selected_feeding_buffer is None}|
No feeding buffer selected
|>

<|New Feeding Buffer|button|on_action=on_new_feeding_buffer|>
|>

<|tab|label=Buffer Trends|
<|card|
## Buffer Trend Settings

**Project:**
<|{trend_project_id}|selector|lov={project_options}|>

**Time Period:**
<|{trend_time_period}|selector|lov={time_period_options}|>

<|Generate Trend|button|on_action=on_generate_trend|>
<|card|>

<|card|
## Buffer Consumption Trend

<|{buffer_trend_chart}|chart|type=line|x=date|y[1]=consumption|y[2]=completion|>
<|card|>
|>
|>
"""

# Create the buffer management page
buffer_management_page = create_page_layout(buffer_management_content)

# Data for the buffer management page
projects = []
selected_project = None
buffer_chart = {}
feeding_buffers = []
selected_feeding_buffer = None
feeding_buffer_chart = {}

# Trend data
trend_project_id = None
trend_time_period = "last_30_days"
buffer_trend_chart = {"date": [], "consumption": [], "completion": []}
project_options = []
time_period_options = [
    {"id": "last_7_days", "label": "Last 7 Days"},
    {"id": "last_30_days", "label": "Last 30 Days"},
    {"id": "last_90_days", "label": "Last 90 Days"},
    {"id": "all_time", "label": "All Time"}
]

def on_init(state):
    """Initialize the buffer management state"""
    update_projects_data(state)
    update_feeding_buffers_data(state)
    update_project_options(state)

def update_projects_data(state):
    """Update projects data from the database"""
    db = next(get_db())
    
    # Get all projects
    projects_db = db.query(Project).all()
    
    state.projects = [{
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "project_buffer": project.project_buffer,
        "buffer_consumption": project.buffer_consumption,
        "buffer_status": project.buffer_status,
        "start_date": project.start_date.strftime("%Y-%m-%d") if project.start_date else None,
        "target_end_date": project.target_end_date.strftime("%Y-%m-%d") if project.target_end_date else None,
        "estimated_completion": "Not calculated"
    } for project in projects_db]

def update_feeding_buffers_data(state):
    """Update feeding buffers data from the database"""
    db = next(get_db())
    
    # Get all feeding buffers
    feeding_buffers_db = db.query(FeedingBuffer).all()
    
    state.feeding_buffers = [{
        "id": buffer.id,
        "name": buffer.name,
        "buffer_size": buffer.buffer_size,
        "buffer_consumption": buffer.buffer_consumption,
        "buffer_status": buffer.buffer_status,
        "project_id": buffer.project_id,
        "project_name": buffer.project.name if buffer.project else "None",
        "merge_task_id": buffer.merge_task_id,
        "merge_task_name": db.query(Task).filter(Task.id == buffer.merge_task_id).first().name if buffer.merge_task_id else "None"
    } for buffer in feeding_buffers_db]

def update_project_options(state):
    """Update project options for dropdown"""
    db = next(get_db())
    
    # Get projects for dropdown
    projects_db = db.query(Project).all()
    state.project_options = [
        {"id": project.id, "label": project.name}
        for project in projects_db
    ]

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

def on_feeding_buffer_selected(state, action, payload):
    """Handle feeding buffer selection"""
    if payload and "index" in payload:
        index = payload["index"]
        if 0 <= index < len(state.feeding_buffers):
            state.selected_feeding_buffer = state.feeding_buffers[index]
        else:
            state.selected_feeding_buffer = None
    else:
        state.selected_feeding_buffer = None

def on_calculate_buffer(state):
    """Calculate buffer consumption for the selected project"""
    if state.selected_project:
        db = next(get_db())
        buffer_consumption = project_controller.calculate_project_buffer_consumption(db, state.selected_project["id"])
        
        # Update projects data
        update_projects_data(state)
        
        # Update selected project
        for project in state.projects:
            if project["id"] == state.selected_project["id"]:
                state.selected_project = project
                break
        
        # Show notification
        notify(state, "success", f"Buffer consumption calculated: {buffer_consumption:.2f}%")

def on_recalculate_buffer(state):
    """Recalculate project buffer size"""
    if state.selected_project:
        db = next(get_db())
        project = project_controller.get(db, state.selected_project["id"])
        
        if project:
            # Get critical chain tasks
            critical_tasks = db.query(Task).filter(
                Task.project_id == project.id,
                Task.is_critical_chain == True
            ).all()
            
            if critical_tasks:
                # Calculate new buffer size
                task_durations = [task.estimated_time for task in critical_tasks]
                new_buffer = calculate_project_buffer(task_durations)
                
                # Update project
                project.project_buffer = new_buffer
                db.add(project)
                db.commit()
                
                # Update projects data
                update_projects_data(state)
                
                # Update selected project
                for p in state.projects:
                    if p["id"] == state.selected_project["id"]:
                        state.selected_project = p
                        break
                
                # Show notification
                notify(state, "success", f"Project buffer recalculated: {new_buffer:.2f} hours")
            else:
                notify(state, "error", "No critical chain tasks found. Calculate critical chain first.")
        else:
            notify(state, "error", "Project not found")

def on_calculate_completion(state):
    """Calculate estimated completion date"""
    if state.selected_project:
        db = next(get_db())
        project = project_controller.get(db, state.selected_project["id"])
        
        if project and project.start_date and project.target_end_date:
            # Get project progress
            tasks = db.query(Task).filter(Task.project_id == project.id).all()
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == "completed"])
            
            if total_tasks > 0:
                project_progress = (completed_tasks / total_tasks) * 100
                
                # Calculate estimated completion date
                estimated_date = calculate_estimated_completion_date(
                    project_progress,
                    project.buffer_consumption,
                    project.start_date,
                    project.target_end_date
                )
                
                # Update selected project
                state.selected_project["estimated_completion"] = estimated_date.strftime("%Y-%m-%d") if estimated_date else "Not available"
                
                # Show notification
                notify(state, "success", f"Estimated completion date: {state.selected_project['estimated_completion']}")
            else:
                notify(state, "error", "No tasks found in project")
        else:
            notify(state, "error", "Project start date or target end date not set")

def on_view_project(state):
    """View project details"""
    if state.selected_project:
        from taipy.gui import navigate
        navigate(state, f"/projects?project_id={state.selected_project['id']}")

def on_new_feeding_buffer(state):
    """Create a new feeding buffer"""
    # TODO: Implement feeding buffer creation form
    notify(state, "info", "Feeding buffer creation not implemented yet")

def on_delete_feeding_buffer(state):
    """Delete the selected feeding buffer"""
    if state.selected_feeding_buffer:
        db = next(get_db())
        buffer = db.query(FeedingBuffer).filter(FeedingBuffer.id == state.selected_feeding_buffer["id"]).first()
        
        if buffer:
            db.delete(buffer)
            db.commit()
            
            # Update feeding buffers data
            update_feeding_buffers_data(state)
            state.selected_feeding_buffer = None
            
            # Show notification
            notify(state, "success", f"Feeding buffer '{buffer.name}' deleted")
        else:
            notify(state, "error", "Feeding buffer not found")

def on_generate_trend(state):
    """Generate buffer trend chart"""
    if state.trend_project_id:
        db = next(get_db())
        project = project_controller.get(db, state.trend_project_id)
        
        if project:
            # TODO: Implement actual trend data retrieval from database
            # For now, generate sample data
            import random
            from datetime import datetime, timedelta
            
            # Generate dates
            if state.trend_time_period == "last_7_days":
                days = 7
            elif state.trend_time_period == "last_30_days":
                days = 30
            elif state.trend_time_period == "last_90_days":
                days = 90
            else:
                days = 90  # Default to 90 days for "all_time"
                
            end_date = datetime.now()
            dates = [(end_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
            dates.reverse()  # Oldest first
            
            # Generate sample data
            buffer_consumption = []
            project_completion = []
            
            # Start with some initial values
            initial_consumption = max(0, min(project.buffer_consumption - 20, 10))
            initial_completion = 0
            
            for i in range(days):
                # Gradually increase both values
                completion_increment = 100 / days
                initial_completion += completion_increment
                
                # Buffer consumption increases more rapidly in the middle
                if i < days / 3:
                    consumption_increment = 0.5
                elif i < 2 * days / 3:
                    consumption_increment = 1.5
                else:
                    consumption_increment = 1.0
                    
                initial_consumption += consumption_increment + random.uniform(-0.5, 0.5)
                
                # Ensure values are within bounds
                buffer_consumption.append(max(0, min(initial_consumption, 100)))
                project_completion.append(max(0, min(initial_completion, 100)))
            
            # Update chart data
            state.buffer_trend_chart = {
                "date": dates,
                "consumption": buffer_consumption,
                "completion": project_completion
            }
            
            # Show notification
            notify(state, "success", f"Trend generated for project '{project.name}'")
        else:
            notify(state, "error", "Project not found")