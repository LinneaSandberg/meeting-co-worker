"""
Integration modules for GitHub and Google Calendar.
"""

from .github_integration import (
    create_github_issue,
    format_action_item_issue,
    format_question_issue,
    check_github_config
)

from .calendar_integration import (
    create_calendar_event,
    format_question_event,
    extract_emails_from_question,
    check_calendar_config
)

__all__ = [
    'create_github_issue',
    'format_action_item_issue',
    'format_question_issue',
    'check_github_config',
    'create_calendar_event',
    'format_question_event',
    'extract_emails_from_question',
    'check_calendar_config'
]
