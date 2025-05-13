# config.py
import os
from pathlib import Path

# Get the absolute path of the project's root directory
BASE_DIR = Path(__file__).resolve().parent

# Define paths relative to the base directory
UPLOAD_FOLDER = BASE_DIR / 'uploads'
OUTPUT_FOLDER = BASE_DIR / 'outputs'
MODEL_PATH = BASE_DIR / 'ml_model' / 'best.pt' # Path to your YOLOv8 model

# Ensure upload and output directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Allowed video extensions (adjust if needed)
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# Optional: Secret key for Flask sessions (important for production)
# You can generate a random key using os.urandom(24)
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-replace-me')

# Debug mode (set to False in production)
DEBUG = True

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS