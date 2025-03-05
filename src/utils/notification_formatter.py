from typing import Dict, Any, Optional
import json
from string import Template

def format_notification(template_str: str, context_data: Dict[str, Any]) -> str:
    """
    Format a notification using a template string and context data
    
    Args:
        template_str: Template string with placeholders
        context_data: Dictionary of context data
        
    Returns:
        Formatted notification text
    """
    # Flatten nested dictionaries for template substitution
    flat_context = _flatten_dict(context_data)
    
    # Apply template
    template = Template(template_str)
    return template.safe_substitute(flat_context)

def format_rich_notification(template_data: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a rich notification (e.g., for Discord, Slack) using a template and context data
    
    Args:
        template_data: Template data structure with placeholders
        context_data: Dictionary of context data
        
    Returns:
        Formatted rich notification data
    """
    # Convert template to JSON string
    template_str = json.dumps(template_data)
    
    # Format the template string
    formatted_str = format_notification(template_str, context_data)
    
    # Convert back to dictionary
    try:
        return json.loads(formatted_str)
    except json.JSONDecodeError:
        # If there's an error, return the original template
        return template_data

def _flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten nested dictionaries for template substitution
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for nested dictionaries
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, str(v) if v is not None else ""))
    return dict(items)