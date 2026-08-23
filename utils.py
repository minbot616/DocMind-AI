import os
import sys
import logging
from typing import Set

# Supported file formats
ALLOWED_EXTENSIONS: Set[str] = {'.pdf', '.docx', '.txt', '.log', '.md'}

# Log configuration
LOG_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "docmind_ai.log"
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("DocMindAI")


def allowed_file(filename: str) -> bool:
    """Checks if a file extension is supported."""
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS


def format_size(bytes_size: int) -> str:
    """Formats file size bytes into a human-readable string."""
    size = float(bytes_size)

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0

    return f"{size:.1f} TB"


def get_file_extension(filename: str) -> str:
    """Returns the file extension including the dot."""
    return os.path.splitext(filename.lower())[1]