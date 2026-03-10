# Python image
FROM python:3.12-slim

# Setting environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Setting the working directory
WORKDIR /app

# Install system dependencies
# curl is needed for the Bun install script; unzip is required by the Bun installer
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Bun
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

# Verify Bun installation
RUN bun --version

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# --- JS/Frontend Requirements (via Bun) ---
COPY package.json bun.lock* /app/
RUN bun install

# Copy the project code
COPY . /app/

# Expose Django port
EXPOSE 8000

# Default command
RUN chmod +x /app/start.sh
CMD ["./start.sh"]
