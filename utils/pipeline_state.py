"""
utils/pipeline_state.py
Thread-safe pipeline state management with locking.
Prevents recommendations from running while GDS pipeline is executing.
"""
import threading
import datetime
from typing import Optional

class PipelineStateManager:
    """
    Manages the state of the GDS pipeline with thread-safe operations.
    Uses a lock to ensure concurrent access safety.
    """

    def __init__(self):
        self._lock = threading.RLock()  # Recursive lock for nested access
        self._running = False
        self._last_run: Optional[str] = None
        self._last_report: Optional[dict] = None
        self._error: Optional[str] = None
        self._start_time: Optional[datetime.datetime] = None

    def start(self) -> bool:
        """
        Mark pipeline as starting.
        Returns True if successful, False if already running.
        """
        with self._lock:
            if self._running:
                return False
            self._running = True
            self._error = None
            self._start_time = datetime.datetime.utcnow()
            return True

    def finish(self, report: dict) -> None:
        """Mark pipeline as finished successfully."""
        with self._lock:
            self._running = False
            self._error = None
            self._last_report = report
            self._last_run = datetime.datetime.utcnow().isoformat()

    def fail(self, error: str) -> None:
        """Mark pipeline as failed with error message."""
        with self._lock:
            self._running = False
            self._error = error
            self._last_report = None

    def is_running(self) -> bool:
        """Check if pipeline is currently running."""
        with self._lock:
            return self._running

    def get_status(self) -> dict:
        """Get complete pipeline status."""
        with self._lock:
            elapsed_seconds = None
            if self._running and self._start_time:
                elapsed = datetime.datetime.utcnow() - self._start_time
                elapsed_seconds = elapsed.total_seconds()

            return {
                "running": self._running,
                "last_run": self._last_run,
                "last_report": self._last_report,
                "error": self._error,
                "elapsed_seconds": elapsed_seconds,
                "start_time": self._start_time.isoformat() if self._start_time else None,
            }

    def reset(self) -> None:
        """Reset all state (for testing)."""
        with self._lock:
            self._running = False
            self._last_run = None
            self._last_report = None
            self._error = None
            self._start_time = None


# Global singleton instance
_pipeline_state = PipelineStateManager()


def get_pipeline_state() -> PipelineStateManager:
    """Get the global pipeline state manager."""
    return _pipeline_state
