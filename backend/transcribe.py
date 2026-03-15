"""
Meeting Copilot - Transcription Module
Transcribes meeting audio using ElevenLabs Scribe v2 and extracts
decisions, action items, and open questions using Claude.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import anthropic
from logging_config import get_transcribe_logger

load_dotenv()

# Initialize logger
logger = get_transcribe_logger()

# Initialize clients
elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

logger.info("Transcription module initialized")


def transcribe_audio(file_path: str) -> dict:
    """
    Transcribe an audio file using ElevenLabs Scribe v2.

    Args:
        file_path: Path to the audio file (mp3, wav, m4a, etc.)

    Returns:
        Transcription result with speaker diarization
    """
    logger.info(f"Starting ElevenLabs transcription: {file_path}")
    print(f"📝 Transcribing: {file_path}")

    try:
        with open(file_path, "rb") as audio_file:
            transcription = elevenlabs.speech_to_text.convert(
                file=audio_file,
                model_id="scribe_v2",           # Use Scribe v2 for best accuracy
                tag_audio_events=True,           # Tag laughter, applause, etc.
                language_code="eng",             # Set to None for auto-detection
                diarize=True,                    # Enable speaker identification
            )

        logger.info(f"ElevenLabs transcription completed successfully")
        print("✅ Transcription complete!")
        return transcription

    except Exception as e:
        logger.error(f"ElevenLabs API error: {str(e)}", exc_info=True)
        raise


def format_transcript_for_extraction(transcription) -> str:
    """
    Format the transcription into a readable format for Claude.
    """
    # The transcription object has a 'words' list with speaker info
    # We'll group by speaker turns
    
    if hasattr(transcription, 'text'):
        # Simple format if we just have text
        return transcription.text
    
    # If we have detailed word-level data with speakers
    formatted_lines = []
    current_speaker = None
    current_text = []
    
    if hasattr(transcription, 'words'):
        for word in transcription.words:
            speaker = getattr(word, 'speaker', 'Unknown')
            text = getattr(word, 'text', '')
            
            if speaker != current_speaker:
                if current_text:
                    formatted_lines.append(f"[Speaker {current_speaker}]: {' '.join(current_text)}")
                current_speaker = speaker
                current_text = [text]
            else:
                current_text.append(text)
        
        # Don't forget the last speaker's text
        if current_text:
            formatted_lines.append(f"[Speaker {current_speaker}]: {' '.join(current_text)}")
        
        return "\n\n".join(formatted_lines)
    
    # Fallback: return the raw text attribute if available
    return str(transcription)


def extract_meeting_insights(transcript: str) -> dict:
    """
    Use Claude to extract decisions, action items, and open questions
    from the meeting transcript.

    Args:
        transcript: The formatted meeting transcript

    Returns:
        Dictionary with decisions, action_items, open_questions, and summary
    """
    logger.info(f"Starting Claude insight extraction (transcript length: {len(transcript)} chars)")
    print("🤖 Extracting insights with Claude...")
    
    extraction_prompt = f"""Analyze this meeting transcript and extract the following:

1. **Decisions Made**: Concrete decisions the team agreed on
2. **Action Items**: Tasks that need to be done, with the owner if mentioned (e.g., "Jake will set up the repo")
3. **Open Questions**: Unresolved questions or topics that need follow-up
4. **Brief Summary**: 2-3 sentence summary of what the meeting was about

Return your response as JSON with this exact structure:
{{
    "decisions": [
        {{"decision": "description", "context": "why/when it was decided"}}
    ],
    "action_items": [
        {{"task": "description", "owner": "person name or null", "deadline": "if mentioned or null"}}
    ],
    "open_questions": [
        {{"question": "description", "context": "why it matters"}}
    ],
    "summary": "Brief meeting summary"
}}

TRANSCRIPT:
{transcript}
"""

    try:
        logger.debug("Calling Anthropic API for insight extraction")
        message = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": extraction_prompt}
            ]
        )
        logger.info(f"Anthropic API call successful (usage: {message.usage.input_tokens} in, {message.usage.output_tokens} out)")

    except Exception as e:
        logger.error(f"Anthropic API error: {str(e)}", exc_info=True)
        raise

    # Parse the JSON response
    response_text = message.content[0].text

    # Try to extract JSON from the response
    import json
    try:
        # Handle case where Claude wraps in ```json blocks
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0]
        else:
            json_str = response_text

        insights = json.loads(json_str.strip())
        logger.info(f"Insights extracted: {len(insights.get('decisions', []))} decisions, "
                   f"{len(insights.get('action_items', []))} action items, "
                   f"{len(insights.get('open_questions', []))} questions")
        print("✅ Insights extracted!")
        return insights
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON from Claude response: {str(e)}")
        print("⚠️  Could not parse JSON, returning raw response")
        return {"raw_response": response_text}


def process_meeting(audio_path: str, on_progress=None) -> dict:
    """
    Full pipeline: transcribe audio and extract insights.

    Args:
        audio_path: Path to the meeting audio file
        on_progress: Optional callback function called with step name
                     ('transcribing', 'extracting', 'complete')

    Returns:
        Dictionary with transcript and extracted insights
    """
    # Step 1: Transcribe
    if on_progress:
        on_progress("transcribing")
    transcription = transcribe_audio(audio_path)

    # Step 2: Format transcript
    formatted_transcript = format_transcript_for_extraction(transcription)

    # Step 3: Extract insights
    if on_progress:
        on_progress("extracting")
    insights = extract_meeting_insights(formatted_transcript)

    if on_progress:
        on_progress("complete")

    return {
        "transcript": formatted_transcript,
        "insights": insights
    }


def print_insights(insights: dict):
    """Pretty print the extracted insights."""
    print("\n" + "="*60)
    print("📋 MEETING INSIGHTS")
    print("="*60)
    
    if "summary" in insights:
        print(f"\n📝 Summary:\n{insights['summary']}")
    
    if "decisions" in insights and insights["decisions"]:
        print("\n✅ Decisions Made:")
        for d in insights["decisions"]:
            print(f"  • {d['decision']}")
            if d.get('context'):
                print(f"    └─ {d['context']}")
    
    if "action_items" in insights and insights["action_items"]:
        print("\n📌 Action Items:")
        for item in insights["action_items"]:
            owner = f" (@{item['owner']})" if item.get('owner') else ""
            deadline = f" [Due: {item['deadline']}]" if item.get('deadline') else ""
            print(f"  • {item['task']}{owner}{deadline}")
    
    if "open_questions" in insights and insights["open_questions"]:
        print("\n❓ Open Questions:")
        for q in insights["open_questions"]:
            print(f"  • {q['question']}")
            if q.get('context'):
                print(f"    └─ {q['context']}")
    
    print("\n" + "="*60)


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <path_to_audio_file>")
        print("\nExample: python transcribe.py meeting.mp3")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    if not Path(audio_file).exists():
        print(f"❌ File not found: {audio_file}")
        sys.exit(1)
    
    result = process_meeting(audio_file)
    print_insights(result["insights"])
