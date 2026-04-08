# ============================================
# Stage 1: Build Frontend Assets (Svelte/Vite)
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system deps for Bun
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Bun
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

# Install JS dependencies
COPY package.json bun.lock* /app/
RUN bun install

# Build frontend
COPY vite.config.js /app/
COPY frontend/ /app/frontend/
COPY dashboard/ /app/dashboard/
RUN bun run build

# ============================================
# Stage 2: Production Django Image
# ============================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . /app/
RUN rm -rf /app/static/dist

# Copy built frontend assets from builder stage
COPY --from=builder /app/static/dist /app/static/dist

# Collect static files
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Create non-root user for security
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m -d /home/appuser appuser && \
    chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

# Production: Gunicorn WSGI server
CMD ["gunicorn", "fzboard.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
