import os
from taipy.gui import Gui

# Simple test page
test_page = """
# CCPM Task Manager Test Page

This is a simple test page to verify that Taipy is working correctly.

<|{message}|text|>

<|Click Me|button|on_action=on_button_click|>
"""

# Initialize state variables
message = "Hello, World!"

# Define callback functions
def on_button_click(state):
    state.message = "Button clicked!"

# Create the GUI
gui = Gui(pages={"/": test_page})

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 50725))
    
    # Run the GUI
    gui.run(title="CCPM Task Manager Test", 
            dark_mode=True,
            host="0.0.0.0", 
            port=port,
            debug=True,
            allow_iframe=True,
            cors_policy="*")