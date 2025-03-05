import os
import pandas as pd
from taipy.gui import Gui, notify

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

# Sample data
tasks_data = [
    {"id": 1, "name": "Task 1", "status": "not_started", "estimated_time": 5.0, "buffer_time": 2.0, "actual_time": 0.0, "completion_percentage": 0.0},
    {"id": 2, "name": "Task 2", "status": "not_started", "estimated_time": 3.0, "buffer_time": 1.0, "actual_time": 0.0, "completion_percentage": 0.0}
]

projects_data = [
    {"id": 1, "name": "Sample Project", "status": "active", "buffer_status": "green", "buffer_consumption": 0.0}
]

# Initialize state variables
tasks_df = pd.DataFrame(tasks_data)
projects_df = pd.DataFrame(projects_data)
selected_task_index = None
selected_task_id = None
selected_task_status = None

def on_init(state):
    """Initialize the state"""
    # Initialize with sample data
    state.tasks_df = pd.DataFrame(tasks_data)
    state.projects_df = pd.DataFrame(projects_data)

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
        # Find the task in the DataFrame
        task_idx = state.tasks_df.index[state.tasks_df['id'] == state.selected_task_id].tolist()[0]
        
        # Update the task status
        state.tasks_df.at[task_idx, 'status'] = "in_progress"
        
        # Update selected task status
        state.selected_task_status = "in_progress"
        
        # Show notification
        notify(state, "success", f"Task '{state.tasks_df.at[task_idx, 'name']}' started")

def on_complete_task(state):
    """Complete the selected task"""
    if state.selected_task_id is not None:
        # Find the task in the DataFrame
        task_idx = state.tasks_df.index[state.tasks_df['id'] == state.selected_task_id].tolist()[0]
        
        # Update the task status and completion
        state.tasks_df.at[task_idx, 'status'] = "completed"
        state.tasks_df.at[task_idx, 'completion_percentage'] = 100.0
        
        # Update selected task status
        state.selected_task_status = "completed"
        
        # Show notification
        notify(state, "success", f"Task '{state.tasks_df.at[task_idx, 'name']}' completed")

def on_refresh(state):
    """Refresh data"""
    # In a real application, this would fetch data from the database
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