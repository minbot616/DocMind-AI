import os
import shutil
import threading
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog
import customtkinter
from database import DatabaseManager
from document_processor import DocumentProcessor
from embeddings import EmbeddingManager
from vector_store import VectorStoreManager
from chat_manager import ChatManager
from utils import allowed_file, format_size, get_file_extension, open_document

# Local documents storage directory
DOCUMENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents")
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

class UploadFrame(customtkinter.CTkFrame):
    """Provides document management: file selector, threaded indexing, progress tracker, and metadata tables."""

    def __init__(self, parent: customtkinter.CTk, user_id: int):
        super().__init__(parent, fg_color="transparent")
        self.user_id = user_id
        
        # User-specific directory
        self.user_docs_dir = os.path.join(DOCUMENTS_DIR, str(user_id))
        os.makedirs(self.user_docs_dir, exist_ok=True)

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # Upload Action Box / Progress
        self.grid_rowconfigure(2, weight=1)  # Document List Table

        # 1. Header
        header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=30, pady=(20, 10), sticky="ew")
        
        header_label = customtkinter.CTkLabel(
            header_frame,
            text="Document Repository",
            font=customtkinter.CTkFont(family="Outfit", size=24, weight="bold")
        )
        header_label.pack(side="left")

        # 2. Upload Box
        self.upload_card = customtkinter.CTkFrame(self, height=120, corner_radius=12, fg_color=("#FFFFFF", "#0B0B0B"), border_width=1, border_color=("#E2E8F0", "#1C1C1C"))
        self.upload_card.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        self.upload_card.grid_columnconfigure(0, weight=1)
        self.upload_card.grid_rowconfigure(0, weight=1)

        self.upload_inner = customtkinter.CTkFrame(self.upload_card, fg_color="transparent")
        self.upload_inner.grid(row=0, column=0, padx=20, pady=15, sticky="nsew")
        self.upload_inner.grid_columnconfigure(0, weight=1)
        
        self.upload_btn = customtkinter.CTkButton(
            self.upload_inner,
            text="Select Files to Upload",
            font=customtkinter.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            width=200,
            height=38,
            command=self.select_files
        )
        self.upload_btn.grid(row=0, column=0, pady=(5, 5))

        self.support_lbl = customtkinter.CTkLabel(
            self.upload_inner,
            text="Supported formats: PDF, DOCX, TXT, LOG, MD (Max 10MB)",
            font=customtkinter.CTkFont(family="Inter", size=11),
            text_color="gray"
        )
        self.support_lbl.grid(row=1, column=0)

        # Progress elements (initially hidden)
        self.progress_frame = customtkinter.CTkFrame(self.upload_card, fg_color="transparent")
        self.progress_lbl = customtkinter.CTkLabel(
            self.progress_frame,
            text="Extracting text and building vector index...",
            font=customtkinter.CTkFont(family="Inter", size=12)
        )
        self.progress_lbl.pack(fill="x", pady=(5, 2))
        
        self.progress_bar = customtkinter.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)

        # 3. Document List Table Container
        self.table_container = customtkinter.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, padx=30, pady=(10, 20), sticky="nsew")
        self.table_container.grid_columnconfigure(0, weight=1)
        self.table_container.grid_rowconfigure(0, weight=0)  # Table Headers
        self.table_container.grid_rowconfigure(1, weight=1)  # Table Rows (Scrollable)

        # Table Header Row
        headers = ["Filename", "Pages", "Chunks", "Status", "Size", "Uploaded At", "Actions"]
        widths = [200, 60, 60, 75, 70, 130, 320]
        
        header_row = customtkinter.CTkFrame(self.table_container, height=35, corner_radius=6, fg_color=("gray90", "gray10"))
        header_row.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        header_row.grid_propagate(False)
        
        for idx, (title, w) in enumerate(zip(headers, widths)):
            lbl = customtkinter.CTkLabel(
                header_row,
                text=title,
                font=customtkinter.CTkFont(family="Inter", size=12, weight="bold"),
                anchor="w",
                width=w
            )
            lbl.pack(side="left", padx=10)

        # Table Row Frame (Scrollable)
        self.rows_frame = customtkinter.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.rows_frame.grid(row=1, column=0, sticky="nsew")

        # Load existing documents
        self.load_documents()

    def select_files(self):
        """Opens file dialog for document selection."""
        filepaths = filedialog.askopenfilenames(
            title="Select Documents",
            filetypes=[("Documents", "*.pdf;*.docx;*.txt;*.log;*.md")]
        )
        if filepaths:
            # Filter valid extensions
            valid_paths = [path for path in filepaths if allowed_file(os.path.basename(path))]
            invalid_paths = [path for path in filepaths if not allowed_file(os.path.basename(path))]
            
            if invalid_paths:
                invalid_names = ", ".join([os.path.basename(p) for p in invalid_paths])
                messagebox.showwarning("Skipped Files", f"The following files are unsupported:\n{invalid_names}")
                
            if valid_paths:
                # Start threaded ingestion
                self.show_progress_mode(True)
                threading.Thread(
                    target=self.process_files_thread,
                    args=(valid_paths,),
                    daemon=True
                ).start()

    def show_progress_mode(self, show: bool):
        """Toggles between Select File button and Processing Progress indicator."""
        if show:
            self.upload_inner.grid_forget()
            self.progress_frame.grid(row=0, column=0, padx=20, pady=15, sticky="nsew")
        else:
            self.progress_frame.grid_forget()
            self.upload_inner.grid(row=0, column=0, padx=20, pady=15, sticky="nsew")

    def process_files_thread(self, filepaths: list, reindex_doc_id: int = None):
        """Worker thread executing document ingestion and vectorization."""
        total_files = len(filepaths)
        settings = DatabaseManager.get_settings(self.user_id)
        embedding_model_name = settings.get("embedding_model", "all-MiniLM-L6-v2")
        api_key = settings.get("api_key", "")
        chunk_size = settings.get("chunk_size", 500)
        chunk_overlap = settings.get("chunk_overlap", 50)
        
        # Load embedding model in thread to avoid freezing GUI
        try:
            self.update_progress_ui(0, "Loading Embedding Model...")
            embed_model = EmbeddingManager.get_embeddings(embedding_model_name, api_key)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Embedding Error", f"Failed to load embedding model: {str(e)}"))
            self.after(0, lambda: self.show_progress_mode(False))
            return

        for idx, path in enumerate(filepaths):
            filename = os.path.basename(path)
            self.update_progress_ui(
                (idx / total_files),
                f"Ingesting ({idx+1}/{total_files}): {filename}..."
            )
            
            try:
                if reindex_doc_id:
                    # Re-indexing an existing file: reuse metadata
                    doc_id = reindex_doc_id
                    dest_path = path
                    file_size = os.path.getsize(dest_path)
                else:
                    # 1. Copy file to local workspace storage
                    dest_path = os.path.join(self.user_docs_dir, filename)
                    # Handle unique naming collision
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(dest_path):
                        filename = f"{base}_{counter}{ext}"
                        dest_path = os.path.join(self.user_docs_dir, filename)
                        counter += 1
                    shutil.copy(path, dest_path)
                    
                    # 2. Get file size
                    file_size = os.path.getsize(dest_path)
                    file_type = get_file_extension(filename).replace(".", "").upper()
                    
                    # 3. Create document record in database
                    doc_id = DatabaseManager.add_document(
                        user_id=self.user_id,
                        filename=filename,
                        file_path=dest_path,
                        file_type=file_type,
                        file_size=file_size
                    )
                
                # 4. Extract pages text
                self.update_progress_ui(
                    ((idx + 0.3) / total_files),
                    f"Parsing text ({idx+1}/{total_files}): {filename}..."
                )
                pages = DocumentProcessor.process_document(dest_path)
                
                # 5. Chunk text
                self.update_progress_ui(
                    ((idx + 0.6) / total_files),
                    f"Vectorizing chunks ({idx+1}/{total_files}): {filename}..."
                )
                chunks = DocumentProcessor.chunk_documents(pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                
                # Update page and chunk counts
                DatabaseManager.update_document_stats(doc_id, len(pages), len(chunks))
                
                # 6. Generate Embeddings & FAISS Vector store
                VectorStoreManager.create_vector_store(
                    user_id=self.user_id,
                    doc_id=doc_id,
                    chunks=chunks,
                    embedding_model=embed_model
                )
                
            except Exception as e:
                # Log error or warn user
                self.after(0, lambda fn=filename, err=e: messagebox.showerror(
                    "Processing Error",
                    f"Failed to ingest file '{fn}': {str(err)}"
                ))
        
        # Complete
        self.update_progress_ui(1.0, "Completed!")
        self.after(1000, lambda: self.show_progress_mode(False))
        self.after(1100, self.load_documents)

    def update_progress_ui(self, value: float, text: str):
        """Thread-safe UI updater."""
        self.after(0, lambda: self.progress_bar.set(value))
        self.after(0, lambda: self.progress_lbl.configure(text=text))

    def load_documents(self):
        """Refreshes the document rows in the scrollable layout."""
        # Clear existing rows
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        docs = DatabaseManager.get_documents(self.user_id)
        if not docs:
            no_docs_lbl = customtkinter.CTkLabel(
                self.rows_frame,
                text="No documents in repository. Upload files to get started!",
                font=customtkinter.CTkFont(family="Inter", size=13),
                text_color="gray"
            )
            no_docs_lbl.pack(pady=40)
            return

        # Add document rows
        for doc in docs:
            self.create_document_row(doc)

    def create_document_row(self, doc: dict):
        """Builds a responsive row representing a single document."""
        row_frame = customtkinter.CTkFrame(self.rows_frame, height=45, corner_radius=8, fg_color=("#FFFFFF", "#0B0B0B"), border_width=1, border_color=("#E2E8F0", "#1C1C1C"))
        row_frame.pack(fill="x", pady=4, ipady=2)
        
        # Grid/pack columns
        # Truncate long filenames
        filename = doc["filename"]
        if len(filename) > 28:
            filename = filename[:25] + "..."
            
        lbl_name = customtkinter.CTkLabel(row_frame, text=filename, font=customtkinter.CTkFont(family="Inter", size=12), width=200, anchor="w")
        lbl_name.pack(side="left", padx=10)
        
        lbl_pages = customtkinter.CTkLabel(row_frame, text=str(doc.get("pages", 0)), font=customtkinter.CTkFont(family="Inter", size=11), width=60, anchor="w")
        lbl_pages.pack(side="left", padx=10)
        
        lbl_chunks = customtkinter.CTkLabel(row_frame, text=str(doc.get("chunks", 0)), font=customtkinter.CTkFont(family="Inter", size=11), width=60, anchor="w")
        lbl_chunks.pack(side="left", padx=10)

        lbl_status = customtkinter.CTkLabel(row_frame, text=doc.get("status", "processed"), font=customtkinter.CTkFont(family="Inter", size=11), width=75, anchor="w")
        lbl_status.pack(side="left", padx=10)
        
        lbl_size = customtkinter.CTkLabel(row_frame, text=format_size(doc["file_size"]), font=customtkinter.CTkFont(family="Inter", size=11), width=70, anchor="w")
        lbl_size.pack(side="left", padx=10)
        
        # Formatting timestamp
        try:
            dt = datetime.strptime(doc["upload_time"], "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%b %d, %Y %H:%M")
        except Exception:
            time_str = doc["upload_time"]
            
        lbl_date = customtkinter.CTkLabel(row_frame, text=time_str, font=customtkinter.CTkFont(family="Inter", size=11), width=130, anchor="w")
        lbl_date.pack(side="left", padx=10)

        # Actions Button Frame
        actions_frame = customtkinter.CTkFrame(row_frame, fg_color="transparent")
        actions_frame.pack(side="right", padx=10)

        # Open
        open_btn = customtkinter.CTkButton(actions_frame, text="Open", font=customtkinter.CTkFont(family="Inter", size=11), fg_color="#10B981", hover_color="#059669", text_color="#FFFFFF", width=42, height=25, command=lambda d=doc: self.open_document(d))
        open_btn.pack(side="left", padx=2)

        # Insights
        insights_btn = customtkinter.CTkButton(actions_frame, text="Insights", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), fg_color="#6366F1", hover_color="#4F46E5", text_color="#FFFFFF", width=55, height=25, command=lambda d=doc: self.show_ai_insights(d))
        insights_btn.pack(side="left", padx=2)

        # Re-index
        reindex_btn = customtkinter.CTkButton(actions_frame, text="Index", font=customtkinter.CTkFont(family="Inter", size=11), fg_color="#F59E0B", hover_color="#D97706", text_color="#FFFFFF", width=42, height=25, command=lambda d=doc: self.re_index_document(d))
        reindex_btn.pack(side="left", padx=2)

        # Metadata
        meta_btn = customtkinter.CTkButton(actions_frame, text="Meta", font=customtkinter.CTkFont(family="Inter", size=11), fg_color="transparent", text_color=("#111827", "#E5E7EB"), border_color=("#4F46E5", "#6366F1"), border_width=1.5, hover_color=("gray90", "gray15"), width=42, height=25, command=lambda d=doc: self.view_metadata(d))
        meta_btn.pack(side="left", padx=2)

        # Rename
        rename_btn = customtkinter.CTkButton(actions_frame, text="Rename", font=customtkinter.CTkFont(family="Inter", size=11), fg_color="transparent", text_color=("#111827", "#E5E7EB"), hover_color=("gray90", "gray15"), width=52, height=25, command=lambda d=doc: self.rename_document(d))
        rename_btn.pack(side="left", padx=2)

        # Delete
        delete_btn = customtkinter.CTkButton(actions_frame, text="Delete", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), fg_color="transparent", text_color="#EF4444", hover_color=("gray90", "gray15"), width=48, height=25, command=lambda d=doc: self.delete_document(d))
        delete_btn.pack(side="left", padx=2)

    def open_document(self, doc: dict):
        """Opens document using default OS application."""
        open_document(doc["file_path"])

    def view_metadata(self, doc: dict):
        """Shows detailed document metadata inside a popup modal."""
        meta_window = customtkinter.CTkToplevel(self)
        meta_window.title(f"Metadata - {doc['filename']}")
        meta_window.geometry("450x320")
        meta_window.grab_set()

        scroll = customtkinter.CTkScrollableFrame(meta_window, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        details = [
            ("Filename", doc["filename"]),
            ("File Path", doc["file_path"]),
            ("File Type", doc["file_type"]),
            ("File Size", format_size(doc["file_size"])),
            ("Pages", str(doc.get("pages", 0))),
            ("Chunks", str(doc.get("chunks", 0))),
            ("Embedding Status", doc.get("status", "processed")),
            ("Uploaded At", doc["upload_time"])
        ]

        for idx, (label, val) in enumerate(details):
            row = customtkinter.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=4)
            lbl = customtkinter.CTkLabel(row, text=f"{label}:", font=customtkinter.CTkFont(family="Inter", size=12, weight="bold"), width=120, anchor="w")
            lbl.pack(side="left")
            val_lbl = customtkinter.CTkLabel(row, text=val, font=customtkinter.CTkFont(family="Inter", size=12), anchor="w", wraplength=250, justify="left")
            val_lbl.pack(side="left", fill="x", expand=True)

    def re_index_document(self, doc: dict):
        """Re-indexes the document chunking and vector store."""
        confirm = messagebox.askyesno(
            "Re-index Document",
            f"Are you sure you want to re-index '{doc['filename']}' using current settings?",
        )
        if confirm:
            self.show_progress_mode(True)
            threading.Thread(
                target=self.process_files_thread,
                args=([doc["file_path"]], doc["id"]),
                daemon=True
            ).start()

    def rename_document(self, doc: dict):
        """Asks user for a new name and updates storage + db."""
        current_name = doc["filename"]
        new_name = simpledialog.askstring("Rename Document", f"Enter new name for {current_name}:", initialvalue=current_name)
        
        if new_name and new_name.strip() != current_name:
            new_name = new_name.strip()
            # Ensure extension is maintained
            old_ext = os.path.splitext(current_name)[1]
            new_ext = os.path.splitext(new_name)[1]
            if old_ext.lower() != new_ext.lower():
                new_name += old_ext
                
            old_path = doc["file_path"]
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            
            try:
                # Rename on filesystem
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                
                # Update db
                DatabaseManager.rename_document(doc["id"], new_name)
                # Note: Vector stores don't need recreating because their folder matches doc_id, not document filename,
                # though some metadata inside vectors could technically contain filename, which is okay since it's just descriptive.
                
                self.load_documents()
                messagebox.showinfo("Success", f"Document renamed to {new_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename document: {str(e)}")

    def delete_document(self, doc: dict):
        """Removes the document from filesystem, databases, and deletes the FAISS vector stores."""
        confirm = messagebox.askyesno(
            "Delete Document",
            f"Are you sure you want to permanently delete '{doc['filename']}'?",
            icon="warning"
        )
        if confirm:
            doc_id = doc["id"]
            # 1. Delete vector store folder
            VectorStoreManager.delete_vector_store(self.user_id, doc_id)
            
            # 2. Delete source file
            if os.path.exists(doc["file_path"]):
                try:
                    os.remove(doc["file_path"])
                except Exception:
                    pass
            
            # 3. Delete DB record
            DatabaseManager.delete_document(doc_id)
            
            self.load_documents()
            messagebox.showinfo("Success", "Document deleted successfully.")

    def show_ai_insights(self, doc: dict):
        """Fetches settings and opens a modal dialogue containing AI-generated summary, keywords, and questions."""
        # Quick check if provider configured
        settings = DatabaseManager.get_settings(self.user_id)
        provider = settings.get("llm_provider", "Ollama")
        model = settings.get("llm_model", "llama3")
        api_key = settings.get("api_key", "")

        # Open Custom Tkinter Popup
        insights_window = customtkinter.CTkToplevel(self)
        insights_window.title(f"AI Insights - {doc['filename']}")
        insights_window.geometry("600x550")
        insights_window.grab_set()  # Modal focus
        
        # Layout inside modal
        insights_window.grid_columnconfigure(0, weight=1)
        insights_window.grid_rowconfigure(0, weight=1)

        scroll_frame = customtkinter.CTkScrollableFrame(insights_window, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Loading text boxes
        summary_card = self.create_insight_box(scroll_frame, "Executive Summary", "Generating...")
        keywords_card = self.create_insight_box(scroll_frame, "Core Keywords / Topics", "Generating...")
        questions_card = self.create_insight_box(scroll_frame, "Suggested Questions to Ask", "Generating...")

        # Worker thread to fetch insights from LLM
        def fetch_insights():
            # 1. Summary
            summary = ChatManager.generate_document_summary(doc["file_path"], provider, model, api_key)
            self.after(0, lambda text=summary: summary_card.configure(text=text))

            # 2. Keywords
            keywords = ChatManager.extract_document_keywords(doc["file_path"], provider, model, api_key)
            keywords_str = ", ".join(keywords) if keywords else "None found."
            self.after(0, lambda text=keywords_str: keywords_card.configure(text=text))

            # 3. Questions
            questions = ChatManager.generate_suggested_questions(doc["file_path"], provider, model, api_key)
            questions_str = "\n".join([f"• {q}" for q in questions]) if questions else "None generated."
            self.after(0, lambda text=questions_str: questions_card.configure(text=text))

        threading.Thread(target=fetch_insights, daemon=True).start()

    def create_insight_box(self, parent: customtkinter.CTkFrame, title: str, initial_text: str) -> customtkinter.CTkLabel:
        """Helper to draw a styled insights textbox inside the modal."""
        box = customtkinter.CTkFrame(parent, corner_radius=8, fg_color=("gray95", "gray10"))
        box.pack(fill="x", pady=10, ipady=5)
        
        # Header Row Frame
        header_row = customtkinter.CTkFrame(box, fg_color="transparent")
        header_row.pack(fill="x", padx=15, pady=(8, 2))

        title_lbl = customtkinter.CTkLabel(
            header_row,
            text=title,
            font=customtkinter.CTkFont(family="Inter", size=13, weight="bold"),
            text_color="#4F46E5",
            anchor="w"
        )
        title_lbl.pack(side="left")

        # Copy Button
        copy_btn = customtkinter.CTkButton(
            header_row,
            text="📋 Copy",
            width=50,
            height=18,
            font=customtkinter.CTkFont(family="Inter", size=9),
            fg_color="transparent",
            text_color="#4F46E5",
            hover_color=("gray90", "gray20"),
            corner_radius=4
        )
        copy_btn.pack(side="right")
        
        content_lbl = customtkinter.CTkLabel(
            box,
            text=initial_text,
            font=customtkinter.CTkFont(family="Inter", size=12),
            anchor="w",
            justify="left",
            wraplength=520
        )
        content_lbl.pack(fill="x", padx=15, pady=(2, 8))
        
        copy_btn.configure(command=lambda: self.copy_to_clipboard(content_lbl.cget("text"), copy_btn))
        
        return content_lbl

    def copy_to_clipboard(self, text: str, btn: customtkinter.CTkButton):
        """Copies text content to clipboard and updates button text as feedback."""
        from utils import copy_to_clipboard
        copy_to_clipboard(self, text, btn)
