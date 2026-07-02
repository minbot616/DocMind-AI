import os
import threading
from tkinter import messagebox
import customtkinter
from database import DatabaseManager
from embeddings import EmbeddingManager
from vector_store import VectorStoreManager
from ui.components import MetricCard
from utils import format_size, open_document, copy_to_clipboard

class DashboardFrame(customtkinter.CTkFrame):
    """The central overview screen. Displays corpus metrics, system configuration cards,
    and a unified semantic search engine across the document library.
    """

    def __init__(self, parent: customtkinter.CTk, user_id: int, switch_tab_callback):
        super().__init__(parent, fg_color="transparent")
        self.user_id = user_id
        self.switch_tab = switch_tab_callback

        # Grid config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # Metrics Cards
        self.grid_rowconfigure(2, weight=1)  # Semantic Search Area

        # 1. Header
        header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=30, pady=(20, 15), sticky="ew")
        
        header_label = customtkinter.CTkLabel(
            header_frame,
            text="Workspace Dashboard",
            font=customtkinter.CTkFont(family="Outfit", size=24, weight="bold")
        )
        header_label.pack(side="left")

        # 2. Metrics Cards Row
        self.metrics_container = customtkinter.CTkFrame(self, fg_color="transparent")
        self.metrics_container.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        self.metrics_container.grid_columnconfigure((0, 1, 2), weight=1)

        # 3. Semantic Search Drawer
        self.search_card = customtkinter.CTkFrame(self, corner_radius=12, fg_color=("#FFFFFF", "#0B0B0B"), border_width=1, border_color=("#E2E8F0", "#1C1C1C"))
        self.search_card.grid(row=2, column=0, padx=30, pady=(15, 20), sticky="nsew")
        self.search_card.grid_columnconfigure(0, weight=1)
        self.search_card.grid_rowconfigure(0, weight=0)  # Input / Button row
        self.search_card.grid_rowconfigure(1, weight=1)  # Scroll results

        # Search Controls Row
        search_control = customtkinter.CTkFrame(self.search_card, fg_color="transparent")
        search_control.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        search_control.grid_columnconfigure(0, weight=1)

        self.search_input = customtkinter.CTkEntry(
            search_control,
            placeholder_text="Search for facts or topics across all your documents semantically...",
            height=40,
            corner_radius=8,
            font=customtkinter.CTkFont(family="Inter", size=13),
            fg_color=("#F8FAFC", "#000000"),
            border_color=("#E2E8F0", "#1C1C1C"),
            text_color=("#0F172A", "#F8FAFC"),
            placeholder_text_color="gray"
        )
        self.search_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_input.bind("<Return>", lambda e: self.perform_search())

        self.search_btn = customtkinter.CTkButton(
            search_control,
            text="Semantic Search",
            font=customtkinter.CTkFont(family="Inter", size=12, weight="bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            width=140,
            height=40,
            command=self.perform_search
        )
        self.search_btn.grid(row=0, column=1)

        # Scroll results
        self.results_scroll = customtkinter.CTkScrollableFrame(self.search_card, fg_color="transparent")
        self.results_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 15))

        # Render Metrics and Placeholder Results
        self.refresh_metrics()
        self.render_empty_search_placeholder()

    def refresh_metrics(self):
        """Calculates system metrics and renders summary cards with Quick Actions."""
        # Clean current metrics widgets
        for widget in self.metrics_container.winfo_children():
            widget.destroy()

        docs = DatabaseManager.get_documents(self.user_id)
        chats = DatabaseManager.get_chats(self.user_id)
        settings = DatabaseManager.get_settings(self.user_id)
        total_questions = DatabaseManager.get_total_questions(self.user_id)

        # Totals
        total_docs = len(docs)
        total_chats = len(chats)
        total_size = sum(d["file_size"] for d in docs)
        
        provider = settings.get("llm_provider", "Ollama")
        model = settings.get("llm_model", "llama3")
        engine_str = f"{provider} ({model})"

        # Row 1: Metrics
        # Card 1: Library Stats
        card_1 = MetricCard(self.metrics_container, "Document Library", 
                            f"{total_docs} Files", f"Total storage: {format_size(total_size)}")
        card_1.grid(row=0, column=0, padx=8, sticky="ew")
        
        # Card 2: AI Engine
        card_2 = MetricCard(self.metrics_container, "Active AI Model", 
                            engine_str, f"Embeddings: {settings.get('embedding_model')}")
        card_2.grid(row=0, column=1, padx=8, sticky="ew")
        
        # Card 3: User Engagement
        card_3 = MetricCard(self.metrics_container, "Engagement Stats", 
                            f"{total_chats} Chats", f"{total_questions} Questions Asked")
        card_3.grid(row=0, column=2, padx=8, sticky="ew")

        # Row 2: Quick Actions panel
        actions_bar = customtkinter.CTkFrame(self, fg_color=("#F1F5F9", "#0B0B0B"), height=50, corner_radius=10, border_width=1, border_color=("#E2E8F0", "#1C1C1C"))
        actions_bar.grid(row=2, column=0, padx=30, pady=(10, 5), sticky="ew")
        
        lbl_act = customtkinter.CTkLabel(actions_bar, text="⚡ Quick Actions:", font=customtkinter.CTkFont(family="Inter", size=12, weight="bold"))
        lbl_act.pack(side="left", padx=15, pady=10)
        
        btn_upload = customtkinter.CTkButton(actions_bar, text="📁 Upload Document", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), width=120, height=30, fg_color="#10B981", hover_color="#059669", command=lambda: self.switch_tab("Documents"))
        btn_upload.pack(side="left", padx=5)

        btn_chat = customtkinter.CTkButton(actions_bar, text="💬 Open Chat", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), width=100, height=30, fg_color="#4F46E5", hover_color="#4338CA", command=lambda: self.switch_tab("AI Chat"))
        btn_chat.pack(side="left", padx=5)

        btn_search = customtkinter.CTkButton(actions_bar, text="🔍 Search Box", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), width=100, height=30, fg_color="transparent", text_color=("#111827", "#E5E7EB"), border_color="#E2E8F0", border_width=1.5, hover_color=("gray90", "gray15"), command=self.search_input.focus)
        btn_search.pack(side="left", padx=5)

        btn_settings = customtkinter.CTkButton(actions_bar, text="⚙️ Settings", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), width=100, height=30, fg_color="transparent", text_color=("#111827", "#E5E7EB"), border_color="#E2E8F0", border_width=1.5, hover_color=("gray90", "gray15"), command=lambda: self.switch_tab("Settings"))
        btn_settings.pack(side="left", padx=5)


    def render_empty_search_placeholder(self):
        """Draws static instructional text if search results are empty."""
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        placeholder = customtkinter.CTkLabel(
            self.results_scroll,
            text="Type a search query above to look up relevant files, chats, or document excerpts.",
            font=customtkinter.CTkFont(family="Inter", size=13),
            text_color="gray"
        )
        placeholder.pack(pady=50)

    def perform_search(self):
        """Starts a thread to query FAISS across all documents."""
        query = self.search_input.get().strip()
        if not query:
            self.render_empty_search_placeholder()
            return

        self.search_btn.configure(state="disabled", text="Searching...")
        self.update()

        threading.Thread(
            target=self.search_thread,
            args=(query,),
            daemon=True
        ).start()

    def search_thread(self, query: str):
        """Worker thread to aggregate vector stores and run global search (files, chats, semantics)."""
        docs = DatabaseManager.get_documents(self.user_id)
        
        # 1. Run local keyword DB queries
        file_matches = DatabaseManager.search_documents_by_name(self.user_id, query)
        chat_matches = DatabaseManager.search_chat_messages(self.user_id, query)
        
        # 2. Run semantic vector search if vector stores are loaded
        results = []
        error_msg = None
        if docs:
            settings = DatabaseManager.get_settings(self.user_id)
            embed_name = settings.get("embedding_model", "all-MiniLM-L6-v2")
            api_key = settings.get("api_key", "")
            try:
                embed_model = EmbeddingManager.get_embeddings(embed_name, api_key)
                doc_ids = [d["id"] for d in docs]
                vector_store = VectorStoreManager.load_merged_vector_store(
                    user_id=self.user_id,
                    doc_ids=doc_ids,
                    embedding_model=embed_model
                )
                if vector_store:
                    results = vector_store.similarity_search(query, k=5)
            except Exception as e:
                error_msg = str(e)
        
        self.after(0, lambda: self.on_search_complete(results, file_matches, chat_matches, error_msg))

    def on_search_complete(self, results, file_matches, chat_matches, error_msg=None):
        """Renders search result matches in scroll frame."""
        self.search_btn.configure(state="normal", text="Search")
        
        # Clear results
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        if error_msg:
            lbl = customtkinter.CTkLabel(self.results_scroll, text=f"Error executing search: {error_msg}", text_color="red")
            lbl.pack(pady=40)
            return

        has_any_results = bool(file_matches or chat_matches or results)
        if not has_any_results:
            lbl = customtkinter.CTkLabel(self.results_scroll, text="No matches found in your files, chats, or database.", font=customtkinter.CTkFont(family="Inter", size=13), text_color="gray")
            lbl.pack(pady=50)
            return

        # Section 1: File Matches
        if file_matches:
            sec_header = customtkinter.CTkLabel(self.results_scroll, text="📄 Document Filename Matches", font=customtkinter.CTkFont(family="Outfit", size=13, weight="bold"), text_color="#4F46E5", anchor="w")
            sec_header.pack(fill="x", pady=(10, 5))
            
            for doc in file_matches:
                card = customtkinter.CTkFrame(self.results_scroll, corner_radius=8, fg_color=("#F8FAFC", "#000000"), border_width=1, border_color=("#E2E8F0", "#1C1C1C"))
                card.pack(fill="x", pady=4, ipady=3)
                
                lbl = customtkinter.CTkLabel(card, text=f"{doc['filename']} ({doc['file_type']}) - Size: {format_size(doc['file_size'])}", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), text_color=("#0F172A", "#F8FAFC"), anchor="w", cursor="hand2")
                lbl.pack(fill="x", padx=15, pady=6)
                lbl.bind("<Button-1>", lambda e, d=doc: self.open_document(d))

        # Section 2: Conversation Log Matches
        if chat_matches:
            sec_header = customtkinter.CTkLabel(self.results_scroll, text="💬 Conversation History Matches", font=customtkinter.CTkFont(family="Outfit", size=13, weight="bold"), text_color="#4F46E5", anchor="w")
            sec_header.pack(fill="x", pady=(15, 5))
            
            for msg in chat_matches:
                card = customtkinter.CTkFrame(self.results_scroll, corner_radius=8, fg_color=("#F8FAFC", "#000000"), border_width=1, border_color=("#E2E8F0", "#1C1C1C"))
                card.pack(fill="x", pady=4, ipady=3)
                
                sender_name = "👤 You" if msg["sender"] == "user" else "🧠 DocMind AI"
                lbl_title = customtkinter.CTkLabel(card, text=f"Chat: '{msg['chat_title']}' ({sender_name})", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), text_color="#4F46E5", anchor="w", cursor="hand2")
                lbl_title.pack(fill="x", padx=15, pady=(5, 1))
                lbl_title.bind("<Button-1>", lambda e, cid=msg["chat_id"]: self.open_chat_view(cid))

                content_snippet = msg["content"].replace("\n", " ")
                if len(content_snippet) > 120:
                    content_snippet = content_snippet[:117] + "..."
                lbl_content = customtkinter.CTkLabel(card, text=f"\"{content_snippet}\"", font=customtkinter.CTkFont(family="Inter", size=10, slant="italic"), text_color="gray", anchor="w", justify="left")
                lbl_content.pack(fill="x", padx=15, pady=(1, 5))

        # Section 3: Semantic Matches
        if results:
            sec_header = customtkinter.CTkLabel(self.results_scroll, text="🔍 Semantic Content Matches", font=customtkinter.CTkFont(family="Outfit", size=13, weight="bold"), text_color="#4F46E5", anchor="w")
            sec_header.pack(fill="x", pady=(15, 5))
            
            for match in results:
                doc_name = match.metadata.get("source", "Unknown Document")
                page_num = match.metadata.get("page", 1)
                content = match.page_content.strip()

                result_card = customtkinter.CTkFrame(self.results_scroll, corner_radius=8, fg_color=("#F8FAFC", "#000000"), border_width=1, border_color=("#E2E8F0", "#1C1C1C"))
                result_card.pack(fill="x", pady=4, ipady=3)
                
                result_header = customtkinter.CTkFrame(result_card, fg_color="transparent")
                result_header.pack(fill="x", padx=15, pady=(6, 1))

                head_lbl = customtkinter.CTkLabel(
                    result_header,
                    text=f"{doc_name} (Page {page_num})",
                    font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"),
                    text_color="#4F46E5",
                    anchor="w"
                )
                head_lbl.pack(side="left")

                copy_btn = customtkinter.CTkButton(
                    result_header,
                    text="📋 Copy",
                    width=45,
                    height=18,
                    font=customtkinter.CTkFont(family="Inter", size=9),
                    fg_color="transparent",
                    text_color="#4F46E5",
                    hover_color=("gray90", "gray20"),
                    corner_radius=4
                )
                copy_btn.configure(command=lambda c=content, b=copy_btn: self.copy_to_clipboard(c, b))
                copy_btn.pack(side="right")

                content_lbl = customtkinter.CTkLabel(
                    result_card,
                    text=f"\"{content}\"",
                    font=customtkinter.CTkFont(family="Inter", size=10, slant="italic"),
                    justify="left",
                    anchor="w",
                    wraplength=700
                )
                content_lbl.pack(fill="x", padx=15, pady=(1, 6))

    def open_document(self, doc: dict):
        """Opens the selected document file locally using the default OS application."""
        open_document(doc["file_path"])

    def open_chat_view(self, chat_id: int):
        """Navigates to the active chat session using the dashboard parent navigation trigger."""
        parent_app = self.master.master
        if hasattr(parent_app, "load_chat_from_history"):
            parent_app.load_chat_from_history(chat_id)

    def copy_to_clipboard(self, text: str, btn: customtkinter.CTkButton):
        """Copies text content to clipboard and updates button text as feedback."""
        copy_to_clipboard(self, text, btn)
