import os
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from transcribe import process_meeting
from integrations import (
    check_github_config,
    check_calendar_config,
    create_github_issue,
    format_action_item_issue,
    format_question_issue,
    create_calendar_event,
    format_question_event
)
from logging_config import get_app_logger

# Initialize logger
logger = get_app_logger()

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'mp4', 'avi', 'mov'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process the meeting."""
    logger.info("Received file upload request")

    # Check if file was uploaded
    if 'file' not in request.files:
        logger.warning("Upload request missing file")
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    # Check if file was selected
    if file.filename == '':
        logger.warning("Upload request with empty filename")
        return jsonify({'error': 'No file selected'}), 400

    # Validate file type
    if not allowed_file(file.filename):
        logger.warning(f"Invalid file type attempted: {file.filename}")
        return jsonify({'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"File saved: {filename} ({os.path.getsize(filepath)} bytes)")

        # Process the meeting
        logger.info(f"Starting transcription for: {filename}")
        result = process_meeting(filepath)
        logger.info(f"Transcription completed for: {filename}")

        # Clean up uploaded file
        os.remove(filepath)
        logger.debug(f"Cleaned up temporary file: {filepath}")

        # Return results
        return jsonify({
            'success': True,
            'transcript': result['transcript'],
            'insights': result['insights']
        })

    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}", exc_info=True)

        # Clean up file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"Cleaned up file after error: {filepath}")

        # Return error (don't expose internal details)
        error_message = str(e)
        if 'API' in error_message or 'key' in error_message.lower():
            error_message = 'API error. Please check your API keys in .env file.'

        return jsonify({'error': error_message}), 500


@app.route('/integration-status', methods=['GET'])
def integration_status():
    """Check which integrations are configured and available."""
    logger.debug("Checking integration status")

    github_config = check_github_config()
    calendar_config = check_calendar_config()

    logger.info(f"Integration status - GitHub: {github_config['enabled']}, Calendar: {calendar_config['enabled']}")

    return jsonify({
        'github_enabled': github_config['enabled'],
        'github_repo': github_config.get('repo'),
        'calendar_enabled': calendar_config['enabled'],
        'calendar_type': calendar_config.get('calendar_type')
    })


@app.route('/create-integrations', methods=['POST'])
def create_integrations():
    """Handle creation of GitHub issues and Google Calendar events."""
    logger.info("Received create-integrations request")

    data = request.json

    if not data:
        logger.warning("Create-integrations request with no data")
        return jsonify({'error': 'No data provided'}), 400

    action_items = data.get('action_items', [])
    open_questions = data.get('open_questions', [])
    logger.info(f"Processing {len(action_items)} action items, {len(open_questions)} questions")

    results = {
        'github_issues': [],
        'calendar_events': []
    }

    # Process action items
    for item in action_items:
        if item.get('create_github'):
            # Format and create GitHub issue for action item
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

    # Process open questions
    for question in open_questions:
        # Create GitHub issue if requested
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

        # Create calendar event if requested
        if question.get('create_calendar'):
            summary, description, attendees = format_question_event(
                question=question['question'],
                context=question.get('context')
            )

            # Get duration from env or use default
            duration = int(os.getenv('DEFAULT_MEETING_DURATION', 30))

            result = create_calendar_event(
                summary=summary,
                description=description,
                attendees=attendees,
                duration_minutes=duration
            )

            results['calendar_events'].append({
                'type': 'open_question',
                'title': question['question'],
                'url': result.get('event_url'),
                'event_id': result.get('event_id'),
                'attendees': attendees,
                'error': result.get('error')
            })

    # Check if any operation succeeded
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

    return jsonify({
        'success': any_success,
        'results': results
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Meeting Copilot Web UI")
    print("="*60)
    print("\nOpen your browser to: http://localhost:5001")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(debug=True, port=5001)
