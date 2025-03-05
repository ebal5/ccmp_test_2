import os
from taipy.gui import Gui, notify

# Dashboard page
dashboard_page = """
# CCPM Task Manager

## Project: Sample Project
### Buffer Consumption
<|{project_buffer_consumption}|progress|value={project_buffer_consumption}|width=100%|>

**Buffer Consumption:** <|{project_buffer_consumption}|text|>%

**Buffer Status:** <|{project_buffer_status}|text|>

## Tasks
<|{task_name}|text|>

**Estimated Time:** <|{task_estimated_time}|text|> hours

**Buffer Time:** <|{task_buffer_time}|text|> hours

**Actual Time:** <|{task_actual_time}|text|> hours

**Completion:** <|{task_completion}|text|>%

<|Start Task|button|on_action=on_start_task|active={task_status == "not_started"}|>
<|Complete Task|button|on_action=on_complete_task|active={task_status == "in_progress"}|>

## Status
<|{status_message}|text|>
"""

# Initialize state variables
task_name = "Sample Task"
task_status = "not_started"
task_estimated_time = 5.0
task_buffer_time = 2.0
task_actual_time = 0.0
task_completion = 0.0
status_message = "Task is ready to start"
project_buffer_consumption = 0.0
project_buffer_status = "green"

def calculate_buffer_consumption(estimated_time, buffer_time, actual_time):
    """Calculate buffer consumption"""
    if actual_time <= estimated_time:
        return 0.0
    else:
        buffer_used = actual_time - estimated_time
        return min(buffer_used / buffer_time * 100, 100.0)

def get_buffer_status(buffer_consumption):
    """Get buffer status based on consumption"""
    if buffer_consumption <= 33.0:
        return "green"
    elif buffer_consumption <= 66.0:
        return "yellow"
    else:
        return "red"

def on_start_task(state):
    """Start the task"""
    state.task_status = "in_progress"
    state.status_message = "Task is in progress"
    notify(state, "success", f"Task '{state.task_name}' started")

def on_complete_task(state):
    """Complete the task"""
    state.task_status = "completed"
    state.task_completion = 100.0
    
    # Simulate actual time being more than estimated
    state.task_actual_time = state.task_estimated_time + (state.task_buffer_time * 0.5)
    
    # Calculate buffer consumption
    state.project_buffer_consumption = calculate_buffer_consumption(
        state.task_estimated_time,
        state.task_buffer_time,
        state.task_actual_time
    )
    
    # Update buffer status
    state.project_buffer_status = get_buffer_status(state.project_buffer_consumption)
    
    state.status_message = f"Task is completed. Buffer consumption: {state.project_buffer_consumption:.1f}%"
    notify(state, "success", f"Task '{state.task_name}' completed")

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