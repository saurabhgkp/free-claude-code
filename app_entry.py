"""PyInstaller entry point."""

import multiprocessing
import os
import sys


def _set_tiktoken_cache():
    """Point tiktoken at its bundled BPE data files when frozen."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # noqa: SLF001
        cache = os.path.join(base, "tiktoken_cache")
        os.environ.setdefault("TIKTOKEN_CACHE_DIR", cache)


def _run():
    import uvicorn

    from api.app import app
    from config.settings import get_settings

    settings = get_settings()
    print(f"\n  free-claude-code is running on http://localhost:{settings.port}\n")
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
        timeout_graceful_shutdown=5,
    )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    _set_tiktoken_cache()
    _run()
