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
# Install numpy first with compatible setuptools (Spleeter requires old numpy)
# numpy 1.18.5 needs older setuptools to build from source
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir "setuptools<60.0" && \
    pip install --no-cache-dir "numpy==1.18.5" && \
    pip install --no-cache-dir --upgrade setuptools && \
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

