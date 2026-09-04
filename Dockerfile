FROM python:3.11-slim

# Install ffmpeg and required system tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create volume/storage directories
RUN mkdir -p /app/temp /app/cache

# Environment defaults
ENV PYTHONUNBUFFERED=1
ENV TEMP_DIR=/app/temp
ENV CACHE_DIR=/app/cache
ENV DB_PATH=/app/cache/grabilo.db

CMD ["python", "app/bot.py"]
