import os
import json
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple, Optional
from database import DatabaseManager
from document_processor import DocumentProcessor
from llm_manager import LLMManager
from utils import logger

class ChatManager:
    """Manages active chat sessions, handles special AI commands (summary, keywords, suggestions),
    and exports chat records to TXT/PDF.
    """

    @staticmethod
    def get_user_chats(user_id: int) -> List[Dict[str, Any]]:
        """Gets all chats for a user."""
        return DatabaseManager.get_chats(user_id)

    @staticmethod
    def create_new_chat(user_id: int, title: str = "New Conversation") -> int:
        """Creates a new chat session."""
        return DatabaseManager.create_chat(user_id, title)

    @staticmethod
    def get_chat_messages(chat_id: int) -> List[Dict[str, Any]]:
        """Gets messages for a chat session."""
        return DatabaseManager.get_messages(chat_id)

    @staticmethod
    def save_message(chat_id: int, sender: str, content: str, sources: Optional[List[Dict[str, Any]]] = None, response_time: Optional[float] = None) -> int:
        """Saves a message to the database."""
        return DatabaseManager.add_message(chat_id, sender, content, sources, response_time)

    @staticmethod
    def rename_chat(chat_id: int, new_title: str) -> bool:
        """Renames a chat session."""
        return DatabaseManager.rename_chat(chat_id, new_title)

    @staticmethod
    def delete_chat(chat_id: int) -> bool:
        """Deletes a chat session."""
        return DatabaseManager.delete_chat(chat_id)

    # --- Special AI Operations ---

    @staticmethod
    def generate_document_summary(
        file_path: str,
        llm_provider: str,
        llm_model: str,
        api_key: str = ""
    ) -> str:
        """Generates a summary of the uploaded document by analyzing the first few pages."""
        try:
            pages = DocumentProcessor.process_document(file_path)
            if not pages:
                return "The document appears to be empty."
            
            # Select up to the first 3 pages to avoid context window issues
            sample_pages = pages[:3]
            content = "\n\n".join([p["text"] for p in sample_pages])
            
            prompt = (
                "You are an expert document analyzer. "
                "Provide a comprehensive summary of the following document content. "
                "Highlight the main goals, key arguments, and overall topic.\n\n"
                f"DOCUMENT CONTENT (FIRST PAGES):\n{content}\n\n"
                "SUMMARY:"
            )
            
            llm = LLMManager.get_llm(llm_provider, llm_model, api_key, temperature=0.3)
            response = llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            err_msg = str(e)
            if "10061" in err_msg or "Connection refused" in err_msg or "actively refused it" in err_msg:
                return (
                    "⚠️ Connection Error: Could not connect to the active LLM provider.\n\n"
                    "If you are using Ollama, please ensure that the Ollama desktop app is running locally (http://localhost:11434) and has the model loaded. "
                    "If you are using a cloud provider (OpenAI/Groq), check your internet connection and API configurations in the Settings tab."
                )
            return f"Error generating summary: {err_msg}"

    @staticmethod
    def extract_document_keywords(
        file_path: str,
        llm_provider: str,
        llm_model: str,
        api_key: str = ""
    ) -> List[str]:
        """Extracts key topics/keywords from the document."""
        try:
            pages = DocumentProcessor.process_document(file_path)
            if not pages:
                return []
            
            # Take the first page which usually contains the title and abstract
            content = pages[0]["text"]
            
            prompt = (
                "Identify the 5 to 8 most relevant keywords or core topics covered in this text. "
                "Output them as a comma-separated list. Do not include any other text.\n\n"
                f"TEXT:\n{content}\n\n"
                "KEYWORDS:"
            )
            
            llm = LLMManager.get_llm(llm_provider, llm_model, api_key, temperature=0.1)
            response = llm.invoke(prompt)
            keywords_text = response.content.strip()
            
            # Parse comma-separated response
            keywords = [k.strip().replace("*", "").replace("-", "") for k in keywords_text.split(",")]
            # Filter out empty strings
            return [k for k in keywords if k]
        except Exception:
            return ["Information Retrieval", "Document Analysis", "AI Search"]

    @staticmethod
    def generate_suggested_questions(
        file_path: str,
        llm_provider: str,
        llm_model: str,
        api_key: str = ""
    ) -> List[str]:
        """Generates 3 suggested questions based on the document contents."""
        try:
            pages = DocumentProcessor.process_document(file_path)
            if not pages:
                return []
            
            # Take a sample page (first page or page 2 if it exists)
            sample_idx = min(1, len(pages) - 1)
            content = pages[sample_idx]["text"]
            
            prompt = (
                "Generate 3 natural questions that a reader would ask after reading the following text. "
                "Output each question on a new line, numbered 1 to 3. Do not include introductory text.\n\n"
                f"TEXT:\n{content}\n\n"
                "QUESTIONS:"
            )
            
            llm = LLMManager.get_llm(llm_provider, llm_model, api_key, temperature=0.5)
            response = llm.invoke(prompt)
            lines = response.content.strip().split("\n")
            
            questions = []
            for line in lines:
                cleaned = line.strip()
                # Remove leading numbering (e.g., "1. ", "2) ", etc.)
                if cleaned and (cleaned[0].isdigit() or cleaned[0] == '-'):
                    parts = cleaned.split(".", 1)
                    if len(parts) > 1:
                        cleaned = parts[1].strip()
                    else:
                        # try split with closing parenthesis
                        parts = cleaned.split(")", 1)
                        if len(parts) > 1:
                            cleaned = parts[1].strip()
                if cleaned:
                    questions.append(cleaned)
            return questions[:3]
        except Exception:
            return [
                "What are the main findings in this document?",
                "Can you explain the methodology used?",
                "What are the key conclusions?"
            ]

    # --- Conversation Export Operations ---

    @classmethod
    def export_chat_to_txt(cls, chat_id: int, output_path: str) -> bool:
        """Exports a conversation transcript to a plain text file."""
        try:
            chat = DatabaseManager.get_chat(chat_id)
            if not chat:
                return False
            messages = DatabaseManager.get_messages(chat_id)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"DocMind AI - Conversation Export: {chat['title']}\n")
                f.write(f"Export Date: {os.path.basename(output_path)}\n")
                f.write("=" * 60 + "\n\n")
                
                for msg in messages:
                    sender = "USER" if msg["sender"] == "user" else "DOCMIND AI"
                    f.write(f"[{sender}] ({msg.get('timestamp', 'N/A')}):\n")
                    f.write(f"{msg['content']}\n")
                    
                    if msg.get("sources"):
                        f.write("\nSources cited:\n")
                        for idx, src in enumerate(msg["sources"]):
                            f.write(f"  [{idx+1}] {src.get('document')} (Page {src.get('page')}):\n")
                            f.write(f"      Snippet: {src.get('snippet', '')[:120].strip()}...\n")
                    f.write("\n" + "-" * 40 + "\n\n")
            return True
        except Exception:
            return False

    @classmethod
    def export_chat_to_pdf(cls, chat_id: int, output_path: str) -> bool:
        """Exports a conversation transcript to a styled PDF using PyMuPDF (fitz) document writing API."""
        try:
            chat = DatabaseManager.get_chat(chat_id)
            if not chat:
                return False
            messages = DatabaseManager.get_messages(chat_id)
            
            doc = fitz.open()
            page = doc.new_page()
            
            y = 50
            margin = 50
            page_width = page.rect.width
            line_height = 14
            
            def add_paragraph(text: str, fontname: str = "helv", fontsize: int = 10, is_code: bool = False) -> None:
                nonlocal y, page
                
                # Dynamic text wrapper to prevent clipping at the right margin
                # Estimated average character width
                char_width = fontsize * 0.45
                max_chars = int((page_width - (2 * margin)) / char_width)
                
                words = text.split()
                lines = []
                current_line = []
                
                for word in words:
                    # Check length of the tested line
                    test_line = " ".join(current_line + [word])
                    if len(test_line) > max_chars:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                    else:
                        current_line.append(word)
                if current_line:
                    lines.append(" ".join(current_line))
                
                for line in lines:
                    if y > (page.rect.height - margin):
                        page = doc.new_page()
                        y = margin
                    # Print text line on page
                    page.insert_text((margin, y), line, fontname=fontname, fontsize=fontsize)
                    y += line_height
                y += 4  # spacing between blocks
 
            # Title
            add_paragraph(f"DocMind AI - Conversation Transcript", fontname="hebo", fontsize=16)
            add_paragraph(f"Chat Session: {chat['title']}", fontname="hebo", fontsize=11)
            y += 10
            
            for msg in messages:
                sender = "USER" if msg["sender"] == "user" else "DOCMIND AI"
                timestamp = msg.get("timestamp", "N/A")
                
                # Sender Header
                add_paragraph(f"{sender} ({timestamp}):", fontname="hebo", fontsize=10)
                
                # Message Body
                add_paragraph(msg["content"], fontname="helv", fontsize=9)
                
                # Citations if they exist
                if msg.get("sources"):
                    add_paragraph("Cited Sources:", fontname="heit", fontsize=8)
                    for src in msg["sources"]:
                        doc_name = src.get("document", "Unknown")
                        page_num = src.get("page", 1)
                        snippet = src.get("snippet", "")[:120].strip().replace("\n", " ")
                        add_paragraph(f"- {doc_name} (Pg {page_num}): \"{snippet}...\"", fontname="helv", fontsize=8)
                
                y += 12  # Space between conversation turns
            
            doc.save(output_path)
            doc.close()
            return True
        except Exception as e:
            logger.exception(f"PDF Export Error for Chat ID {chat_id}")
            return False
