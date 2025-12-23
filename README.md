# Stem Separator API

Production-ready FastAPI application for audio stem separation using Spleeter. This API provides a robust, scalable solution for separating audio files into individual stems (vocals, drums, bass, etc.) with comprehensive error handling, structured logging, and production-grade features.

## ✨ Features

- 🎵 **Audio Stem Separation**: Separate audio files into 2, 4, or 5 stems using Spleeter
- 🚀 **FastAPI**: High-performance async API built with FastAPI
- 📊 **Structured Logging**: JSON-formatted logs with Loguru (colored console output in dev, JSON in prod)
- 🎨 **Visual Feedback**: Terminal spinners with Halo for long-running operations
- 📖 **Comprehensive API Docs**: Detailed Swagger/OpenAPI documentation with examples
- 🛡️ **Error Handling**: Comprehensive error handling for all edge cases
- ✅ **File Validation**: Strict file validation (size, format, MIME type)
- 🔒 **Security**: Path traversal protection, filename sanitization
- 📦 **Production Ready**: Proper project structure, configuration management, and best practices
- 🧪 **Type Safety**: Full type hints and Pydantic validation
- 🎯 **Code Quality**: 100/100 quality score with zero errors or warnings (Ruff)
- 🔧 **TensorFlow Compatibility**: Automatic compatibility shim for TensorFlow 2.13+ on Apple Silicon

## 📋 Requirements

- Python 3.9+
- Conda (Miniconda or Anaconda) - **Recommended for Apple Silicon Macs**
- ffmpeg
- libsndfile

## 🚀 Quick Start

### Using Conda (Recommended - Especially for Apple Silicon)

Conda is **strongly recommended** for Apple Silicon (M1/M2/M3) Macs as it handles:
- System dependencies (ffmpeg, libsndfile) automatically
- Apple's optimized TensorFlow builds
- Better dependency resolution
- TensorFlow estimator compatibility

1. **Install Conda** (if not already installed):
   ```bash
   # Download Miniconda from https://docs.conda.io/en/latest/miniconda.html
   # Or use Miniforge (ARM64 optimized): https://github.com/conda-forge/miniforge
   ```

2. **Create and activate the conda environment**:
   ```bash
   conda create -n stem-sep python=3.9
   conda activate stem-sep
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**:
   ```bash
   python -c "from app.main import app; import tensorflow as tf; print('✅ All packages installed!'); print(f'✅ TensorFlow version: {tf.__version__}')"
   ```

5. **Start the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

### Using venv (Alternative)

If you prefer venv:

1. **Install system dependencies**:
   ```bash
   # macOS
   brew install ffmpeg libsndfile
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install packages**:
   ```bash
   pip install -r requirements.txt
   ```

   **Note**: On Apple Silicon, TensorFlow 2.13.0 with tensorflow-estimator is included in requirements.txt

## 📖 Usage

### Starting the Server

```bash
# Make sure environment is activated
conda activate stem-sep  # or: source venv/bin/activate

# Start server
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs (Interactive API documentation)
- **ReDoc**: http://localhost:8000/redoc (Alternative documentation)
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### API Endpoints

#### 1. Health Check
```bash
GET /health
```

Returns service health status:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "stem-separator-api"
}
```

#### 2. Readiness Check
```bash
GET /ready
```

Checks if the service is ready to process requests (verifies models are loaded):
```json
{
  "status": "ready",
  "models_loaded": true,
  "version": "1.0.0"
}
```

#### 3. Separate Audio
```bash
POST /api/v1/separate
```

**Parameters:**
- `file` (multipart/form-data, required): Audio file to separate
- `stems` (query, optional): Number of stems - `2stems`, `4stems`, or `5stems` (default: `2stems`)
- `bitrate` (query, optional): Output bitrate (default: `320k`)
- `format` (query, optional): Output format - `wav`, `mp3`, `flac`, `m4a`, `aac`, `ogg` (default: `wav`)

**Supported Audio Formats:**
- MP3, WAV, FLAC, M4A, AAC, OGG

**Stem Options:**
- **2stems**: Separates into vocals and accompaniment
- **4stems**: Separates into vocals, drums, bass, and other
- **5stems**: Separates into vocals, drums, bass, piano, and other

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/separate?stems=2stems&bitrate=320k&format=wav" \
  -F "file=@audio_example.mp3"
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully separated audio into 2stems",
  "job_id": "181543dd-c632-4a42-bb8d-f3ca74c763cd",
  "stems": "2stems",
  "output_files": ["vocals.wav", "accompaniment.wav"],
  "processing_time": 12.45
}
```

#### 4. Download Stem File
```bash
GET /api/v1/separate/{job_id}/download/{filename}
```

Download a specific stem file from a completed separation job.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/separate/181543dd-c632-4a42-bb8d-f3ca74c763cd/download/vocals.wav" \
  --output vocals.wav
```

### Interactive API Documentation

Visit http://localhost:8000/docs for the interactive Swagger UI where you can:
- View all endpoints with detailed descriptions
- See request/response examples
- Try out the API directly from your browser
- Download OpenAPI specification

## 🔧 Configuration

Configuration is managed through environment variables or a `.env` file. Key settings:

```env
# API Settings
API_TITLE=Stem Separator API
API_VERSION=1.0.0
DEBUG=False

# Server Settings
HOST=0.0.0.0
PORT=8000

# File Upload Settings
MAX_UPLOAD_SIZE=104857600  # 100MB in bytes

# Logging Settings
LOG_LEVEL=INFO
LOG_FORMAT=json  # or "text" for colored console output
LOG_DIR=logs
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# Processing Settings
PROCESS_TIMEOUT=600  # 10 minutes
CLEANUP_AFTER_PROCESSING=True
```

## 🏗️ Project Structure

```
stem-sep/
├── app/
│   ├── main.py                  # FastAPI application
│   ├── config.py                # Configuration management
│   ├── logging_config.py        # Loguru logging setup
│   ├── models.py                # Pydantic models
│   ├── exceptions.py            # Custom exceptions
│   ├── utils.py                 # Utility functions
│   ├── profiling.py             # Performance profiling
│   ├── tensorflow_compat.py     # TensorFlow compatibility shim
│   ├── routes/                  # API routes
│   │   ├── __init__.py
│   │   ├── health.py            # Health check endpoints
│   │   └── separate.py          # Audio separation endpoints
│   └── services/                # Business logic
│       ├── __init__.py
│       └── audio_service.py    # Audio processing service
├── temp/                        # Temporary files (uploads, outputs)
│   ├── uploads/
│   └── output/
├── logs/                        # Application logs
├── requirements.txt             # Python dependencies (macOS)
├── requirements-linux.txt      # Python dependencies (Linux/Railway)
├── Dockerfile                   # Docker configuration for Railway
├── start.sh                     # Startup script for Railway
├── Procfile                     # Railway Procfile
├── railway.json                 # Railway configuration
└── README.md
```

## 🎯 Code Quality

This project maintains a **100/100 quality score** with zero errors or warnings:

- ✅ **Ruff**: All linting checks pass
- ✅ **Type Safety**: Full type hints throughout
- ✅ **Formatting**: Consistent code formatting
- ✅ **Documentation**: Comprehensive docstrings and API docs

Run quality checks:
```bash
ruff check app/
ruff format app/
```

## 🐛 Troubleshooting

### Apple Silicon (M1/M2/M3) Issues

The project includes automatic TensorFlow compatibility handling for Apple Silicon:

1. **TensorFlow Estimator Compatibility**: 
   - The project automatically patches `tf.estimator` for TensorFlow 2.13+
   - Uses `tensorflow-estimator==2.13.0` for compatibility
   - No manual configuration needed

2. **If you encounter TensorFlow import errors**:
   ```bash
   # Reinstall TensorFlow
   pip uninstall tensorflow tensorflow-macos -y
   pip install tensorflow-macos==2.13.0 --no-cache-dir
   ```

3. **Check architecture**:
   ```bash
   python -c "import platform; print(platform.machine())"
   # Should output: arm64
   ```

### Common Issues

1. **Model Loading Errors**
   - Spleeter models download automatically on first use
   - Ensure internet connection is available
   - Check disk space (models are ~500MB each)

2. **FFmpeg Errors**
   - Verify installation: `ffmpeg -version`
   - On macOS: `brew install ffmpeg`
   - Or use conda: `conda install -c conda-forge ffmpeg`

3. **Import Errors**
   - Ensure environment is activated
   - Verify all packages installed: `pip list`
   - Try reinstalling: `pip install --force-reinstall -r requirements.txt`

4. **typing_extensions Errors**
   - Ensure `typing_extensions>=4.6.0` is installed
   - Required for Pydantic 2.9.2 compatibility

## 📚 Dependencies

### Core Dependencies
- **FastAPI** (0.115.0): Modern web framework
- **Spleeter** (2.1.0): Audio stem separation
- **TensorFlow** (2.13.0): Machine learning backend
- **Pydantic** (2.9.2): Data validation

### Logging & UX
- **Loguru** (0.7.2): Structured logging with JSON support
- **Halo** (0.0.31): Terminal spinners for visual feedback

### Compatibility
- **tensorflow-estimator** (2.13.0): TensorFlow estimator compatibility
- **typing_extensions** (>=4.6.0): Type hint compatibility

See `requirements.txt` for the complete list.

## 🔄 Why Conda vs venv?

### Conda Advantages:
- ✅ **System Dependencies**: Automatically installs ffmpeg, libsndfile
- ✅ **Apple Silicon**: Better support for M1/M2/M3 Macs with Apple's TensorFlow
- ✅ **Dependency Resolution**: Handles complex dependency conflicts better
- ✅ **Cross-platform**: Works consistently across macOS, Linux, Windows

### venv Advantages:
- ✅ **Lightweight**: Smaller footprint
- ✅ **Standard**: Built into Python
- ✅ **Simple**: Easier for pure Python projects

### Recommendation:
- **Use Conda** if you're on Apple Silicon or need system dependencies
- **Use venv** if you're on Linux/Windows and have system deps installed manually

## 🧪 Development

### Running the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Code Quality Checks

```bash
# Linting
ruff check app/

# Formatting
ruff format app/

# Type checking (if mypy is installed)
mypy app/
```

### Testing

```bash
pip install pytest pytest-asyncio httpx
pytest
```

## 🚢 Production Deployment

### Railway Deployment

This project is configured for easy deployment on Railway:

1. **Connect your GitHub repository** to Railway
2. **Railway will automatically detect** the Dockerfile
3. **Set environment variables** (optional):
   ```env
   DEBUG=False
   LOG_FORMAT=json
   LOG_LEVEL=INFO
   CLEANUP_AFTER_PROCESSING=True
   MAX_UPLOAD_SIZE=104857600
   ```
4. **Deploy!** Railway will:
   - Build the Docker image using `Dockerfile`
   - Use `requirements-linux.txt` (Linux-compatible TensorFlow)
   - Automatically set the PORT environment variable
   - Start the application

**Note**: The Dockerfile uses `requirements-linux.txt` which contains `tensorflow==2.13.0` (Linux version) instead of `tensorflow-macos` (macOS only).

### Docker Build

To build and run locally:

```bash
docker build -t stem-separator-api .
docker run -p 8000:8000 stem-separator-api
```

### Environment Variables

Set these in your production environment:

```env
DEBUG=False
LOG_FORMAT=json
LOG_LEVEL=INFO
CLEANUP_AFTER_PROCESSING=True
MAX_UPLOAD_SIZE=104857600
PORT=8000  # Railway sets this automatically
```

## 📝 Logging

The application uses **Loguru** for structured logging:

- **Development**: Colored console output for easy debugging
- **Production**: JSON-formatted logs for log aggregation systems
- **File Logging**: Automatic log rotation and compression
- **Structured Data**: All logs include context (job_id, user_id, etc.)

Log format can be configured via `LOG_FORMAT` environment variable:
- `json`: Machine-readable JSON logs (production)
- `text`: Human-readable colored logs (development)

## 🎨 Features in Detail

### Structured Logging (Loguru)
- JSON logs in production for log aggregation
- Colored console output in development
- Automatic log rotation and compression
- Contextual logging with job IDs and request tracking

### Visual Feedback (Halo)
- Terminal spinners during audio processing
- Non-intrusive (only in terminal environments)
- Automatic fallback if not in terminal

### Enhanced API Documentation
- Comprehensive Swagger/OpenAPI docs
- Request/response examples
- Parameter descriptions with validation rules
- Multiple response examples for different scenarios
- Interactive "Try it out" functionality

### TensorFlow Compatibility
- Automatic patching for TensorFlow 2.13+ compatibility
- Works seamlessly on Apple Silicon
- No manual configuration required

## 📄 License

MIT License

## 🙏 Acknowledgments

- [Spleeter](https://github.com/deezer/spleeter) by Deezer Research - Audio source separation
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Loguru](https://github.com/Delgan/loguru) - Structured logging
- [Halo](https://github.com/manrajgrover/halo) - Terminal spinners

## 📞 Support

For issues, questions, or contributions, please open an issue on the project repository.

---

**Made with ❤️ for audio processing**
