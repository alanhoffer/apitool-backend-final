import os
import tempfile
from pathlib import Path


def is_vercel() -> bool:
    return os.getenv("VERCEL") == "1"


def is_serverless() -> bool:
    return is_vercel() or os.getenv("SERVERLESS") == "1"


def should_run_scheduler() -> bool:
    if os.getenv("TESTING") == "1":
        return False
    return os.getenv("ENABLE_SCHEDULER", "true").lower() == "true" and not is_serverless()


def get_upload_dir() -> Path:
    configured_path = os.getenv("UPLOAD_DIR")
    if configured_path:
        upload_dir = Path(configured_path)
    elif is_serverless():
        upload_dir = Path(tempfile.gettempdir()) / "uploads"
    else:
        upload_dir = Path("uploads")

    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir
