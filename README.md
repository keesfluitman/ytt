# YTT - YouTube Transcript Translator

<div align="center">

![YTT Logo](https://img.shields.io/badge/YTT-YouTube_Transcript_Translator-red?style=for-the-badge&logo=youtube)

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-5-FF3E00?style=flat-square&logo=svelte)](https://kit.svelte.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Carbon Design](https://img.shields.io/badge/Carbon_Design-v0.99-0F62FE?style=flat-square&logo=ibm)](https://carbondesignsystem.com/)
[![LibreTranslate](https://img.shields.io/badge/LibreTranslate-Integrated-4CAF50?style=flat-square)](https://github.com/LibreTranslate/LibreTranslate)

A modern, self-hosted web application for fetching, translating, and managing YouTube video transcripts.

[Features](#features) • [Quick Start](#quick-start) • [Installation](#installation) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

## 📺 Overview

YTT (YouTube Transcript Translator) is a powerful tool that allows you to:
- Fetch transcripts from any YouTube video
- Automatically translate them to your preferred language
- Edit and review translations side-by-side
- Manage your translation history
- Export transcripts in various formats (coming soon)

Perfect for researchers, content creators, language learners, and anyone who needs to work with multilingual video content.

## ✨ Features

### Core Functionality
- 🎬 **YouTube Integration** - Fetch transcripts from any public YouTube video
- 🌐 **Automatic Translation** - Powered by LibreTranslate (self-hosted, no API keys required)
- 📝 **Edit Mode** - Review and edit translations with synchronized paragraph scrolling
- 📚 **History Management** - Save, search, and manage all your translations
- 👁️ **View Modes** - Side-by-side or paragraph-by-paragraph viewing
- 📱 **Mobile Responsive** - Optimized for desktop, tablet, and mobile devices

### UI/UX Features
- 🎨 **Carbon Design System** - Professional IBM design language
- 🌙 **Dark/Light Mode** - (Coming soon)
- 🖥️ **Fullscreen Mode** - Distraction-free reading experience
- 🔗 **Paragraph Linking** - Synchronized scrolling between original and translation
- 📍 **Rail Navigation** - Space-efficient navigation that expands on hover

### Technical Features
- 🐳 **Docker Ready** - Single container deployment with all dependencies
- 🔒 **Privacy First** - Self-hosted solution, your data stays with you
- ⚡ **Fast & Efficient** - Built with SvelteKit 5 and FastAPI
- 🔄 **No API Keys** - Uses self-hosted LibreTranslate

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ytt.git
cd ytt
```

2. Copy the example environment file:
```bash
cp production/.env.example production/.env
```

3. Start the services:
```bash
cd production
docker compose up -d
```

4. Access YTT at `http://localhost:8000`

That's it! YTT and LibreTranslate are now running.

## 📦 Installation

### Prerequisites
- Docker and Docker Compose
- 4GB RAM minimum (for LibreTranslate models)
- 10GB disk space (for container images and translation models)

### Detailed Setup

1. **Clone and Configure**
```bash
git clone https://github.com/yourusername/ytt.git
cd ytt/production
cp .env.example .env
```

2. **Edit Configuration** (optional)
```bash
nano .env
# Adjust CORS_ORIGINS if needed for your domain
```

3. **Build and Deploy**
```bash
# Using the deployment script
./deploy.sh

# Or manually with docker compose
docker compose up -d
```

4. **Verify Installation**
```bash
# Check if services are running
docker compose ps

# View logs
docker compose logs -f
```

### Using External LibreTranslate

If you already have a LibreTranslate instance:

1. Edit `production/.env`:
```env
LIBRETRANSLATE_URL=https://translate.your-domain.com
```

2. Remove the LibreTranslate service from `docker-compose.yml`

3. Deploy only YTT:
```bash
docker compose up -d ytt
```

## 🛠️ Development

### Local Development Setup

1. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

2. **Frontend Setup**
```bash
cd frontend
pnpm install
pnpm dev
```

3. **LibreTranslate** (for translation features)
```bash
docker run -d -p 5000:5000 libretranslate/libretranslate
```

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
│   ├── deploy.sh
│   └── .env.example
└── docs/            # Documentation
```

### Technology Stack
- **Frontend**: SvelteKit 5, Carbon Design System v0.99
- **Backend**: FastAPI, Python 3.11+
- **Translation**: LibreTranslate
- **Container**: Docker, multi-stage builds
- **Database**: SQLite (local file storage)

## 📖 Documentation

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

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ytt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ytt/discussions)
- **Email**: your-email@example.com

---

<div align="center">

Made with ❤️ by the YTT Team

[Report Bug](https://github.com/yourusername/ytt/issues) • [Request Feature](https://github.com/yourusername/ytt/issues)

</div>