import os

UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'mp4', 'avi', 'mov'}

JOB_TTL_SECONDS = 30 * 60  # 30 minutes
JOB_CLEANUP_INTERVAL = 60  # check every 60 seconds

DEFAULT_MEETING_DURATION = int(os.getenv('DEFAULT_MEETING_DURATION', 30))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
