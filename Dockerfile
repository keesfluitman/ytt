# Multi-stage Dockerfile for YTT - All-in-one Container
# Stage 1: Build the frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files (using pnpm)
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install pnpm and dependencies
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Copy frontend source
COPY frontend/ ./

# Build static files
RUN pnpm run build

# Stage 2: Production runtime with Python + FastAPI
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Copy built frontend static files from stage 1
COPY --from=frontend-builder /app/frontend/build ./static

# Create data directories and set up user
RUN mkdir -p data/uploads data/transcripts

# Create user with UID/GID 99 to match Unraid's nobody:users
RUN groupadd -g 99 users 2>/dev/null || true && \
    useradd -u 99 -g 99 -d /app -s /bin/bash unraid-user 2>/dev/null || true && \
    chown -R 99:99 /app

# Switch to UID 99 (Unraid's nobody)
USER 99:99

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with verbose logging
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]