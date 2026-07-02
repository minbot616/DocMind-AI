import os
import sys
import subprocess
import logging
from tkinter import messagebox
from typing import Set

# Supported file formats
ALLOWED_EXTENSIONS: Set[str] = {'.pdf', '.docx', '.txt', '.log', '.md'}

# Log configuration
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docmind_ai.log")
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
    """Returns the file extension including the dot (e.g. '.pdf')."""
    return os.path.splitext(filename.lower())[1]

def open_document(file_path: str) -> bool:
    """Opens the selected document file locally using the default OS application."""
    if not os.path.exists(file_path):
        messagebox.showerror("Error", "Source file not found on disk.")
        logger.error(f"Failed to open document: file not found at path '{file_path}'")
        return False
    
    logger.info(f"Opening document: {file_path}")
    try:
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.call(["open", file_path])
        else:
            subprocess.call(["xdg-open", file_path])
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open file: {str(e)}")
        logger.exception(f"Exception occurred while opening document '{file_path}'")
        return False

def copy_to_clipboard(widget, text: str, btn) -> None:
    """Copies text content to clipboard and updates button text as feedback."""
    try:
        widget.clipboard_clear()
        widget.clipboard_append(text)
        widget.update()
        btn.configure(text="✓ Copied!")
        widget.after(1500, lambda: btn.configure(text="📋 Copy"))
        logger.info("Copied content snippet to clipboard.")
    except Exception:
        logger.exception("Failed to copy text to clipboard.")
