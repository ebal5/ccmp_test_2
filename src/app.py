from taipy.gui import Gui, navigate
from taipy import Core

# Import views
from .views.dashboard import dashboard_page
from .views.tasks import tasks_page
from .views.projects import projects_page
from .views.time_tracking import time_tracking_page
from .views.buffer_management import buffer_management_page
from .views.settings import settings_page

# Define pages
pages = {
    "/": dashboard_page,
    "tasks": tasks_page,
    "projects": projects_page,
    "time_tracking": time_tracking_page,
    "buffer_management": buffer_management_page,
    "settings": settings_page
}

# Initialize state variables
active_tasks = []
projects = []
time_entries = []
selected_task = None
selected_project = None
active_timer = None
active_timer_task = None
active_timer_duration = 0
current_task = None
task_time_entries = []
task_id = None
is_editing = False
editing_mode = "New"
tasks = []

# Create the GUI
gui = Gui(pages=pages)