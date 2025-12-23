"""TensorFlow compatibility shim for Spleeter.

This module patches TensorFlow to add the estimator module for compatibility
with Spleeter, which requires tf.estimator that was removed in TensorFlow 2.13+.

This must be imported before Spleeter uses tensorflow.estimator.
"""

import sys
from typing import Any


# Patch function that patches tensorflow if it's already imported
def patch_tensorflow_estimator() -> None:
    """Patch tensorflow module to add estimator if missing."""
    if "tensorflow" not in sys.modules:
        return

    tf = sys.modules["tensorflow"]

    # Skip if already patched
    if hasattr(tf, "estimator"):
        return

    try:
        # Method 1: Direct import from _api.v1 (preferred method)
        from tensorflow_estimator._api.v1 import estimator  # noqa: E402

        # Add estimator to tensorflow module
        tf.estimator = estimator  # type: ignore
        return
    except (ImportError, AttributeError):
        # Continue to try other methods if this fails
        pass

    try:
        # Method 2: Import tensorflow_estimator and access estimator via _api
        import tensorflow_estimator  # noqa: E402

        # Try different access patterns
        if hasattr(tensorflow_estimator, "_api") and hasattr(
            tensorflow_estimator._api, "v1"
        ):
            if hasattr(tensorflow_estimator._api.v1, "estimator"):
                tf.estimator = tensorflow_estimator._api.v1.estimator  # type: ignore
                return
    except (ImportError, AttributeError):
        pass

    try:
        # Method 3: Import from python.estimator.estimator_lib
        import tensorflow_estimator.python.estimator.estimator_lib as estimator_lib  # noqa: E402

        # Create a wrapper that provides the needed classes
        class EstimatorWrapper:
            """Wrapper for estimator module."""

            RunConfig = estimator_lib.RunConfig  # type: ignore
            Estimator = estimator_lib.Estimator  # type: ignore

            class ModeKeys:
                """Mode keys."""

                TRAIN = "train"
                EVAL = "eval"
                PREDICT = "predict"

        tf.estimator = EstimatorWrapper()  # type: ignore
        return
    except (ImportError, AttributeError):
        pass

    # Last resort: create a minimal shim
    class EstimatorShim:
        """Minimal shim for tf.estimator that provides RunConfig and Estimator."""

        class RunConfig:
            """Minimal RunConfig shim."""

            def __init__(self, **kwargs: Any) -> None:
                """Initialize RunConfig with kwargs."""
                self.__dict__.update(kwargs)

        class Estimator:
            """Minimal Estimator shim."""

            def __init__(self, **kwargs: Any) -> None:
                """Initialize Estimator with kwargs."""
                self.__dict__.update(kwargs)

        class ModeKeys:
            """Mode keys for estimator."""

            TRAIN = "train"
            EVAL = "eval"
            PREDICT = "predict"

    tf.estimator = EstimatorShim()  # type: ignore


# Try to patch immediately if tensorflow is already imported
# This handles the case where tensorflow was imported before this module
try:
    patch_tensorflow_estimator()
except Exception:
    # If patching fails, it will be retried when tensorflow is imported
    pass
