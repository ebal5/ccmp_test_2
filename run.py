import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app
from src.app import gui, Core

# Import database initialization
from src.database import init_db

# Initialize the database
init_db()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 50725))
    
    # Initialize Taipy Core
    Core().run()
    
    # Run the GUI
    gui.run(title="CCPM Task Manager", 
            dark_mode=True,
            host="0.0.0.0", 
            port=port,
            debug=True,
            allow_iframe=True,
            cors_policy="*")