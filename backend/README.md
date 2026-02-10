# Meeting Copilot - Transcription Module

Transcribe meeting audio and automatically extract decisions, action items, and open questions.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up API keys

Copy the example env file and add your keys:

```bash
cp .env.example .env
```

Then edit `.env` with your actual API keys:
- **ElevenLabs**: Get your key from https://elevenlabs.io/app/settings/api-keys
- **Anthropic**: Get your key from https://console.anthropic.com/

### 3. Run it

**Option A: Web UI (Recommended)**

```bash
python app.py
```

Then open your browser to: `http://localhost:5001`

Drag and drop your audio file into the browser!

**Option B: Command Line**

```bash
python transcribe.py path/to/your/meeting.mp3
```

## What it does

1. **Transcribes** your audio using ElevenLabs Scribe v2 (with speaker diarization)
2. **Extracts** key information using Claude:
   - Decisions made
   - Action items (with owners if mentioned)
   - Open questions
   - Brief summary

## Supported audio formats

MP3, WAV, M4A, FLAC, OGG, and most common audio/video formats.

## Example output

```
============================================================
📋 MEETING INSIGHTS
============================================================

📝 Summary:
Team discussed the MVP scope for the hackathon project and assigned initial tasks.

✅ Decisions Made:
  • Using Supabase for the database
    └─ Faster to set up than self-hosted Postgres
  • MVP will focus on Discord integration only

📌 Action Items:
  • Set up the GitHub repo (@Jake)
  • Create the database schema (@Sarah) [Due: Tomorrow]
  • Research Discord bot permissions (@Mike)

❓ Open Questions:
  • Do we need user authentication for the MVP?
    └─ Depends on whether we want persistent user data

============================================================
```

## Next steps

- [ ] Add output to Notion/Linear
- [ ] Add MCP integration for Claude to update boards directly
- [ ] Support real-time transcription (WebSocket API)
