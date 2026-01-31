# YTT - YouTube Transcript Translator

## 🚨 IMPORTANT: SVELTE 5 REQUIREMENT
**This project uses Svelte 5 with modern rune patterns.** 
- **DO NOT** use Svelte 4 legacy patterns like `$:` reactive statements
- **USE** Svelte 5 runes: `$state()`, `$derived()`, `$effect()`, `$props()`
- If you're not familiar with Svelte 5 syntax:
  - Check existing code patterns in `frontend/src/routes/+layout.svelte` for reference
  - Use the Svelte MCP server (`mcp__svelte__*` tools) to look up correct syntax
  - Run `svelte-autofixer` tool to validate your Svelte code

## 🎨 IMPORTANT: CARBON DESIGN SYSTEM USAGE
**This project uses Carbon Components Svelte v0.99.1 - Understand the limitations!**

### ⚠️ CRITICAL: Carbon v0.99.1 Uses Hardcoded CSS
**carbon-components-svelte v0.99.1 does NOT support CSS variables like Carbon v11!**
- ❌ CSS variables (--cds-spacing-*, --cds-ui-*) **DO NOT EXIST** in v0.99.1
- ✅ Use hardcoded pixel values that match Carbon's design system
- ✅ Carbon's white.css provides ALL typography, colors, and component styling
- ✅ Focus on using Carbon components, not CSS variables

### Before Writing ANY Custom CSS:
1. **FIRST** check `docs/carbon-reference/COMPONENT_CATALOG.md` for available components
2. **SECOND** check `docs/carbon-reference/USAGE_GUIDE.md` for implementation patterns  
3. **THIRD** check `docs/carbon-reference/COMPONENT_EXAMPLES.md` for copy-paste examples
4. **FOURTH** check `docs/carbon-reference/CSS_UTILITIES.md` for spacing values (but use hardcoded px!)

### Carbon Reference Documentation:
- **[Component Catalog](./docs/carbon-reference/COMPONENT_CATALOG.md)** - Complete list of 71+ components with descriptions
- **[Usage Guide](./docs/carbon-reference/USAGE_GUIDE.md)** - Best practices and common patterns
- **[Component Examples](./docs/carbon-reference/COMPONENT_EXAMPLES.md)** - Copy-paste ready code snippets
- **[CSS Utilities](./docs/carbon-reference/CSS_UTILITIES.md)** - Carbon spacing scale (use px values, not variables!)

### CSS Architecture Principles:
- ✅ **Minimal Custom CSS**: Only write CSS for app-specific features (fullscreen, paragraph linking, etc.)
- ✅ **Let Carbon Handle Styling**: Typography, colors, hover states, focus states all handled by white.css
- ✅ **Hardcoded Values**: Use `16px` not `var(--cds-spacing-05)` (which doesn't exist)
- ✅ **Component-First**: Use `Tile`, `Button`, `Grid` etc. instead of custom divs
- ✅ **Rail Navigation**: Use space-efficient rail SideNav instead of full-width sidebars

### Current CSS Implementation (Optimized):
- **~150 lines total CSS** (was 200+) - only for app-specific features
- **Fullscreen mode**: Custom layout for distraction-free reading
- **Paragraph linking**: Custom hover effects and synchronized scrolling
- **Responsive text areas**: Fixed-height scrollable containers
- **Rail navigation**: Minimal space usage (48px collapsed, expands on hover)

### Common Mistakes to AVOID:
- ❌ Using CSS variables (`var(--cds-*)`) → Use hardcoded values
- ❌ Setting text colors on headings → Carbon white.css handles this
- ❌ Custom spacing variables → Use hardcoded px values from Carbon scale
- ❌ Writing custom CSS for cards → Use `Tile` components
- ❌ Creating custom tables → Use `DataTable` with built-in features
- ❌ Custom grid/flexbox → Use `Grid`, `Row`, `Column` components
- ❌ Duplicate navigation → Use either HeaderNav OR SideNav, not both

### When Custom CSS IS Needed:
- ✅ App-specific features (fullscreen mode, paragraph linking)
- ✅ Layout constraints (scrollable areas, fixed heights)  
- ✅ Responsive adjustments for specific layouts
- ✅ Navigation enhancements (rail auto-open behavior)

## Current Architecture

### **All-in-One Container Approach**
Successfully implemented single Docker container serving both frontend and backend following the FastAPI + SPA pattern from [this blog post](https://davidmuraya.com/blog/serving-a-react-frontend-application-with-fastapi/).

### **Tech Stack**
- **Frontend**: SvelteKit 5 (using modern runes - NO legacy Svelte 4 patterns) with Carbon Design System, built as SPA
- **Backend**: FastAPI with custom `SPAStaticFiles` handler for client-side routing
- **Translation**: LibreTranslate service integration via Docker network
- **Deployment**: Single Docker image with multi-stage build

### **Key Components**

#### **Frontend (SvelteKit)**
- Location: `frontend/`
- Build output: Static files in `build/` directory
- API calls: Relative paths (`/api`) - same origin as backend
- Routing: Client-side SPA routing for `/history`, `/view/[id]`, etc.

#### **Backend (FastAPI)**
- Location: `backend/`
- Custom `SPAStaticFiles` class handles frontend routing (404s → index.html)
- API endpoints: `/api/translate`, `/api/youtube/fetch`, `/api/history`
- Health check: `/health`

#### **Docker Setup**
- **Dockerfile**: Multi-stage build (Node.js → Python)
- **Image**: `ytt:latest` (single container for frontend + backend)
- **Network**: Connected to `nginx` external network for LibreTranslate access
- **Port**: 8000 (exposed on local network only)

### **Deployment Architecture**

#### **Production Flow**
1. **Local Development**: `pnpm dev` (frontend) + `uvicorn main:app --reload` (backend)
2. **Build & Deploy**: `./docker-deploy.sh` builds and transfers image to Unraid
3. **Server**: Unraid runs container via Compose Manager
4. **Access**: `https://ytt.rappedoos.com` (nginx proxy) or `http://192.168.1.249:8000` (direct)

#### **Network Setup**
- **Local Network**: Container accessible at `192.168.1.249:8000`
- **Public Access**: `ytt.rappedoos.com` proxies all traffic to container
- **LibreTranslate**: Container-to-container via `http://libretranslate:5000`

## Current Status

### ✅ **Working**
- Frontend loads correctly at `ytt.rappedoos.com`
- SPA routing works for navigation (direct URL access and refresh)
- YouTube transcript fetching with automatic translation via LibreTranslate
- History page with edit/review functionality
- Translation API working correctly
- Health checks: `/health` endpoint functional
- LibreTranslate connectivity: Container-to-container communication working
- Docker deployment pipeline with automatic backups
- Proper UID/GID permissions for Unraid (99:99)
- Edit mode: Load history items in main route for reviewing/editing
- Session storage for passing translation data between pages
- **Modern Navigation**: Rail SideNav with responsive behavior and icon-based design
- **Optimized CSS**: Minimal custom styles, relies on Carbon v0.99.1's built-in styling
- **No Horizontal Scroll**: Proper column sizing accounts for navigation space
- **Fullscreen Mode**: Centered layout with max-width for readability on large displays
- **Paragraph Linking**: Synchronized scrolling and hover highlighting in view mode

### 🔧 **Configuration Files**

#### **Local (`docker-compose.yml`)**
```yaml
services:
  ytt:
    image: ytt:latest
    container_name: ytt
    environment:
      - CORS_ORIGINS=["*"]  # JSON array format
```

#### **Server (Unraid Compose Manager)**
- **Location**: `/boot/config/plugins/compose.manager/projects/ytt/docker-compose.yml`
- **Important**: Unraid's Compose Manager stores all project files in this directory
```yaml
services:
  ytt:
    image: ytt:latest
    container_name: ytt
    environment:
      - CORS_ORIGINS=["*"]  # JSON array format
    networks:
      - nginx  # External network for LibreTranslate access
    ports:
      - "192.168.1.249:8000:8000"
```

## Completed Features (Latest Session - Jan 2026)

### **Previous Features**
1. **Automatic Translation**: YouTube transcripts automatically translated when fetched if target language differs from source
2. **Edit/Review Mode**: History items can be opened in main page for editing/reviewing
3. **Fixed SPA Routing**: Direct URL access and page refresh work using `StarletteHTTPException` 
4. **Fixed Permissions**: Container runs as UID/GID 99 matching Unraid's nobody:users
5. **Unified Service Naming**: Docker service renamed from `ytt-backend` to `ytt` for consistency
6. **Corrected nginx proxy config**: Updated container name references
7. **Migrated to Svelte 5**: All components now use modern Svelte 5 runes (`$state`, `$derived`, `$effect`) - NO legacy `$:` patterns
8. **Paragraph Linking**: Client-side paragraph synchronization with hover highlighting and visual indicators in view mode

### **Mobile Responsiveness Implementation (Current Session)**
9. **Responsive Navigation**: Complete mobile navigation using Carbon UIShell
   - Implemented `Header` with automatic hamburger menu detection
   - Added `SideNav` with responsive breakpoints (< 1056px)
   - Proper state synchronization between Header and SideNav
   - Desktop: Horizontal navigation, Mobile: Hamburger + slide-out navigation

10. **Mobile-Optimized History Page**: Responsive data display
   - **Desktop**: Full DataTable with OverflowMenu for actions
   - **Mobile**: Card-based layout with touch-optimized UI
   - **Responsive breakpoint**: 768px switching between layouts
   - **Features**: Search functionality works on both layouts, all actions preserved

11. **Carbon Grid System Integration**: Responsive layout foundation
   - Using Carbon's `Grid`, `Row`, `Column` components
   - Consistent responsive breakpoints across the app
   - Better mobile spacing and layout behavior

12. **Mobile Paragraph-by-Paragraph View**: Enhanced reading experience
   - **Mobile UX**: Alternating original → translation blocks for natural reading flow
   - **Desktop**: Traditional side-by-side view with synchronized scrolling
   - **Smart Toggle**: Auto-enables paragraph view on mobile (< 768px), manual toggle on desktop
   - **Features**: Paired paragraph display, visual distinction with color coding, responsive scaling
   - **Compatibility**: Works with existing paragraph linking and fullscreen modes

13. **Carbon Design System Architecture Optimization**: Clean CSS implementation
   - **Discovery**: Carbon v0.99.1 uses hardcoded CSS, not CSS variables like v11
   - **CSS Minimization**: Reduced custom CSS to only app-specific features (fullscreen, paragraph linking)
   - **Layout Fixes**: Resolved horizontal scrolling by adjusting Grid column spans for SideNav
   - **Fullscreen Enhancement**: Centered layout on large displays with 1920px max-width for readability
   - **Documentation**: Updated CSS_UTILITIES.md to reflect v0.99.1 reality and limitations

14. **Navigation System Redesign**: Modern rail-based navigation
   - **Rail SideNav**: Converted to space-efficient rail variant (48px collapsed, ~256px expanded)
   - **Icon-Based Navigation**: Added proper Carbon icons (Language, RecentlyViewed, Settings)
   - **Removed Duplicate Navigation**: Eliminated HeaderNav items, using only rail SideNav
   - **Auto-responsive**: Opens on desktop (≥1056px), hamburger menu on mobile
   - **Better UX**: Hover to expand, clean modern interface, more screen space for content

## Development Commands

```bash
# Build and deploy
./docker-deploy.sh

# Check logs
ssh root@192.168.1.249 "docker logs ytt -f"

# Restart on server (Unraid Compose Manager location)
ssh root@192.168.1.249 "docker compose -f /boot/config/plugins/compose.manager/projects/ytt/docker-compose.yml restart ytt"

# Full redeploy on server
ssh root@192.168.1.249 "cd /boot/config/plugins/compose.manager/projects/ytt && docker compose down && docker compose up -d"
```

## Previously Fixed Issues
1. **SPA Routing**: Fixed using `StarletteHTTPException` instead of `HTTPException` in SPAStaticFiles
2. **Container Permissions**: Fixed by using numeric UID/GID 99 directly instead of 'nobody' username
3. **Service Naming**: Unified docker-compose service name from `ytt-backend` to `ytt`
4. **Translation Storage**: Fixed transcripts and translations stored separately - now combined
5. **CORS Configuration**: Fixed JSON array format for CORS_ORIGINS environment variable
6. **LibreTranslate URL**: Fixed container-to-container URL from localhost to service name
7. **Svelte 4 Legacy Code**: Migrated all components from Svelte 4 patterns (`$:`) to Svelte 5 runes

## Next Features TODO

For a comprehensive list of planned features, see [docs/todos.md](./docs/todos.md)

### Priority Features:

1. **Timed Transcript Playback** ⏱️
   - See detailed plan: [docs/plans/timed-transcript-playback.md](./docs/plans/timed-transcript-playback.md)
   - Preserve VTT timestamps from YouTube
   - Add playback controls with synchronized highlighting
   - Enable click-to-jump navigation
   - Export as SRT/VTT subtitle files

2. **LLM Integration for Text Processing** 🤖
   - "Clean Text" button to remove filler words
   - "Summarize" button for AI-powered summarization
   - Support multiple LLM providers:
     - Claude API (official)
     - Local Claude via OAuth (personal use)
     - OpenAI, Ollama, custom endpoints
   - Model selection and cost estimation

3. **Enhanced Translation Features** 🌐
   - Multiple translation providers
   - Quality scoring and comparison
   - Custom glossaries
   - Translation memory

## File Structure
```
ytt/
├── docs/                  # Documentation
│   ├── todos.md          # Comprehensive TODO list
│   └── plans/            # Feature planning documents
│       └── timed-transcript-playback.md
├── frontend/              # SvelteKit 5 app
│   ├── src/
│   ├── package.json
│   └── svelte.config.js  # SPA with fallback: 'index.html'
├── backend/               # FastAPI app
│   ├── app/
│   ├── main.py           # SPAStaticFiles with StarletteHTTPException
│   └── requirements.txt
├── Dockerfile            # Multi-stage build with UID/GID 99
├── docker-compose.yml    # Local development
├── docker-deploy.sh      # Deployment script
└── .env                  # Environment variables
```