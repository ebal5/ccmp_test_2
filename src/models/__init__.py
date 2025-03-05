from .base import Base, engine, get_db
from .task import Task, TaskStatus, TaskPriority
from .project import Project, ProjectStatus, BufferStatus
from .feeding_buffer import FeedingBuffer
from .time_entry import TimeEntry
from .notification import Notification, NotificationType, NotificationStatus, NotificationChannel
from .notification_template import NotificationTemplate
from .api_key import ApiKey

# Create all tables in the database
def create_tables():
    Base.metadata.create_all(bind=engine)