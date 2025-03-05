from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json
import requests
import aiohttp
import asyncio
from string import Template

from ..models import Notification, NotificationTemplate, NotificationStatus, NotificationType, NotificationChannel
from .base_controller import BaseController

class NotificationController(BaseController[Notification, Dict[str, Any]]):
    def __init__(self):
        super().__init__(Notification)
    
    def get_pending_notifications(self, db: Session) -> List[Notification]:
        """Get all pending notifications"""
        return db.query(Notification).filter(
            Notification.status == NotificationStatus.PENDING
        ).all()
    
    def get_failed_notifications(self, db: Session) -> List[Notification]:
        """Get all failed notifications"""
        return db.query(Notification).filter(
            Notification.status == NotificationStatus.FAILED
        ).all()
    
    def create_notification(
        self, 
        db: Session, 
        notification_type: NotificationType,
        channel: NotificationChannel,
        recipient: str,
        context_data: Dict[str, Any],
        task_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Notification:
        """Create a notification using a template"""
        # Find the appropriate template
        template = db.query(NotificationTemplate).filter(
            NotificationTemplate.notification_type == notification_type,
            NotificationTemplate.channel == channel,
            NotificationTemplate.is_active == True
        ).first()
        
        if not template:
            # Try to find a default template for this type
            template = db.query(NotificationTemplate).filter(
                NotificationTemplate.notification_type == notification_type,
                NotificationTemplate.is_default == True,
                NotificationTemplate.is_active == True
            ).first()
            
        if not template:
            # No template found, create a basic notification
            title = f"{notification_type.capitalize()} Notification"
            message = json.dumps(context_data)
        else:
            # Apply template
            title = self._apply_template(template.title_template, context_data)
            message = self._apply_template(template.message_template, context_data)
        
        # Create notification
        notification = Notification(
            type=notification_type,
            title=title,
            message=message,
            data=context_data,
            channel=channel,
            recipient=recipient,
            task_id=task_id,
            project_id=project_id,
            status=NotificationStatus.PENDING
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return notification
    
    def send_notification(self, db: Session, notification_id: int) -> bool:
        """Send a notification"""
        notification = self.get(db, notification_id)
        if not notification or notification.status == NotificationStatus.SENT:
            return False
            
        success = False
        error_message = None
        
        try:
            # Send based on channel type
            if notification.channel == NotificationChannel.DISCORD:
                success = self._send_discord_notification(notification)
            elif notification.channel == NotificationChannel.SLACK:
                success = self._send_slack_notification(notification)
            elif notification.channel == NotificationChannel.TEAMS:
                success = self._send_teams_notification(notification)
            elif notification.channel == NotificationChannel.TELEGRAM:
                success = self._send_telegram_notification(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                success = self._send_webhook_notification(notification)
            else:
                error_message = f"Unsupported channel: {notification.channel}"
                
        except Exception as e:
            error_message = str(e)
            
        # Update notification status
        if success:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
        else:
            notification.status = NotificationStatus.FAILED
            notification.error_message = error_message
            notification.retry_count += 1
            
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return success
    
    def send_all_pending(self, db: Session) -> Dict[str, int]:
        """Send all pending notifications"""
        pending = self.get_pending_notifications(db)
        results = {"sent": 0, "failed": 0}
        
        for notification in pending:
            if self.send_notification(db, notification.id):
                results["sent"] += 1
            else:
                results["failed"] += 1
                
        return results
    
    def _apply_template(self, template_str: str, context_data: Dict[str, Any]) -> str:
        """Apply context data to a template string"""
        # Convert nested dictionaries to dot notation for template
        flat_context = self._flatten_dict(context_data)
        
        # Apply template
        template = Template(template_str)
        return template.safe_substitute(flat_context)
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionaries for template substitution"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _send_discord_notification(self, notification: Notification) -> bool:
        """Send a notification to Discord"""
        webhook_url = notification.recipient
        
        # Check if we have rich format data
        if notification.data and "rich_format" in notification.data:
            payload = notification.data["rich_format"]
        else:
            # Create a basic embed
            payload = {
                "embeds": [{
                    "title": notification.title,
                    "description": notification.message,
                    "color": 3447003  # Blue color
                }]
            }
            
        # Send the webhook
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 204
    
    def _send_slack_notification(self, notification: Notification) -> bool:
        """Send a notification to Slack"""
        webhook_url = notification.recipient
        
        # Check if we have rich format data
        if notification.data and "rich_format" in notification.data:
            payload = notification.data["rich_format"]
        else:
            # Create a basic message
            payload = {
                "text": notification.title,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": notification.message
                        }
                    }
                ]
            }
            
        # Send the webhook
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 200
    
    def _send_teams_notification(self, notification: Notification) -> bool:
        """Send a notification to Microsoft Teams"""
        webhook_url = notification.recipient
        
        # Create a basic card
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": notification.title,
            "sections": [{
                "activityTitle": notification.title,
                "text": notification.message
            }]
        }
            
        # Send the webhook
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 200
    
    def _send_telegram_notification(self, notification: Notification) -> bool:
        """Send a notification to Telegram"""
        # Telegram requires a bot token and chat ID
        # Format: "bot_token:chat_id"
        if ":" not in notification.recipient:
            return False
            
        bot_token, chat_id = notification.recipient.split(":", 1)
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"{notification.title}\n\n{notification.message}",
            "parse_mode": "Markdown"
        }
            
        # Send the message
        response = requests.post(url, json=payload)
        return response.status_code == 200
    
    def _send_webhook_notification(self, notification: Notification) -> bool:
        """Send a notification to a generic webhook"""
        webhook_url = notification.recipient
        
        # Create a generic payload
        payload = {
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": notification.data
        }
            
        # Send the webhook
        response = requests.post(webhook_url, json=payload)
        return 200 <= response.status_code < 300