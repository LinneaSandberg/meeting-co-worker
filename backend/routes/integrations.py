from fastapi import APIRouter, HTTPException, Request

from integrations import check_github_config, check_calendar_config
from services.integration_service import process_integrations
from logging_config import get_app_logger

logger = get_app_logger()

router = APIRouter()


@router.get('/integration-status')
async def integration_status():
    """Check which integrations are configured and available."""
    logger.debug("Checking integration status")

    github_config = check_github_config()
    calendar_config = check_calendar_config()

    logger.info(f"Integration status - GitHub: {github_config['enabled']}, Calendar: {calendar_config['enabled']}")

    return {
        'github_enabled': github_config['enabled'],
        'github_repo': github_config.get('repo'),
        'calendar_enabled': calendar_config['enabled'],
        'calendar_type': calendar_config.get('calendar_type')
    }


@router.post('/create-integrations')
async def create_integrations(request: Request):
    """Handle creation of GitHub issues and Google Calendar events."""
    logger.info("Received create-integrations request")

    data = await request.json()

    if not data:
        raise HTTPException(status_code=400, detail='No data provided')

    action_items = data.get('action_items', [])
    open_questions = data.get('open_questions', [])
    logger.info(f"Processing {len(action_items)} action items, {len(open_questions)} questions")

    results = process_integrations(action_items, open_questions)

    any_success = (
        any(item.get('url') for item in results['github_issues']) or
        any(event.get('url') for event in results['calendar_events'])
    )

    github_success = sum(1 for item in results['github_issues'] if item.get('url'))
    github_failed = len(results['github_issues']) - github_success
    calendar_success = sum(1 for event in results['calendar_events'] if event.get('url'))
    calendar_failed = len(results['calendar_events']) - calendar_success

    logger.info(
        f"Integration results - GitHub: {github_success} created, {github_failed} failed; "
        f"Calendar: {calendar_success} created, {calendar_failed} failed"
    )

    return {
        'success': any_success,
        'results': results
    }
