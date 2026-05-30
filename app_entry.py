"""
PyInstaller entry point.

Use this file as the PyInstaller target (not server.py).
The app object is passed directly to uvicorn.run() to avoid string-based
module imports, which don't work in frozen executables.
"""
import multiprocessing
import sys


def _run():
    import uvicorn

    from api.app import app
    from config.settings import get_settings

    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
        timeout_graceful_shutdown=5,
    )


if __name__ == "__main__":
    # Required on Windows so spawned subprocesses don't re-run the entry point
    multiprocessing.freeze_support()
    _run()
