"""
Logging configuration for Meeting Copilot backend.
Provides consistent logging across all modules.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create logs directory
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str, log_file: str = "app.log", level: int = logging.INFO) -> logging.Logger:
    """
    Create and configure a logger with both file and console handlers.

    Args:
        name: Logger name (typically __name__ of the module)
        log_file: Log file name (stored in logs/ directory)
        level: Logging level (default INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # File handler with rotation (max 5MB, keep 3 backups)
    file_handler = RotatingFileHandler(
        LOGS_DIR / log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if os.getenv("DEBUG") else logging.WARNING)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Pre-configured loggers for each module
def get_app_logger() -> logging.Logger:
    """Get logger for Flask app."""
    return setup_logger("meeting_copilot.app", "app.log")


def get_transcribe_logger() -> logging.Logger:
    """Get logger for transcription module."""
    return setup_logger("meeting_copilot.transcribe", "transcribe.log")


def get_github_logger() -> logging.Logger:
    """Get logger for GitHub integration."""
    return setup_logger("meeting_copilot.github", "integrations.log")


def get_calendar_logger() -> logging.Logger:
    """Get logger for Google Calendar integration."""
    return setup_logger("meeting_copilot.calendar", "integrations.log")
