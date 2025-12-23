FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching (use Linux-compatible requirements)
COPY requirements-linux.txt requirements.txt

# Install Python dependencies
# Install numpy first - force wheel installation (Spleeter requires old numpy)
# Use --only-binary to avoid building from source
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir --only-binary=numpy "numpy<1.19.0,>=1.18.0" && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p temp/uploads temp/output logs

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Run the application using startup script (handles Railway's PORT env var)
CMD ["/app/start.sh"]

