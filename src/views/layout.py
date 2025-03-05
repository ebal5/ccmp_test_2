from taipy.gui import Markdown

# Navigation bar
navbar = """
<|navbar|>
<|navbar-brand|>
CCPM Task Manager
<|navbar-brand|>

<|navbar-toggler|>

<|navbar-collapse|>
<|navitem|label=Dashboard|href=/|>
<|navitem|label=Tasks|href=/tasks|>
<|navitem|label=Projects|href=/projects|>
<|navitem|label=Time Tracking|href=/time_tracking|>
<|navitem|label=Buffer Management|href=/buffer_management|>
<|navitem|label=Settings|href=/settings|>
<|navbar-collapse|>
<|navbar|>
"""

# Page layout template
def create_page_layout(content: str) -> str:
    """
    Create a page layout with navigation and content
    
    Args:
        content: Page content
        
    Returns:
        Complete page layout
    """
    return f"""
{navbar}

<|container|>
{content}
<|container|>
"""