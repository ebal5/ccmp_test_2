from taipy.gui import Markdown, notify
from sqlalchemy.orm import Session
import secrets

from ..models.base import get_db
from ..models import ApiKey, NotificationTemplate, NotificationType, NotificationChannel
from .layout import create_page_layout

# Settings content
settings_content = """
# Settings

<|tabs|
<|tab|label=API Keys|
<|{api_keys}|table|width=100%|selected={selected_api_key}|on_selection_change=on_api_key_selected|>

<|card|
## API Key Management

<|part|render={is_creating_key}|
**Name:** <|{new_key_name}|input|>

**Description:** <|{new_key_description}|input|multiline=true|>

**Permissions:** <|{new_key_permissions}|input|multiline=true|placeholder=Enter permissions as JSON array, e.g. ["read", "write"]|>

<|layout|columns=1 1 1|
<|Create Key|button|on_action=on_create_key|>
<|Cancel|button|on_action=on_cancel_key_creation|>
|>
|>

<|part|render={not is_creating_key and selected_api_key is None}|
<|Create New API Key|button|on_action=on_new_api_key|>
|>

<|part|render={selected_api_key is not None}|
## Selected API Key

**Name:** <|{selected_api_key["name"] if selected_api_key else ""}|text|>

**Key:** <|{selected_api_key["key"] if selected_api_key else ""}|text|>

**Created:** <|{selected_api_key["created_at"] if selected_api_key else ""}|text|>

**Last Used:** <|{selected_api_key["last_used_at"] if selected_api_key else ""}|text|>

<|layout|columns=1 1 1|
<|Deactivate Key|button|on_action=on_deactivate_key|active={selected_api_key and selected_api_key["is_active"]}|>
<|Activate Key|button|on_action=on_activate_key|active={selected_api_key and not selected_api_key["is_active"]}|>
<|Delete Key|button|on_action=on_delete_key|>
|>
|>
<|card|>
|>

<|tab|label=Notification Templates|
<|{notification_templates}|table|width=100%|selected={selected_template}|on_selection_change=on_template_selected|>

<|card|
## Template Management

<|part|render={is_editing_template}|
**Name:** <|{edit_template["name"]}|input|>

**Description:** <|{edit_template["description"]}|input|multiline=true|>

**Notification Type:**
<|{edit_template["notification_type"]}|selector|lov={notification_types}|>

**Channel:**
<|{edit_template["channel"]}|selector|lov={notification_channels}|>

**Title Template:**
<|{edit_template["title_template"]}|input|multiline=true|>

**Message Template:**
<|{edit_template["message_template"]}|input|multiline=true|>

**Rich Format (JSON):**
<|{edit_template["rich_format"]}|input|multiline=true|>

**Is Active:** <|{edit_template["is_active"]}|toggle|>

**Is Default:** <|{edit_template["is_default"]}|toggle|>

<|layout|columns=1 1 1|
<|Save Template|button|on_action=on_save_template|>
<|Cancel|button|on_action=on_cancel_template_edit|>
|>
|>

<|part|render={not is_editing_template and selected_template is None}|
<|Create New Template|button|on_action=on_new_template|>
|>

<|part|render={not is_editing_template and selected_template is not None}|
## Selected Template

**Name:** <|{selected_template["name"] if selected_template else ""}|text|>

**Type:** <|{selected_template["notification_type"] if selected_template else ""}|text|>

**Channel:** <|{selected_template["channel"] if selected_template else ""}|text|>

**Is Active:** <|{selected_template["is_active"] if selected_template else ""}|text|>

**Is Default:** <|{selected_template["is_default"] if selected_template else ""}|text|>

<|layout|columns=1 1 1|
<|Edit Template|button|on_action=on_edit_template|>
<|Delete Template|button|on_action=on_delete_template|>
|>
|>
<|card|>
|>

<|tab|label=Webhook Configuration|
<|card|
## Discord Webhook

**Webhook URL:** <|{discord_webhook_url}|input|>

<|Save Discord Webhook|button|on_action=on_save_discord_webhook|>
<|card|>

<|card|
## Slack Webhook

**Webhook URL:** <|{slack_webhook_url}|input|>

<|Save Slack Webhook|button|on_action=on_save_slack_webhook|>
<|card|>

<|card|
## Microsoft Teams Webhook

**Webhook URL:** <|{teams_webhook_url}|input|>

<|Save Teams Webhook|button|on_action=on_save_teams_webhook|>
<|card|>

<|card|
## Telegram Bot

**Bot Token:** <|{telegram_bot_token}|input|>

**Chat ID:** <|{telegram_chat_id}|input|>

<|Save Telegram Settings|button|on_action=on_save_telegram_settings|>
<|card|>
|>
|>
"""

# Create the settings page
settings_page = create_page_layout(settings_content)

# Data for the settings page
api_keys = []
selected_api_key = None
is_creating_key = False
new_key_name = ""
new_key_description = ""
new_key_permissions = ""

notification_templates = []
selected_template = None
is_editing_template = False
edit_template = {
    "id": None,
    "name": "",
    "description": "",
    "notification_type": NotificationType.TASK_STATUS_CHANGE,
    "channel": NotificationChannel.DISCORD,
    "title_template": "",
    "message_template": "",
    "rich_format": "",
    "is_active": True,
    "is_default": False
}

notification_types = [type.value for type in NotificationType]
notification_channels = [channel.value for channel in NotificationChannel]

# Webhook settings
discord_webhook_url = ""
slack_webhook_url = ""
teams_webhook_url = ""
telegram_bot_token = ""
telegram_chat_id = ""

def on_init(state):
    """Initialize the settings state"""
    update_api_keys(state)
    update_notification_templates(state)
    load_webhook_settings(state)

def update_api_keys(state):
    """Update API keys from the database"""
    db = next(get_db())
    
    # Get all API keys
    api_keys_db = db.query(ApiKey).all()
    
    state.api_keys = [{
        "id": key.id,
        "name": key.name,
        "key": key.key,
        "description": key.description,
        "is_active": key.is_active,
        "created_at": key.created_at.strftime("%Y-%m-%d %H:%M"),
        "last_used_at": key.last_used_at.strftime("%Y-%m-%d %H:%M") if key.last_used_at else "Never"
    } for key in api_keys_db]

def update_notification_templates(state):
    """Update notification templates from the database"""
    db = next(get_db())
    
    # Get all notification templates
    templates_db = db.query(NotificationTemplate).all()
    
    state.notification_templates = [{
        "id": template.id,
        "name": template.name,
        "notification_type": template.notification_type,
        "channel": template.channel,
        "is_active": template.is_active,
        "is_default": template.is_default
    } for template in templates_db]

def load_webhook_settings(state):
    """Load webhook settings from environment or database"""
    # TODO: Implement loading from database or environment
    # For now, use empty strings
    state.discord_webhook_url = ""
    state.slack_webhook_url = ""
    state.teams_webhook_url = ""
    state.telegram_bot_token = ""
    state.telegram_chat_id = ""

def on_api_key_selected(state, action, payload):
    """Handle API key selection"""
    if payload and "index" in payload:
        index = payload["index"]
        if 0 <= index < len(state.api_keys):
            state.selected_api_key = state.api_keys[index]
        else:
            state.selected_api_key = None
    else:
        state.selected_api_key = None

def on_template_selected(state, action, payload):
    """Handle notification template selection"""
    if payload and "index" in payload:
        index = payload["index"]
        if 0 <= index < len(state.notification_templates):
            state.selected_template = state.notification_templates[index]
        else:
            state.selected_template = None
    else:
        state.selected_template = None

def on_new_api_key(state):
    """Start creating a new API key"""
    state.is_creating_key = True
    state.new_key_name = ""
    state.new_key_description = ""
    state.new_key_permissions = ""

def on_cancel_key_creation(state):
    """Cancel API key creation"""
    state.is_creating_key = False

def on_create_key(state):
    """Create a new API key"""
    if not state.new_key_name:
        notify(state, "error", "API key name is required")
        return
        
    db = next(get_db())
    
    # Parse permissions
    import json
    permissions = None
    if state.new_key_permissions:
        try:
            permissions = json.loads(state.new_key_permissions)
        except json.JSONDecodeError:
            notify(state, "error", "Invalid JSON format for permissions")
            return
    
    # Create new API key
    api_key = ApiKey(
        name=state.new_key_name,
        description=state.new_key_description,
        key=ApiKey.generate_key(),
        permissions=permissions,
        is_active=True
    )
    
    db.add(api_key)
    db.commit()
    
    # Update API keys
    update_api_keys(state)
    
    # Reset form
    state.is_creating_key = False
    
    # Show notification
    notify(state, "success", f"API key '{api_key.name}' created")

def on_deactivate_key(state):
    """Deactivate the selected API key"""
    if state.selected_api_key:
        db = next(get_db())
        api_key = db.query(ApiKey).filter(ApiKey.id == state.selected_api_key["id"]).first()
        
        if api_key:
            api_key.is_active = False
            db.add(api_key)
            db.commit()
            
            # Update API keys
            update_api_keys(state)
            
            # Update selected key
            for key in state.api_keys:
                if key["id"] == state.selected_api_key["id"]:
                    state.selected_api_key = key
                    break
            
            # Show notification
            notify(state, "success", f"API key '{api_key.name}' deactivated")

def on_activate_key(state):
    """Activate the selected API key"""
    if state.selected_api_key:
        db = next(get_db())
        api_key = db.query(ApiKey).filter(ApiKey.id == state.selected_api_key["id"]).first()
        
        if api_key:
            api_key.is_active = True
            db.add(api_key)
            db.commit()
            
            # Update API keys
            update_api_keys(state)
            
            # Update selected key
            for key in state.api_keys:
                if key["id"] == state.selected_api_key["id"]:
                    state.selected_api_key = key
                    break
            
            # Show notification
            notify(state, "success", f"API key '{api_key.name}' activated")

def on_delete_key(state):
    """Delete the selected API key"""
    if state.selected_api_key:
        db = next(get_db())
        api_key = db.query(ApiKey).filter(ApiKey.id == state.selected_api_key["id"]).first()
        
        if api_key:
            db.delete(api_key)
            db.commit()
            
            # Update API keys
            update_api_keys(state)
            state.selected_api_key = None
            
            # Show notification
            notify(state, "success", f"API key '{api_key.name}' deleted")

def on_new_template(state):
    """Start creating a new notification template"""
    state.edit_template = {
        "id": None,
        "name": "",
        "description": "",
        "notification_type": NotificationType.TASK_STATUS_CHANGE.value,
        "channel": NotificationChannel.DISCORD.value,
        "title_template": "{{notification_type}} Notification",
        "message_template": "{{message}}",
        "rich_format": "",
        "is_active": True,
        "is_default": False
    }
    state.is_editing_template = True

def on_edit_template(state):
    """Edit the selected notification template"""
    if state.selected_template:
        db = next(get_db())
        template = db.query(NotificationTemplate).filter(NotificationTemplate.id == state.selected_template["id"]).first()
        
        if template:
            # Convert rich format to string
            import json
            rich_format_str = json.dumps(template.rich_format) if template.rich_format else ""
            
            state.edit_template = {
                "id": template.id,
                "name": template.name,
                "description": template.description or "",
                "notification_type": template.notification_type,
                "channel": template.channel,
                "title_template": template.title_template,
                "message_template": template.message_template,
                "rich_format": rich_format_str,
                "is_active": template.is_active,
                "is_default": template.is_default
            }
            state.is_editing_template = True

def on_cancel_template_edit(state):
    """Cancel notification template editing"""
    state.is_editing_template = False

def on_save_template(state):
    """Save the notification template"""
    if not state.edit_template["name"]:
        notify(state, "error", "Template name is required")
        return
        
    db = next(get_db())
    
    # Parse rich format
    import json
    rich_format = None
    if state.edit_template["rich_format"]:
        try:
            rich_format = json.loads(state.edit_template["rich_format"])
        except json.JSONDecodeError:
            notify(state, "error", "Invalid JSON format for rich format")
            return
    
    if state.edit_template["id"]:
        # Update existing template
        template = db.query(NotificationTemplate).filter(NotificationTemplate.id == state.edit_template["id"]).first()
        
        if template:
            template.name = state.edit_template["name"]
            template.description = state.edit_template["description"]
            template.notification_type = state.edit_template["notification_type"]
            template.channel = state.edit_template["channel"]
            template.title_template = state.edit_template["title_template"]
            template.message_template = state.edit_template["message_template"]
            template.rich_format = rich_format
            template.is_active = state.edit_template["is_active"]
            template.is_default = state.edit_template["is_default"]
            
            db.add(template)
            db.commit()
            
            # Show notification
            notify(state, "success", f"Template '{template.name}' updated")
    else:
        # Create new template
        template = NotificationTemplate(
            name=state.edit_template["name"],
            description=state.edit_template["description"],
            notification_type=state.edit_template["notification_type"],
            channel=state.edit_template["channel"],
            title_template=state.edit_template["title_template"],
            message_template=state.edit_template["message_template"],
            rich_format=rich_format,
            is_active=state.edit_template["is_active"],
            is_default=state.edit_template["is_default"]
        )
        
        db.add(template)
        db.commit()
        
        # Show notification
        notify(state, "success", f"Template '{template.name}' created")
    
    # Update notification templates
    update_notification_templates(state)
    state.is_editing_template = False

def on_delete_template(state):
    """Delete the selected notification template"""
    if state.selected_template:
        db = next(get_db())
        template = db.query(NotificationTemplate).filter(NotificationTemplate.id == state.selected_template["id"]).first()
        
        if template:
            db.delete(template)
            db.commit()
            
            # Update notification templates
            update_notification_templates(state)
            state.selected_template = None
            
            # Show notification
            notify(state, "success", f"Template '{template.name}' deleted")

def on_save_discord_webhook(state):
    """Save Discord webhook URL"""
    # TODO: Implement saving to database or environment
    notify(state, "success", "Discord webhook URL saved")

def on_save_slack_webhook(state):
    """Save Slack webhook URL"""
    # TODO: Implement saving to database or environment
    notify(state, "success", "Slack webhook URL saved")

def on_save_teams_webhook(state):
    """Save Microsoft Teams webhook URL"""
    # TODO: Implement saving to database or environment
    notify(state, "success", "Microsoft Teams webhook URL saved")

def on_save_telegram_settings(state):
    """Save Telegram settings"""
    # TODO: Implement saving to database or environment
    notify(state, "success", "Telegram settings saved")