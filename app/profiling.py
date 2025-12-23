"""Performance profiling and monitoring utilities."""

import functools
import time
import tracemalloc
from contextlib import contextmanager
from typing import Callable, Dict, TypeVar

from loguru import logger

logger = logger.bind(name=__name__)

F = TypeVar("F", bound=Callable)


def profile_time(func: F) -> F:
    """Decorator to profile function execution time."""

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start_time
            logger.debug(
                f"Function {func.__name__} took {elapsed:.4f}s",
                function=func.__name__,
                duration=elapsed,
            )

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start_time
            logger.debug(
                f"Function {func.__name__} took {elapsed:.4f}s",
                function=func.__name__,
                duration=elapsed,
            )

    # Return appropriate wrapper based on function type
    if hasattr(func, "__code__") and func.__code__.co_flags & 0x80:  # CO_COROUTINE
        return async_wrapper  # type: ignore
    return sync_wrapper  # type: ignore


@contextmanager
def profile_memory():
    """Context manager to profile memory usage."""
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    try:
        yield
    finally:
        snapshot_after = tracemalloc.take_snapshot()
        top_stats = snapshot_after.compare_to(snapshot_before, "lineno")

        logger.debug("Memory profiling results:")
        for stat in top_stats[:10]:
            logger.debug(f"{stat}")

        tracemalloc.stop()


@contextmanager
def profile_performance(operation_name: str):
    """Context manager to profile both time and memory for an operation."""
    start_time = time.perf_counter()
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        snapshot_after = tracemalloc.take_snapshot()
        top_stats = snapshot_after.compare_to(snapshot_before, "lineno")

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        logger.info(
            f"Performance profile: {operation_name}",
            operation=operation_name,
            duration=elapsed,
            memory_current_mb=current / 1024 / 1024,
            memory_peak_mb=peak / 1024 / 1024,
            top_memory_stats=[
                {
                    "filename": stat.traceback[0].filename,
                    "lineno": stat.traceback[0].lineno,
                    "size_diff_mb": stat.size_diff / 1024 / 1024,
                }
                for stat in top_stats[:5]
            ],
        )


def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage statistics."""
    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return {
            "rss_mb": mem_info.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": mem_info.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": process.memory_percent(),
        }
    except ImportError:
        # psutil not installed, return basic info
        logger.debug("psutil not available, using basic memory info")
        return {"rss_mb": 0.0, "vms_mb": 0.0, "percent": 0.0}
