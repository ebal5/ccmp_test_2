from sqlalchemy.orm import Session
from ..models import Base, engine, get_db
from ..models import Project, Task, FeedingBuffer, TimeEntry, NotificationTemplate

def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize with default data
    db = next(get_db())
    
    # Check if we already have data
    if db.query(Project).first() is None:
        _init_default_data(db)
    
    db.close()

def _init_default_data(db: Session):
    # Create default notification templates
    _create_default_notification_templates(db)
    
    # Commit changes
    db.commit()

def _create_default_notification_templates(db: Session):
    # Task status change template for Discord
    discord_task_status = NotificationTemplate(
        name="Discord Task Status Change",
        description="Default template for task status changes on Discord",
        notification_type="task_status_change",
        channel="discord",
        title_template="Task Status Changed: {{task.name}}",
        message_template="Task **{{task.name}}** status changed from **{{old_status}}** to **{{new_status}}**.\n\nProject: {{task.project.name}}\nEstimated time: {{task.estimated_time}} hours\nBuffer: {{task.buffer_time}} hours",
        rich_format={
            "color": 3447003,
            "fields": [
                {"name": "Task", "value": "{{task.name}}", "inline": True},
                {"name": "New Status", "value": "{{new_status}}", "inline": True},
                {"name": "Project", "value": "{{task.project.name}}", "inline": True},
                {"name": "Estimated Time", "value": "{{task.estimated_time}} hours", "inline": True},
                {"name": "Buffer", "value": "{{task.buffer_time}} hours", "inline": True}
            ]
        },
        is_active=True,
        is_default=True
    )
    
    # Buffer alert template for Slack
    slack_buffer_alert = NotificationTemplate(
        name="Slack Buffer Alert",
        description="Default template for buffer alerts on Slack",
        notification_type="buffer_alert",
        channel="slack",
        title_template="Buffer Alert: {{project.name}}",
        message_template="Project *{{project.name}}* buffer consumption is now at *{{project.buffer_consumption}}%* ({{buffer_status}}).",
        rich_format={
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Buffer Alert: {{project.name}}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Project *{{project.name}}* buffer consumption is now at *{{project.buffer_consumption}}%* ({{buffer_status}})."
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Project:*\n{{project.name}}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Buffer Status:*\n{{buffer_status}}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Consumption:*\n{{project.buffer_consumption}}%"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Target End Date:*\n{{project.target_end_date}}"
                        }
                    ]
                }
            ]
        },
        is_active=True,
        is_default=True
    )
    
    # Add templates to database
    db.add(discord_task_status)
    db.add(slack_buffer_alert)
    
    # Add more default templates as needed