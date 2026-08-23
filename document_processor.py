import os
import fitz  # PyMuPDF
import docx  # python-docx
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

class DocumentProcessor:
    """Handles text extraction and chunking for PDF, DOCX, and TXT files."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Standardizes text encoding, strips trailing/leading whitespaces, and removes redundant gaps."""
        if not text:
            return ""
        # Standardize lines
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned_line = " ".join(line.split())
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        return "\n".join(cleaned_lines)

    @classmethod
    def extract_text_from_pdf(cls, file_path: str) -> List[Dict[str, Any]]:
        """Extracts text page-by-page from a PDF using PyMuPDF."""
        pages = []
        doc = fitz.open(file_path)
        for page_idx, page in enumerate(doc):
            text = page.get_text("text")
            cleaned_text = cls.clean_text(text)
            if cleaned_text.strip():
                pages.append({
                    "text": cleaned_text,
                    "metadata": {
                        "source": os.path.basename(file_path),
                        "page": page_idx + 1,
                        "type": "pdf"
                    }
                })
        doc.close()
        return pages

    @classmethod
    def extract_text_from_docx(cls, file_path: str) -> List[Dict[str, Any]]:
        """Extracts text from a DOCX file using python-docx, paginated pseudo-style (every ~500 words)."""
        doc = docx.Document(file_path)
        pages = []
        text_accumulator = ""
        current_word_count = 0
        pseudo_page = 1

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            text_accumulator += text + "\n"
            current_word_count += len(text.split())

            if current_word_count >= 500:
                pages.append({
                    "text": cls.clean_text(text_accumulator),
                    "metadata": {
                        "source": os.path.basename(file_path),
                        "page": pseudo_page,
                        "type": "docx"
                    }
                })
                text_accumulator = ""
                current_word_count = 0
                pseudo_page += 1

        if text_accumulator.strip():
            pages.append({
                "text": cls.clean_text(text_accumulator),
                "metadata": {
                    "source": os.path.basename(file_path),
                    "page": pseudo_page,
                    "type": "docx"
                }
            })

        return pages

    @classmethod
    def extract_text_from_txt(cls, file_path: str) -> List[Dict[str, Any]]:
        """Extracts text from TXT files, chunking into pseudo-pages of ~3000 characters."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        cleaned_text = cls.clean_text(text)
        pages = []
        chunk_size = 3000
        for page_idx, start_idx in enumerate(range(0, len(cleaned_text), chunk_size)):
            chunk = cleaned_text[start_idx:start_idx + chunk_size]
            if chunk.strip():
                pages.append({
                    "text": chunk,
                    "metadata": {
                        "source": os.path.basename(file_path),
                        "page": page_idx + 1,
                        "type": "txt"
                    }
                })
        return pages

    @classmethod
    def process_document(cls, file_path: str) -> List[Dict[str, Any]]:
        """Determines the file type and parses its text into pages with metadata."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path.lower())[1]
        if ext == '.pdf':
            return cls.extract_text_from_pdf(file_path)
        elif ext == '.docx':
            return cls.extract_text_from_docx(file_path)
        elif ext in ['.txt', '.log', '.md']:
            return cls.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @classmethod
    def chunk_documents(cls, pages: List[Dict[str, Any]], chunk_size: int = 800, chunk_overlap: int = 150, document_id: int = 0) -> List[Dict[str, Any]]:
        """Chunks pages of text into smaller, overlapping sections using RecursiveCharacterTextSplitter and attaches rich metadata."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = []
        global_chunk_idx = 0
        for page in pages:
            split_texts = splitter.split_text(page["text"])
            for split_text in split_texts:
                page_meta = page["metadata"].copy()
                filename = page_meta.get("source", "unknown")
                chunk_id = f"doc_{document_id}_chk_{global_chunk_idx}"

                meta = {
                    "document_id": document_id,
                    "filename": filename,
                    "source": filename,
                    "chunk_id": chunk_id,
                    "chunk_index": global_chunk_idx,
                    "page": page_meta.get("page", 1),
                    "file_type": page_meta.get("type", "unknown")
                }
                # Preserve any extra metadata keys
                meta.update({k: v for k, v in page_meta.items() if k not in meta})

                chunks.append({
                    "text": split_text,
                    "metadata": meta
                })
                global_chunk_idx += 1

        return chunks

