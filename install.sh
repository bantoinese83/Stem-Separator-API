#!/bin/bash
# Installation script for Stem Separator API
# Optimized for Apple Silicon (M1/M2/M3) Macs

set -e

echo "🎵 Installing Stem Separator API..."

# Check if we're in the right environment
if [[ "$CONDA_DEFAULT_ENV" != "stem-sep" ]]; then
    echo "⚠️  Not in stem-sep environment. Please activate it first:"
    echo "   conda activate stem-sep"
    exit 1
fi

echo ""
echo "Step 1: Installing TensorFlow 2.13.0 for macOS (with estimator compatibility)..."
# Uninstall any existing TensorFlow versions
pip uninstall tensorflow tensorflow-macos -y 2>/dev/null || true

# Install TensorFlow 2.13.0 (compatible with tensorflow-estimator)
pip install tensorflow-macos==2.13.0 --no-cache-dir

# Install tensorflow-estimator for compatibility
echo "Installing tensorflow-estimator for compatibility..."
pip install tensorflow-estimator==2.13.0

echo ""
echo "Step 2: Installing core dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "Step 3: Installing Spleeter dependencies (if needed)..."
# Spleeter may have some dependency conflicts, install compatible versions
pip install ffmpeg-python librosa norbert || {
    echo "⚠️  Some Spleeter dependencies may have conflicts, continuing..."
}

echo ""
echo "✅ Installation complete!"
echo ""
echo "Verifying installation..."
python -c "
import sys

errors = []
success = []

try:
    import fastapi
    success.append('✅ FastAPI installed')
except ImportError as e:
    errors.append(f'❌ FastAPI error: {e}')

try:
    import spleeter
    success.append('✅ Spleeter installed')
except ImportError as e:
    errors.append(f'❌ Spleeter error: {e}')

try:
    import tensorflow as tf
    success.append(f'✅ TensorFlow installed (version: {tf.__version__})')
    # Check if estimator is available
    try:
        from tensorflow_estimator._api.v1 import estimator
        success.append('✅ TensorFlow estimator compatibility available')
    except ImportError:
        success.append('⚠️  TensorFlow estimator will be patched at runtime')
except ImportError as e:
    errors.append(f'❌ TensorFlow error: {e}')

try:
    from loguru import logger
    success.append('✅ Loguru installed')
except ImportError as e:
    errors.append(f'❌ Loguru error: {e}')

try:
    from halo import Halo
    success.append('✅ Halo installed')
except ImportError as e:
    errors.append(f'❌ Halo error: {e}')

try:
    import pydantic
    success.append(f'✅ Pydantic installed (version: {pydantic.__version__})')
except ImportError as e:
    errors.append(f'❌ Pydantic error: {e}')

# Print results
for msg in success:
    print(msg)
for msg in errors:
    print(msg)

if errors:
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All dependencies installed successfully!"
    echo ""
    echo "To start the server:"
    echo "  uvicorn app.main:app --reload"
    echo ""
    echo "API will be available at:"
    echo "  - http://localhost:8000"
    echo "  - http://localhost:8000/docs (Swagger UI)"
    echo "  - http://localhost:8000/redoc (ReDoc)"
else
    echo ""
    echo "⚠️  Some dependencies failed to install. Please check the errors above."
    exit 1
fi
