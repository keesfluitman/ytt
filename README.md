# YTT - YouTube Transcript Translator

A simple tool for learning languages through YouTube videos. 

## What is this?

YTT is a hobby project that does one thing: **helps you learn languages by making it easy to read YouTube transcripts alongside their translations**. 

That's it! No fancy features, no database - just JSON files storing your transcripts. It's a tool built for personal use that you might find handy too.

## Why use it?

If you're learning a language through YouTube videos (documentaries, talks, etc.), you've probably wanted to:
- See the transcript without YouTube's tiny subtitle box
- Have the translation right next to the original text
- Save interesting videos to review later
- Not rely on external services that might disappear

This tool does exactly that, nothing more, nothing less.

## Features

What it does:
- Fetches transcripts from YouTube videos
- Translates them using LibreTranslate (runs locally, no API keys!)
- Shows original and translation side-by-side
- Saves everything in JSON files (no database needed)
- Works on mobile too (paragraph-by-paragraph view)
- Has a fullscreen reading mode
- Remembers your translation history

## Installation

### Quick Start (Build from source)

Since there's no published Docker image yet, you'll need to build it yourself. Don't worry, it's straightforward:

1. Clone the repository:
```bash
git clone https://github.com/keesfluitman/ytt.git
cd ytt
```

2. Build the Docker image:
```bash
docker build -t ytt:latest .
```

3. Run with docker-compose:
```bash
cd production
cp .env.example .env  # Optional: adjust settings
docker compose up -d
```

4. Open `http://localhost:8000` in your browser

That's it! The first startup takes a bit longer as LibreTranslate downloads its language models.

### What you need
- Docker and Docker Compose
- About 4GB RAM (LibreTranslate needs this for language models)
- About 10GB disk space

### Using your own LibreTranslate

If you already run LibreTranslate somewhere:

1. Edit `production/.env`:
```env
LIBRETRANSLATE_URL=https://your-translate-server.com
```

2. Comment out the LibreTranslate service in `docker-compose.yml`

3. Run just YTT:
```bash
docker compose up -d ytt
```

## Development

Want to run it locally without Docker?

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

### LibreTranslate
```bash
docker run -d -p 5000:5000 libretranslate/libretranslate
```

Then open `http://localhost:5173` (frontend dev server)

### Project Structure
```
ytt/
├── frontend/          # SvelteKit 5 application
│   ├── src/
│   │   ├── routes/   # Page components
│   │   └── lib/      # Shared components
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/     # API endpoints
│   │   └── models/  # Data models
├── production/       # Production deployment files
│   ├── docker-compose.yml
│   └── .env.example
└── Dockerfile        # Single container build
```

### Tech Stack
- Frontend: SvelteKit 5 (with the new runes!)
- Backend: FastAPI
- UI: Carbon Design System (the v0.99 one, not the fancy new one)
- Translation: LibreTranslate
- Storage: JSON files in `data/` folder

## API Documentation

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/youtube/fetch` | POST | Fetch YouTube transcript |
| `/api/translate` | POST | Translate text |
| `/api/history` | GET | Get translation history |
| `/api/history` | POST | Save translation |
| `/api/history/{id}` | GET | Get specific translation |
| `/api/history/{id}` | PUT | Update translation |
| `/api/history/{id}` | DELETE | Delete translation |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:8000"]` |
| `LIBRETRANSLATE_URL` | LibreTranslate API URL | `http://libretranslate:5000` |

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Frontend: Follow Svelte 5 best practices with runes
- Backend: Follow PEP 8 for Python code
- Use Carbon Design System components where possible

## 🗺️ Roadmap

### Coming Soon
- [ ] **Timed Transcripts** - Preserve YouTube timestamps for video synchronization
- [ ] **Export Formats** - Download as SRT, VTT, TXT, PDF
- [ ] **LLM Integration** - Clean transcripts, generate summaries
- [ ] **Multiple Translation Engines** - Google, DeepL, OpenAI support
- [ ] **Batch Processing** - Translate multiple videos at once
- [ ] **API Access** - REST API for programmatic access

See [docs/todos.md](docs/todos.md) for the complete feature roadmap.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LibreTranslate](https://github.com/LibreTranslate/LibreTranslate) - Open-source translation API
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) - YouTube transcript fetching
- [Carbon Design System](https://carbondesignsystem.com/) - IBM's design system
- [SvelteKit](https://kit.svelte.dev/) - The web framework
- [FastAPI](https://fastapi.tiangolo.com/) - The API framework

## Support

- **Issues**: [GitHub Issues](https://github.com/keesfluitman/ytt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/keesfluitman/ytt/discussions)

---

Made for learning languages, one YouTube video at a time.