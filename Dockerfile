# Multi-stage Dockerfile for YTT - All-in-one Container
# Stage 1: Build the frontend
FROM node:24-alpine@sha256:a0b9bf06e4e6193cf7a0f58816cc935ff8c2a908f81e6f1a95432d679c54fbfd AS frontend-builder

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

# Install system dependencies:
# - curl for the healthcheck
# - openssh-client to reach the remote Claude host for translation improvement
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    openssh-client \
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

# Build info (injected at build time via --build-arg)
ARG BUILD_DATE=unknown
ARG GIT_COMMIT=unknown
RUN echo "{\"version\": \"1.0.0\", \"build_date\": \"${BUILD_DATE}\", \"git_commit\": \"${GIT_COMMIT}\"}" > build-info.json

# Create data directories and set up user
RUN mkdir -p data/uploads data/transcripts

# SSH dir for the remote-Claude integration: the private key is bind-mounted in
# at /app/.ssh/id_ed25519, and ssh writes known_hosts here on first connect.
RUN mkdir -p /app/.ssh && chmod 700 /app/.ssh

# Create user with UID/GID 99 to match Unraid's nobody:users.
# A real passwd/group entry is required: the ssh client (used for the
# remote-Claude integration) calls getpwuid(99) to find the home dir for
# ~/.ssh, and fails with "No user exists for uid 99" without it. The previous
# `groupadd -g 99 users` clashed with the pre-existing "users" group, so gid 99
# was never created and the user creation silently failed.
RUN if ! getent group 99 >/dev/null; then groupadd -g 99 appuser; fi && \
    if ! getent passwd 99 >/dev/null; then useradd -u 99 -g 99 -d /app -s /bin/bash appuser; fi && \
    chown -R 99:99 /app

# ssh (and anything using ~) resolves the home dir from here
ENV HOME=/app

# Switch to UID 99 (Unraid's nobody)
USER 99:99

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with verbose logging
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]