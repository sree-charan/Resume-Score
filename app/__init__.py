import os
import sys

# Add parent directory to path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create essential directories for the application
def init_app_directories():
    """Initialize application directories if they don't exist"""
    # Create upload directories
    os.makedirs(os.path.join('app', 'uploads', 'resumes'), exist_ok=True)
    os.makedirs(os.path.join('app', 'uploads', 'job_descriptions'), exist_ok=True)
    
    # Create JSON storage directory
    os.makedirs(os.path.join('app', 'data'), exist_ok=True)
    
    # Create other required directories
    os.makedirs(os.path.join('app', 'templates', 'errors'), exist_ok=True)
    os.makedirs(os.path.join('app', 'static', 'css'), exist_ok=True)
    os.makedirs(os.path.join('app', 'static', 'js'), exist_ok=True)
    os.makedirs(os.path.join('app', 'static', 'img'), exist_ok=True)
    os.makedirs(os.path.join('app', 'utils'), exist_ok=True)
    os.makedirs(os.path.join('app', 'models'), exist_ok=True)
    
    print("Application directories initialized successfully!")

if __name__ == "__main__":
    init_app_directories()