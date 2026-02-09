# YTT - YouTube Transcript Translator

A simple tool for learning languages through YouTube videos.

## What it does

- Fetches transcripts from YouTube videos via yt-dlp
- Translates them using LibreTranslate (self-hosted, no API keys)
- Shows original and translation side-by-side with synchronized scrolling
- Saves transcripts in per-video folders (`transcripts/{video_id}/`)
- Mobile fullscreen mode with 50/50 split-screen and paragraph snapping
- Desktop fullscreen with paragraph linking and hover highlighting
- Translation history with search and review

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit 5 (runes), Carbon Design System v0.99.1 |
| Backend | FastAPI, yt-dlp |
| Translation | LibreTranslate |
| Storage | JSON files (no database) |
| Deployment | Single Docker container, multi-stage build |

## Quick Start

```bash
git clone https://github.com/keesfluitman/ytt.git
cd ytt
docker build -t ytt:latest .
docker compose up -d
```

Open `http://localhost:8000`. First startup is slow while LibreTranslate downloads language models.

**Requirements:** Docker, ~4GB RAM, ~10GB disk.

### Using your own LibreTranslate

Set `LIBRETRANSLATE_URL` in your `.env` or `docker-compose.yml` and run just the YTT container.

## Development

```bash
# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && uvicorn main:app --reload

# Frontend
cd frontend && pnpm install && pnpm dev

# LibreTranslate
docker run -d -p 5000:5000 libretranslate/libretranslate
```

Frontend dev server: `http://localhost:5173`

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/youtube/fetch` | POST | Fetch and translate YouTube transcript |
| `/api/translate` | POST | Translate text (supports entry_id for updating existing entries) |
| `/api/history` | GET | List translation history |
| `/api/history/{id}` | GET/PUT/DELETE | Manage individual entries |
| `/api/version` | GET | Build info (version, date, commit) |
| `/health` | GET | Health check |

## Project Structure

```
ytt/
├── frontend/          # SvelteKit 5 SPA
│   └── src/routes/    # Pages: translate, history, view/[id], settings
├── backend/           # FastAPI
│   └── app/
│       ├── api/       # Endpoints (translate, youtube, history)
│       └── services/  # Business logic (translator, youtube, history)
├── Dockerfile         # Multi-stage build (Node.js -> Python)
└── docker-compose.yml
```

## License

MIT

---

Built for learning languages, one YouTube video at a time.
