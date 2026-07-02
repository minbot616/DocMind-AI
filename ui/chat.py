import os
import threading
from tkinter import filedialog, messagebox
import customtkinter
from database import DatabaseManager
from chat_manager import ChatManager
from rag_pipeline import RAGPipeline
from embeddings import EmbeddingManager
from vector_store import VectorStoreManager

class ChatFrame(customtkinter.CTkFrame):
    """The central chat workspace. Integrates multi-document filters, RAG queries, message history,
    citations drawer, suggestions, and transcript exports.
    """

    def __init__(self, parent: customtkinter.CTk, user_id: int):
        super().__init__(parent, fg_color="transparent")
        self.user_id = user_id
        
        # Chat Session State
        self.active_chat_id = None
        self.selected_doc_ids = []
        self.stop_generation_flag = False
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)  # Doc filter sidebar
        self.grid_rowconfigure(0, weight=1)    # Main workspace

        # --- Main Workspace (Left) ---
        self.workspace_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.workspace_frame.grid(row=0, column=0, sticky="nsew")
        self.workspace_frame.grid_columnconfigure(0, weight=1)
        self.workspace_frame.grid_rowconfigure(0, weight=0)  # Top Bar (Chat Title & Export)
        self.workspace_frame.grid_rowconfigure(1, weight=1)  # Chat History
        self.workspace_frame.grid_rowconfigure(2, weight=0)  # Input Box

        # Top Bar
        self.top_bar = customtkinter.CTkFrame(self.workspace_frame, height=50, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        
        self.title_lbl = customtkinter.CTkLabel(
            self.top_bar,
            text="New Conversation",
            font=customtkinter.CTkFont(family="Outfit", size=16, weight="bold")
        )
        self.title_lbl.pack(side="left", padx=20)

        # Export Options
        self.export_pdf_btn = customtkinter.CTkButton(
            self.top_bar,
            text="Export PDF",
            width=90,
            height=28,
            fg_color="transparent",
            border_color="#4F46E5",
            border_width=1,
            text_color=("#1F2937", "#E5E7EB"),
            hover_color=("gray90", "gray20"),
            command=self.export_pdf
        )
        self.export_pdf_btn.pack(side="right", padx=(5, 20), pady=10)

        self.export_txt_btn = customtkinter.CTkButton(
            self.top_bar,
            text="Export TXT",
            width=90,
            height=28,
            fg_color="transparent",
            border_color="gray",
            border_width=1,
            text_color=("#1F2937", "#E5E7EB"),
            hover_color=("gray90", "gray20"),
            command=self.export_txt
        )
        self.export_txt_btn.pack(side="right", padx=5, pady=10)

        # Chat History Scroll Area
        self.history_frame = customtkinter.CTkScrollableFrame(self.workspace_frame, fg_color="transparent")
        self.history_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Input Area (Bottom)
        self.input_frame = customtkinter.CTkFrame(self.workspace_frame, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 20))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.chat_input = customtkinter.CTkEntry(
            self.input_frame,
            placeholder_text="Ask DocMind AI a question...",
            height=45,
            corner_radius=10,
            font=customtkinter.CTkFont(family="Inter", size=13),
            fg_color=("#F8FAFC", "#000000"),
            border_color=("#E2E8F0", "#1C1C1C"),
            text_color=("#0F172A", "#F8FAFC"),
            placeholder_text_color="gray"
        )
        self.chat_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.chat_input.bind("<Return>", lambda e: self.send_message())

        self.send_btn = customtkinter.CTkButton(
            self.input_frame,
            text="Send",
            width=90,
            height=45,
            corner_radius=10,
            fg_color="#4F46E5",
            hover_color="#4338CA",
            font=customtkinter.CTkFont(family="Inter", size=13, weight="bold"),
            command=self.send_message
        )
        self.send_btn.grid(row=0, column=1)

        # Thinking spinner placeholder
        self.thinking_label = customtkinter.CTkLabel(
            self.workspace_frame,
            text="DocMind AI is searching documents and thinking...",
            font=customtkinter.CTkFont(family="Inter", size=11, slant="italic"),
            text_color="gray"
        )
        # Initially hidden

        # --- Document Filter Sidebar (Right) ---
        self.filter_sidebar = customtkinter.CTkFrame(self, width=220, corner_radius=0, fg_color=("#F1F5F9", "#0B0B0B"), border_width=0)
        self.filter_sidebar.grid(row=0, column=1, sticky="nsw")
        self.filter_sidebar.grid_columnconfigure(0, weight=1)
        self.filter_sidebar.grid_rowconfigure(1, weight=1)

        sidebar_title = customtkinter.CTkLabel(
            self.filter_sidebar,
            text="Search Context",
            font=customtkinter.CTkFont(family="Outfit", size=14, weight="bold")
        )
        sidebar_title.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        # Scrollable document checklist
        self.doc_scroll = customtkinter.CTkScrollableFrame(self.filter_sidebar, fg_color="transparent")
        self.doc_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        self.checkbox_vars = {}  # {doc_id: CTkCheckBoxVar}
        
        # Load chat history
        self.start_or_load_chat()
        self.refresh_document_filters()

    def refresh_document_filters(self):
        """Reloads check boxes representing documents context filters."""
        for widget in self.doc_scroll.winfo_children():
            widget.destroy()

        self.checkbox_vars.clear()
        docs = DatabaseManager.get_documents(self.user_id)

        if not docs:
            lbl = customtkinter.CTkLabel(
                self.doc_scroll,
                text="No documents uploaded.\nUpload files under Documents\ntab to query.",
                font=customtkinter.CTkFont(family="Inter", size=11),
                text_color="gray"
            )
            lbl.pack(pady=20)
            return

        # Add "Select All" checkbox
        self.all_var = customtkinter.BooleanVar(value=True)
        all_cb = customtkinter.CTkCheckBox(
            self.doc_scroll,
            text="Select All",
            font=customtkinter.CTkFont(family="Inter", size=12, weight="bold"),
            variable=self.all_var,
            command=self.toggle_all_docs
        )
        all_cb.pack(fill="x", pady=5)

        for doc in docs:
            var = customtkinter.BooleanVar(value=True)
            self.checkbox_vars[doc["id"]] = var
            
            # Truncate label
            display_name = doc["filename"]
            if len(display_name) > 22:
                display_name = display_name[:19] + "..."
                
            cb = customtkinter.CTkCheckBox(
                self.doc_scroll,
                text=display_name,
                font=customtkinter.CTkFont(family="Inter", size=11),
                variable=var,
                command=self.update_doc_selection
            )
            cb.pack(fill="x", pady=3)
            
        self.update_doc_selection()

    def toggle_all_docs(self):
        """Ticks or unticks all context checkboxes based on Select All state."""
        val = self.all_var.get()
        for doc_id, var in self.checkbox_vars.items():
            var.set(val)
        self.update_doc_selection()

    def update_doc_selection(self):
        """Reads selected checkboxes and updates state list."""
        self.selected_doc_ids = [
            doc_id for doc_id, var in self.checkbox_vars.items() if var.get()
        ]
        
        # Auto-update Select All checkbox if individual boxes are ticked
        if hasattr(self, 'all_var'):
            all_selected = all(var.get() for var in self.checkbox_vars.values()) if self.checkbox_vars else False
            self.all_var.set(all_selected)

    def start_or_load_chat(self, chat_id: int = None):
        """Loads old chat history bubbles or initializes a new chat."""
        # Clear bubbles
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        self.welcome_lbl = None
        self.suggestions_frame = None

        if chat_id:
            self.active_chat_id = chat_id
            chat = DatabaseManager.get_chat(chat_id)
            self.title_lbl.configure(text=chat["title"] if chat else "Conversation")
            
            # Load messages from SQLite
            messages = DatabaseManager.get_messages(chat_id)
            for msg in messages:
                self.render_message_bubble(msg["sender"], msg["content"], msg.get("sources"))
        else:
            # Lazy chat creation: keep active_chat_id as None until the user asks a question
            self.active_chat_id = None
            self.title_lbl.configure(text="New Chat")
            
            # Render Suggested Questions
            self.render_initial_suggestions()

    def render_initial_suggestions(self):
        """Renders helper buttons for quick questions if chat is empty."""
        self.welcome_lbl = customtkinter.CTkLabel(
            self.history_frame,
            text="Welcome to DocMind AI! How can I assist you?",
            font=customtkinter.CTkFont(family="Outfit", size=15, weight="bold"),
            pady=15
        )
        self.welcome_lbl.pack()

        self.suggestions_frame = customtkinter.CTkFrame(self.history_frame, fg_color="transparent")
        self.suggestions_frame.pack(pady=10)

        predefined = [
            "Summarize the main points of the document.",
            "What are the core findings and recommendations?",
            "List any important action items or next steps."
        ]

        for q in predefined:
            btn = customtkinter.CTkButton(
                self.suggestions_frame,
                text=q,
                fg_color=("gray95", "gray15"),
                text_color=("#111827", "#E5E7EB"),
                hover_color=("gray90", "gray20"),
                border_color=("#4F46E5", "#4338CA"),
                border_width=1,
                corner_radius=8,
                anchor="w",
                font=customtkinter.CTkFont(family="Inter", size=12),
                height=35,
                width=450,
                command=lambda question=q: self.input_predefined_question(question)
            )
            btn.pack(pady=4)

    def clear_suggestions(self):
        """Removes the welcome label and suggestion cards cleanly if they exist."""
        if hasattr(self, "welcome_lbl") and self.welcome_lbl:
            try:
                self.welcome_lbl.destroy()
            except Exception:
                pass
            self.welcome_lbl = None
        if hasattr(self, "suggestions_frame") and self.suggestions_frame:
            try:
                self.suggestions_frame.destroy()
            except Exception:
                pass
            self.suggestions_frame = None

    def input_predefined_question(self, question: str):
        """Inputs suggested question directly into prompt."""
        self.chat_input.delete(0, "end")
        self.chat_input.insert(0, question)
        self.send_message()

    def stop_generation(self):
        """Sets the stop flag to halt current streaming generation."""
        self.stop_generation_flag = True
        self.send_btn.configure(state="disabled", text="Stopping...")

    def send_message(self):
        """Submits prompt, records to db, and triggers the RAG thread."""
        query_text = self.chat_input.get().strip()
        if not query_text:
            return

        if not self.selected_doc_ids:
            messagebox.showwarning("Context Selection", "Please check at least one document on the right sidebar to use as search context.")
            return

        # 0. Lazy chat creation on first query!
        if self.active_chat_id is None:
            self.active_chat_id = ChatManager.create_new_chat(self.user_id, "New Chat")

        # Disable inputs & set send button to stop action
        self.chat_input.delete(0, "end")
        self.chat_input.configure(state="disabled")
        self.send_btn.configure(text="Stop", fg_color="#EF4444", hover_color="#DC2626", command=self.stop_generation)
        self.stop_generation_flag = False

        # 1. Render User Message bubble
        self.render_message_bubble("user", query_text)
        
        # Save User Message to db
        ChatManager.save_message(self.active_chat_id, "user", query_text)
        
        # Auto rename chat if title is default 'New Chat'
        chat = DatabaseManager.get_chat(self.active_chat_id)
        if chat and chat["title"] == "New Chat":
            new_title = query_text[:25] + "..." if len(query_text) > 25 else query_text
            ChatManager.rename_chat(self.active_chat_id, new_title)
            self.title_lbl.configure(text=new_title)

        # 2. Pre-render Assistant response bubble placeholder
        self.active_stream_text = "🔍 Searching documents & thinking..."
        self.active_stream_lbl, self.active_stream_card = self.render_message_bubble("assistant", self.active_stream_text)
        
        # 3. Spin worker thread for RAG to keep UI interactive
        threading.Thread(
            target=self.process_rag_query_thread,
            args=(query_text,),
            daemon=True
        ).start()

    def process_rag_query_thread(self, query_text: str):
        """Worker thread executing vector retrieval and LLM querying with streaming updates."""
        settings = DatabaseManager.get_settings(self.user_id)
        provider = settings.get("llm_provider", "Ollama")
        model = settings.get("llm_model", "llama3")
        api_key = settings.get("api_key", "")
        embed_name = settings.get("embedding_model", "all-MiniLM-L6-v2")
        temp = settings.get("temperature", 0.2)
        max_tok = settings.get("max_tokens", 1024)

        # Keep loading placeholder visible during document index retrieval
        def on_token(token):
            self.after(0, lambda t=token: self.append_stream_token(t))

        duration = 0.0
        try:
            # 1. Load active embedding model
            embed_model = EmbeddingManager.get_embeddings(embed_name, api_key)
            
            # 2. Load and merge vector stores for selected documents
            vector_store = VectorStoreManager.load_merged_vector_store(
                user_id=self.user_id,
                doc_ids=self.selected_doc_ids,
                embedding_model=embed_model
            )
            
            if not vector_store:
                answer = "Error: The vector indexes for the selected documents could not be loaded. Please re-upload or check your database settings."
                citations = []
            else:
                # 3. Run search & LLM
                chat_history = ChatManager.get_chat_messages(self.active_chat_id)
                # Drop the last user message we just added to database to prevent redundancy in LLM history formatting
                if chat_history and chat_history[-1]["sender"] == "user":
                    chat_history = chat_history[:-1]
                    
                answer, citations, duration = RAGPipeline.query(
                    query_text=query_text,
                    vector_store=vector_store,
                    llm_provider=provider,
                    llm_model=model,
                    api_key=api_key,
                    chat_history=chat_history,
                    stream_callback=on_token,
                    stop_signal=lambda: self.stop_generation_flag,
                    temperature=temp,
                    max_tokens=max_tok
                )
                
        except Exception as e:
            from utils import logger
            logger.exception("RAG pipeline query execution failed.")
            err_msg = str(e)
            if "10061" in err_msg or "Connection refused" in err_msg or "actively refused it" in err_msg:
                answer = (
                    "⚠️ Connection Error: Could not connect to the active LLM provider.\n\n"
                    "If you are using Ollama, please ensure that the Ollama desktop app is running locally (http://localhost:11434). "
                    "If you are using a cloud provider (like OpenAI or Groq), please verify your internet connection and check that your API key is correctly configured in the **Settings** tab."
                )
            elif "api_key" in err_msg.lower() or "unauthorized" in err_msg.lower() or "api key" in err_msg.lower():
                answer = (
                    "⚠️ Authentication Error: Invalid or missing API key for the selected provider.\n\n"
                    "Please check your settings in the **Settings** tab and verify your API keys are correct."
                )
            else:
                answer = f"An unexpected pipeline error occurred: {err_msg}"
            citations = []
            duration = 0.0

        # Return to main thread to update UI and save to DB
        self.after(0, lambda: self.on_rag_complete(answer, citations, duration))

    def append_stream_token(self, token: str):
        """Thread-safe stream token appender."""
        if not self.stop_generation_flag:
            # Clear searching placeholder text on first token arrival
            if self.active_stream_text == "🔍 Searching documents & thinking...":
                self.active_stream_text = ""
                self.active_stream_lbl.configure(text="")
                
            self.active_stream_text += token
            self.active_stream_lbl.configure(text=self.active_stream_text)
            self.history_frame.update_idletasks()
            self.history_frame._parent_canvas.yview_moveto(1.0)

    def on_rag_complete(self, answer: str, citations: list, duration: float):
        """Saves assistant response and updates chat history bubbles."""
        # Overwrite content text to final response (in case stopped early)
        if self.stop_generation_flag:
            answer = self.active_stream_text + " *[Generation Stopped]*"
            
        self.active_stream_lbl.configure(text=answer)
        
        # Save to DB
        ChatManager.save_message(self.active_chat_id, "assistant", answer, citations, duration)

        # Restore input state
        self.send_btn.configure(text="Send", fg_color="#4F46E5", hover_color="#4338CA", command=self.send_message, state="normal")
        self.chat_input.configure(state="normal")
        self.chat_input.focus()

        # Render Citations under pre-created card if any
        if citations:
            citations_drawer = customtkinter.CTkFrame(self.active_stream_card, fg_color="transparent")
            citations_drawer.pack(fill="x", padx=15, pady=(0, 8))
            self.create_citations_toggle(citations_drawer, citations)

        # Scroll to bottom
        self.history_frame.update_idletasks()
        self.history_frame._parent_canvas.yview_moveto(1.0)

    def render_message_bubble(self, sender: str, content: str, citations: list = None):
        """Appends a styled text block representation of a message inside history scroll."""
        # Clear suggestions if they exist on first real message
        self.clear_suggestions()

        # Outer bubble frame
        bubble = customtkinter.CTkFrame(self.history_frame, fg_color="transparent")
        bubble.pack(fill="x", pady=8)

        # Bubble card alignment
        if sender == "user":
            card = customtkinter.CTkFrame(bubble, fg_color=("#4F46E5", "#6366F1"), corner_radius=12) # Indigo User
            card.pack(side="right", padx=(50, 10))
            text_color = "#FFFFFF"
            align = "e"
            sender_name = "👤 You"
        else:
            card = customtkinter.CTkFrame(bubble, fg_color=("#FFFFFF", "#0B0B0B"), border_width=1, border_color=("#E2E8F0", "#1C1C1C"), corner_radius=12) # Sleek slate Assistant
            card.pack(side="left", padx=(10, 50))
            text_color = ("#0F172A", "#F8FAFC")
            align = "w"
            sender_name = "🧠 DocMind AI"

        # Sender row frame
        sender_row = customtkinter.CTkFrame(card, fg_color="transparent")
        sender_row.pack(fill="x", padx=15, pady=(8, 2))

        # Sender text tag
        lbl_sender = customtkinter.CTkLabel(
            sender_row,
            text=sender_name,
            font=customtkinter.CTkFont(family="Inter", size=10, weight="bold"),
            text_color="#E0E7FF" if sender == "user" else "#818CF8"
        )
        lbl_sender.pack(side="left")

        # Small Copy Button
        copy_btn = customtkinter.CTkButton(
            sender_row,
            text="📋 Copy",
            width=45,
            height=16,
            font=customtkinter.CTkFont(family="Inter", size=9),
            fg_color="transparent",
            text_color="#E0E7FF" if sender == "user" else "#818CF8",
            hover_color=("#3730A3", "#312E81") if sender == "user" else ("#E2E8F0", "#334155"),
            corner_radius=4
        )
        copy_btn.pack(side="right", padx=(10, 0))

        # Content Text
        # Estimated wrap spacing
        lbl_content = customtkinter.CTkLabel(
            card,
            text=content,
            font=customtkinter.CTkFont(family="Inter", size=12),
            text_color=text_color,
            justify="left",
            anchor="w",
            wraplength=450
        )
        lbl_content.pack(anchor="w", padx=15, pady=(2, 10))

        # Dynamically fetch label text when Copy is clicked
        copy_btn.configure(command=lambda lbl=lbl_content, b=copy_btn: self.copy_to_clipboard(lbl.cget("text"), b))

        # Citations drawer (only for assistant responses)
        if sender == "assistant" and citations:
            citations_drawer = customtkinter.CTkFrame(card, fg_color="transparent")
            citations_drawer.pack(fill="x", padx=15, pady=(0, 8))
            
            # Interactive toggle button
            self.create_citations_toggle(citations_drawer, citations)

        # Scroll to bottom
        self.history_frame.update_idletasks()
        self.history_frame._parent_canvas.yview_moveto(1.0)
        
        return lbl_content, card

    def create_citations_toggle(self, parent: customtkinter.CTkFrame, citations: list):
        """Creates a collapsible panel for viewing source snippets."""
        sources_card = customtkinter.CTkFrame(parent, fg_color=("gray90", "gray14"), corner_radius=6)
        
        def toggle_view():
            if sources_card.winfo_ismapped():
                sources_card.pack_forget()
                btn.configure(text=f"Show Citations ({len(citations)})")
            else:
                sources_card.pack(fill="x", pady=(5, 0))
                btn.configure(text="Hide Citations")
            self.history_frame.update_idletasks()
            self.history_frame._parent_canvas.yview_moveto(1.0)

        btn = customtkinter.CTkButton(
            parent,
            text=f"Show Citations ({len(citations)})",
            font=customtkinter.CTkFont(family="Inter", size=10, weight="bold"),
            fg_color="transparent",
            text_color="#818CF8",
            hover_color=("gray90", "gray16"),
            height=20,
            width=100,
            command=toggle_view
        )
        btn.pack(side="left")

        # Retrieve absolute file paths to allow click-to-open
        docs = DatabaseManager.get_documents(self.user_id)
        doc_path_map = {d["filename"]: d["file_path"] for d in docs}

        # Fill hidden citations card
        for idx, src in enumerate(citations):
            doc_name = src.get("document", "Unknown")
            page_num = src.get("page", 1)
            score = src.get("score", 1.0)
            score_percentage = f"{int(score * 100)}%"
            
            # Create citation details header
            lbl_src = customtkinter.CTkLabel(
                sources_card,
                text=f"[{idx+1}] {doc_name} (Page {page_num}) - Match Confidence: {score_percentage}",
                font=customtkinter.CTkFont(family="Inter", size=10, weight="bold", underline=True),
                text_color=("#4F46E5", "#818CF8"),
                anchor="w",
                cursor="hand2"
            )
            lbl_src.pack(fill="x", padx=10, pady=(6, 1))
            
            # Click event bindings
            doc_path = doc_path_map.get(doc_name)
            if doc_path:
                lbl_src.bind("<Button-1>", lambda e, p=doc_path, pn=page_num: self.open_pdf_viewer(p, pn))

            lbl_snippet = customtkinter.CTkLabel(
                sources_card,
                text=f"\"{src['snippet'][:160]}...\"",
                font=customtkinter.CTkFont(family="Inter", size=10, slant="italic"),
                text_color="gray",
                anchor="w",
                justify="left",
                wraplength=400
            )
            lbl_snippet.pack(fill="x", padx=15, pady=(1, 6))

    def open_pdf_viewer(self, filepath: str, page_num: int):
        """Launches the built-in visual PDF page modal."""
        from ui.viewer import PDFPageViewer
        PDFPageViewer(self, filepath, page_num)

    # --- Transcript Exports ---

    def export_pdf(self):
        """Triggers ChatManager to write history to PDF file."""
        if not self.active_chat_id:
            return
        
        path = filedialog.asksaveasfilename(
            title="Export Chat as PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")]
        )
        if path:
            success = ChatManager.export_chat_to_pdf(self.active_chat_id, path)
            if success:
                messagebox.showinfo("Export Successful", f"Transcript saved to {os.path.basename(path)}")
            else:
                messagebox.showerror("Export Failed", "Could not export transcript to PDF.")

    def export_txt(self):
        """Triggers ChatManager to write history to TXT file."""
        if not self.active_chat_id:
            return
        
        path = filedialog.asksaveasfilename(
            title="Export Chat as Text",
            defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt")]
        )
        if path:
            success = ChatManager.export_chat_to_txt(self.active_chat_id, path)
            if success:
                messagebox.showinfo("Export Successful", f"Transcript saved to {os.path.basename(path)}")
            else:
                messagebox.showerror("Export Failed", "Could not export transcript to Text.")

    def copy_to_clipboard(self, text: str, btn: customtkinter.CTkButton):
        """Copies text content to clipboard and updates button text as feedback."""
        from utils import copy_to_clipboard
        copy_to_clipboard(self, text, btn)
