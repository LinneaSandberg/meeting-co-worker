from config import DEFAULT_MEETING_DURATION
from integrations import (
    create_github_issue,
    format_action_item_issue,
    format_question_issue,
    create_calendar_event,
    format_question_event,
)


def process_integrations(action_items: list, open_questions: list) -> dict:
    """Create GitHub issues and calendar events from meeting results."""
    results = {
        'github_issues': [],
        'calendar_events': []
    }

    for item in action_items:
        if item.get('create_github'):
            title, body = format_action_item_issue(
                task=item['task'],
                owner=item.get('owner'),
                deadline=item.get('deadline')
            )
            result = create_github_issue(title, body, issue_type="action_item")
            results['github_issues'].append({
                'type': 'action_item',
                'title': item['task'],
                'url': result.get('issue_url'),
                'issue_number': result.get('issue_number'),
                'error': result.get('error')
            })

    for question in open_questions:
        if question.get('create_github'):
            title, body = format_question_issue(
                question=question['question'],
                context=question.get('context')
            )
            result = create_github_issue(title, body, issue_type="open_question")
            results['github_issues'].append({
                'type': 'open_question',
                'title': question['question'],
                'url': result.get('issue_url'),
                'issue_number': result.get('issue_number'),
                'error': result.get('error')
            })

        if question.get('create_calendar'):
            summary, description, attendees = format_question_event(
                question=question['question'],
                context=question.get('context')
            )
            result = create_calendar_event(
                summary=summary,
                description=description,
                attendees=attendees,
                duration_minutes=DEFAULT_MEETING_DURATION
            )
            results['calendar_events'].append({
                'type': 'open_question',
                'title': question['question'],
                'url': result.get('event_url'),
                'event_id': result.get('event_id'),
                'attendees': attendees,
                'error': result.get('error')
            })

    return results
