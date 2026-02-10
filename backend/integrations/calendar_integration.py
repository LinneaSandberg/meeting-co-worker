"""
Google Calendar Integration Module
Creates calendar events from meeting open questions.
"""

import os
import re
import sys
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import get_calendar_logger

logger = get_calendar_logger()

# Scopes required for calendar access
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service():
    """
    Get authenticated Google Calendar service.
    Handles OAuth2 flow and token refresh.

    Returns:
        Google Calendar service object or None if auth fails
    """
    creds = None
    token_path = "token.json"
    credentials_path = os.getenv("GOOGLE_OAUTH_CREDENTIALS_PATH", "credentials.json")

    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        logger.error(f"Google OAuth credentials not found at: {credentials_path}")
        return None, "Google OAuth credentials not found. Add credentials.json to project root."

    # Load existing token if available
    if os.path.exists(token_path):
        logger.debug("Loading existing Google OAuth token")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired token
            try:
                logger.info("Refreshing expired Google OAuth token")
                creds.refresh(Request())
                logger.info("Google OAuth token refreshed successfully")
            except Exception as e:
                logger.error(f"Failed to refresh Google OAuth token: {str(e)}", exc_info=True)
                return None, f"Failed to refresh token: {str(e)}"
        else:
            # Run OAuth flow
            try:
                logger.info("Starting Google OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Google OAuth flow completed successfully")
            except Exception as e:
                logger.error(f"Google OAuth flow failed: {str(e)}", exc_info=True)
                return None, f"OAuth flow failed: {str(e)}"

        # Save credentials for future use
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        logger.debug("Saved Google OAuth token to file")

    try:
        service = build('calendar', 'v3', credentials=creds)
        logger.debug("Google Calendar service built successfully")
        return service, None
    except Exception as e:
        logger.error(f"Failed to build Google Calendar service: {str(e)}", exc_info=True)
        return None, f"Failed to build calendar service: {str(e)}"


def create_calendar_event(
    summary: str,
    description: str,
    attendees: Optional[List[str]] = None,
    duration_minutes: int = 30
) -> dict:
    """
    Create a Google Calendar event.

    Args:
        summary: Event title
        description: Event details
        attendees: List of email addresses
        duration_minutes: Event duration (default 30 min)

    Returns:
        dict with 'success', 'event_url', 'event_id', or 'error'
    """
    logger.info(f"Creating calendar event: {summary[:50]}...")

    # Get calendar service
    service, error = get_calendar_service()
    if error:
        logger.error(f"Failed to get calendar service: {error}")
        return {
            "success": False,
            "error": error
        }

    # Get calendar ID (default to primary)
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    # Schedule event 1 week in the future
    start_time = datetime.now() + timedelta(days=7)
    start_time = start_time.replace(hour=14, minute=0, second=0, microsecond=0)  # 2 PM

    end_time = start_time + timedelta(minutes=duration_minutes)

    # Format event data
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'UTC',
        },
    }

    # Add attendees if provided
    if attendees:
        event['attendees'] = [{'email': email} for email in attendees if email]

    try:
        # Create event
        logger.debug(f"Inserting event into calendar: {calendar_id}")
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='all' if attendees else 'none'
        ).execute()

        logger.info(f"Calendar event created: {created_event.get('id')} - {created_event.get('htmlLink')}")
        return {
            "success": True,
            "event_url": created_event.get('htmlLink'),
            "event_id": created_event.get('id'),
            "error": None
        }

    except HttpError as e:
        # Handle specific HTTP errors
        if e.resp.status == 401:
            error_msg = "Calendar authentication failed. Please complete OAuth flow."
            logger.error("Google Calendar auth failed (401)")
        elif e.resp.status == 403:
            error_msg = "Calendar access denied. Check permissions in Google Cloud Console."
            logger.error("Google Calendar access denied (403)")
        elif e.resp.status == 404:
            error_msg = f"Calendar not found: {calendar_id}"
            logger.error(f"Google Calendar not found (404): {calendar_id}")
        else:
            error_msg = f"Calendar API error: {e.error_details if hasattr(e, 'error_details') else str(e)}"
            logger.error(f"Google Calendar API error ({e.resp.status}): {error_msg}")

        return {
            "success": False,
            "error": error_msg
        }

    except Exception as e:
        logger.error(f"Unexpected error creating calendar event: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def extract_emails_from_question(question: str, context: Optional[str] = None) -> List[str]:
    """
    Attempt to extract email addresses from question and context.
    This is a simple implementation that looks for email patterns.

    Args:
        question: The open question text
        context: Optional context that might mention people

    Returns:
        list of email addresses
    """
    # Combine question and context
    text = question
    if context:
        text += " " + context

    # Simple email regex pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)

    return list(set(emails))  # Remove duplicates


def format_question_event(question: str, context: Optional[str] = None) -> tuple:
    """
    Format an open question as a calendar event.

    Args:
        question: The open question text
        context: Optional context about why it matters

    Returns:
        tuple of (summary, description, attendees)
    """
    # Create event summary (title)
    summary = f"Discussion: {question[:100]}"  # Limit to 100 chars

    # Create event description
    description_parts = [
        "Meeting Follow-up Discussion",
        "",
        f"**Question:** {question}",
    ]

    if context:
        description_parts.append(f"\n**Context:** {context}")

    description_parts.extend([
        "",
        "---",
        "*This event was created from a meeting transcription by Meeting Copilot.*",
        "",
        "Please use this time to discuss and resolve the open question."
    ])

    description = "\n".join(description_parts)

    # Extract attendees
    attendees = extract_emails_from_question(question, context)

    return summary, description, attendees


def check_calendar_config() -> dict:
    """
    Check if Google Calendar integration is properly configured.

    Returns:
        dict with 'enabled', 'calendar_type', and optional 'error'
    """
    credentials_path = os.getenv("GOOGLE_OAUTH_CREDENTIALS_PATH", "credentials.json")

    if not os.path.exists(credentials_path):
        logger.debug("Google Calendar not configured (credentials.json not found)")
        return {
            "enabled": False,
            "calendar_type": None,
            "error": "Google OAuth credentials not found. Add credentials.json to project root."
        }

    # Check if we have a valid token
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            if creds and creds.valid:
                logger.debug("Google Calendar integration verified (valid token)")
                return {
                    "enabled": True,
                    "calendar_type": "oauth",
                    "error": None
                }
        except Exception as e:
            logger.warning(f"Error reading token.json: {str(e)}")

    # Credentials exist but no valid token
    logger.debug("Google Calendar credentials exist but OAuth flow not completed")
    return {
        "enabled": False,
        "calendar_type": "oauth",
        "error": "OAuth flow not completed. Create an event to authenticate."
    }
