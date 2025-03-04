import os
import secrets
from datetime import timedelta

# Build paths inside the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Secret key for secure sessions (generate a random one)
SECRET_KEY = 'your-secret-key-here'  # Change this to a secure secret key

# Flask-WTF settings
WTF_CSRF_ENABLED = True

# Upload settings
UPLOAD_FOLDER_RESUMES = os.path.join(BASE_DIR, 'app', 'uploads', 'resumes')
UPLOAD_FOLDER_JOB_DESCRIPTIONS = os.path.join(BASE_DIR, 'app', 'uploads', 'job_descriptions')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

# SQLite database settings
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:your_password@localhost/resume_analyzer'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Debug settings
DEBUG = True

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}