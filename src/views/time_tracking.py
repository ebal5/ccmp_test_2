from taipy.gui import Markdown, notify
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..models.base import get_db
from ..models import TimeEntry, Task
from ..controllers import TimeEntryController, TaskController
from .layout import create_page_layout

# Initialize controllers
time_entry_controller = TimeEntryController()
task_controller = TaskController()

# Time tracking content
time_tracking_content = """
# Time Tracking

<|tabs|
<|tab|label=Time Entries|
<|layout|columns=3 1|
<|{time_entries}|table|width=100%|selected={selected_time_entry}|on_selection_change=on_time_entry_selected|>

<|card|
## Time Controls

<|part|render={active_timer is None}|
<|Start Timer|button|on_action=on_start_timer|>

**Task:**
<|{new_timer_task_id}|selector|lov={task_options}|>

**Category:**
<|{new_timer_category}|input|>
|>

<|part|render={active_timer is not None}|
## Active Timer

**Task:** <|{active_timer_task["name"] if active_timer_task else "None"}|text|>

**Category:** <|{active_timer["category"] if active_timer else "None"}|text|>

**Started:** <|{active_timer["start_time"] if active_timer else ""}|text|>

**Duration:** <|{active_timer_duration}|text|> minutes

<|Stop Timer|button|on_action=on_stop_timer|>
|>

<|part|render={selected_time_entry is not None}|
## Selected Entry

**Start:** <|{selected_time_entry["start_time"] if selected_time_entry else ""}|text|>

**End:** <|{selected_time_entry["end_time"] if selected_time_entry else ""}|text|>

**Duration:** <|{selected_time_entry["duration"] if selected_time_entry else ""}|text|>

<|Delete Entry|button|on_action=on_delete_time_entry|>
|>
<|card|>
|>
|>

<|tab|label=Time Reports|
<|card|
## Time Report Settings

**Date Range:**
<|{report_date_range}|selector|lov={date_range_options}|>

**Custom Start Date:**
<|{report_start_date}|date|active={report_date_range == "custom"}|>

**Custom End Date:**
<|{report_end_date}|date|active={report_date_range == "custom"}|>

**Group By:**
<|{report_group_by}|selector|lov={group_by_options}|>

<|Generate Report|button|on_action=on_generate_report|>
<|card|>

<|card|
## Time Report Results

<|{time_report_data}|table|width=100%|>

<|part|render={time_report_data|len > 0}|
<|{time_report_chart}|chart|type=pie|x=label|y=value|>
|>
<|card|>
|>
|>
"""

# Create the time tracking page
time_tracking_page = create_page_layout(time_tracking_content)

# Data for the time tracking page
time_entries = []
selected_time_entry = None
active_timer = None
active_timer_task = None
active_timer_duration = 0
new_timer_task_id = None
new_timer_category = ""
task_options = []

# Report data
report_date_range = "today"
report_start_date = datetime.now().strftime("%Y-%m-%d")
report_end_date = datetime.now().strftime("%Y-%m-%d")
report_group_by = "task"
time_report_data = []
time_report_chart = {"label": [], "value": []}

# Options for dropdowns
date_range_options = [
    {"id": "today", "label": "Today"},
    {"id": "yesterday", "label": "Yesterday"},
    {"id": "this_week", "label": "This Week"},
    {"id": "last_week", "label": "Last Week"},
    {"id": "this_month", "label": "This Month"},
    {"id": "last_month", "label": "Last Month"},
    {"id": "custom", "label": "Custom Range"}
]

group_by_options = [
    {"id": "task", "label": "Task"},
    {"id": "category", "label": "Category"},
    {"id": "day", "label": "Day"},
    {"id": "week", "label": "Week"}
]

def on_init(state):
    """Initialize the time tracking state"""
    update_time_entries(state)
    update_task_options(state)
    check_active_timer(state)

def update_time_entries(state):
    """Update time entries from the database"""
    db = next(get_db())
    
    # Get recent time entries
    time_entries_db = db.query(TimeEntry).order_by(TimeEntry.start_time.desc()).limit(100).all()
    
    state.time_entries = [{
        "id": entry.id,
        "task_id": entry.task_id,
        "task_name": db.query(Task).filter(Task.id == entry.task_id).first().name if entry.task_id else None,
        "category": entry.category,
        "start_time": entry.start_time.strftime("%Y-%m-%d %H:%M"),
        "end_time": entry.end_time.strftime("%Y-%m-%d %H:%M") if entry.end_time else "Active",
        "duration": f"{entry.duration:.2f} hours" if entry.duration else "In progress"
    } for entry in time_entries_db]

def update_task_options(state):
    """Update task options for dropdown"""
    db = next(get_db())
    
    # Get active tasks for dropdown
    tasks_db = db.query(Task).filter(
        Task.status.in_(["not_started", "in_progress"])
    ).all()
    
    state.task_options = [{"id": None, "label": "No Task (Category Only)"}] + [
        {"id": task.id, "label": task.name}
        for task in tasks_db
    ]

def check_active_timer(state):
    """Check for active timer"""
    db = next(get_db())
    
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
        duration_seconds = (datetime.utcnow() - active_timer_db.start_time).total_seconds()
        state.active_timer_duration = round(duration_seconds / 60, 1)
    else:
        state.active_timer = None
        state.active_timer_task = None
        state.active_timer_duration = 0

def on_time_entry_selected(state, action, payload):
    """Handle time entry selection"""
    if payload and "index" in payload:
        index = payload["index"]
        if 0 <= index < len(state.time_entries):
            state.selected_time_entry = state.time_entries[index]
        else:
            state.selected_time_entry = None
    else:
        state.selected_time_entry = None

def on_start_timer(state):
    """Start a new timer"""
    db = next(get_db())
    
    # Start timer
    time_entry = time_entry_controller.start_timer(
        db, 
        task_id=state.new_timer_task_id, 
        category=state.new_timer_category
    )
    
    # Update time entries
    update_time_entries(state)
    check_active_timer(state)
    
    # Reset form
    state.new_timer_task_id = None
    state.new_timer_category = ""
    
    # Show notification
    notify(state, "success", "Timer started")

def on_stop_timer(state):
    """Stop the active timer"""
    if state.active_timer:
        db = next(get_db())
        time_entry = time_entry_controller.stop_timer(db, state.active_timer["id"])
        
        # Update time entries
        update_time_entries(state)
        check_active_timer(state)
        
        # Show notification
        notify(state, "success", "Timer stopped")

def on_delete_time_entry(state):
    """Delete the selected time entry"""
    if state.selected_time_entry:
        db = next(get_db())
        time_entry = time_entry_controller.delete(db, state.selected_time_entry["id"])
        
        # Update time entries
        update_time_entries(state)
        state.selected_time_entry = None
        
        # Show notification
        notify(state, "success", "Time entry deleted")

def on_generate_report(state):
    """Generate time report"""
    db = next(get_db())
    
    # Calculate date range
    start_date, end_date = get_date_range(state.report_date_range, state.report_start_date, state.report_end_date)
    
    # Get time entries in date range
    time_entries = time_entry_controller.get_by_date_range(db, start_date, end_date)
    
    # Group data based on selection
    grouped_data = group_time_entries(db, time_entries, state.report_group_by)
    
    # Update report data
    state.time_report_data = grouped_data
    
    # Update chart data
    state.time_report_chart = {
        "label": [item["label"] for item in grouped_data],
        "value": [item["hours"] for item in grouped_data]
    }
    
    # Show notification
    notify(state, "success", f"Report generated for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

def get_date_range(range_type, custom_start=None, custom_end=None):
    """Get start and end dates based on range type"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if range_type == "today":
        return today, today + timedelta(days=1) - timedelta(microseconds=1)
    elif range_type == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday + timedelta(days=1) - timedelta(microseconds=1)
    elif range_type == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=7) - timedelta(microseconds=1)
    elif range_type == "last_week":
        start = today - timedelta(days=today.weekday() + 7)
        return start, start + timedelta(days=7) - timedelta(microseconds=1)
    elif range_type == "this_month":
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end = today.replace(month=today.month + 1, day=1)
        return start, end - timedelta(microseconds=1)
    elif range_type == "last_month":
        if today.month == 1:
            start = today.replace(year=today.year - 1, month=12, day=1)
            end = today.replace(month=1, day=1)
        else:
            start = today.replace(month=today.month - 1, day=1)
            end = today.replace(day=1)
        return start, end - timedelta(microseconds=1)
    elif range_type == "custom":
        if isinstance(custom_start, str):
            start = datetime.strptime(custom_start, "%Y-%m-%d")
        else:
            start = custom_start
            
        if isinstance(custom_end, str):
            end = datetime.strptime(custom_end, "%Y-%m-%d")
        else:
            end = custom_end
            
        return start, end + timedelta(days=1) - timedelta(microseconds=1)
    
    # Default to today
    return today, today + timedelta(days=1) - timedelta(microseconds=1)

def group_time_entries(db, time_entries, group_by):
    """Group time entries by the specified field"""
    result = {}
    
    for entry in time_entries:
        # Skip entries without duration
        if not entry.duration:
            continue
            
        if group_by == "task":
            if entry.task_id:
                task = db.query(Task).filter(Task.id == entry.task_id).first()
                key = task.name if task else f"Task {entry.task_id}"
            else:
                key = "No Task"
        elif group_by == "category":
            key = entry.category or "No Category"
        elif group_by == "day":
            key = entry.start_time.strftime("%Y-%m-%d")
        elif group_by == "week":
            # Get the Monday of the week
            monday = entry.start_time - timedelta(days=entry.start_time.weekday())
            key = f"Week of {monday.strftime('%Y-%m-%d')}"
        else:
            key = "Unknown"
            
        if key in result:
            result[key] += entry.duration
        else:
            result[key] = entry.duration
    
    # Convert to list of dictionaries
    return [{"label": key, "hours": value, "percentage": 0} for key, value in result.items()]