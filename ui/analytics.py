import os
import re
import json
from collections import Counter
import customtkinter
from database import DatabaseManager
from utils import format_size, logger
from ui.components import MetricCard

class AnalyticsFrame(customtkinter.CTkFrame):
    """Visualizes system usage, top questions, cited documents, and provider stats."""

    def __init__(self, parent: customtkinter.CTk, user_id: int):
        super().__init__(parent, fg_color="transparent")
        self.user_id = user_id

        # Grid config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # Cards Row
        self.grid_rowconfigure(2, weight=1)  # Lists Detail Area

        # 1. Header
        header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=30, pady=(20, 15), sticky="ew")
        
        header_label = customtkinter.CTkLabel(
            header_frame,
            text="Usage & System Analytics",
            font=customtkinter.CTkFont(family="Outfit", size=24, weight="bold")
        )
        header_label.pack(side="left")

        # 2. Metrics Cards Row container
        self.metrics_container = customtkinter.CTkFrame(self, fg_color="transparent")
        self.metrics_container.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        self.metrics_container.grid_columnconfigure((0, 1, 2), weight=1)

        # 3. Lists detail grid container
        self.details_container = customtkinter.CTkFrame(self, fg_color="transparent")
        self.details_container.grid(row=2, column=0, padx=30, pady=15, sticky="nsew")
        self.details_container.grid_columnconfigure((0, 1), weight=1)
        self.details_container.grid_rowconfigure(0, weight=1)

        self.refresh_analytics()

    def refresh_analytics(self):
        """Re-fetches database information and renders analytics charts."""
        # Clean current views
        for widget in self.metrics_container.winfo_children():
            widget.destroy()
        for widget in self.details_container.winfo_children():
            widget.destroy()

        # Database aggregation queries
        docs = DatabaseManager.get_documents(self.user_id)
        chats = DatabaseManager.get_chats(self.user_id)
        settings = DatabaseManager.get_settings(self.user_id)

        total_docs = len(docs)
        total_chunks = sum(d.get("chunks", 0) for d in docs)
        total_size = sum(d["file_size"] for d in docs)
        # Aggregate real average response time from database
        avg_response_time = "N/A"
        try:
            with DatabaseManager.get_db_connection(DatabaseManager.HISTORY_DB) as conn:
                cursor = conn.execute(
                    """
                    SELECT AVG(response_time) FROM messages 
                    WHERE response_time IS NOT NULL 
                      AND chat_id IN (SELECT id FROM chats WHERE user_id = ?)
                    """,
                    (self.user_id,)
                )
                row = cursor.fetchone()
                if row and row[0] is not None:
                    avg_response_time = f"{row[0]:.2f}s"
        except Exception:
            logger.exception("Failed to calculate average response latency from database.")

        # Provider configurations
        provider = settings.get("llm_provider", "Ollama")
        model = settings.get("llm_model", "llama3")
        embed_name = settings.get("embedding_model", "all-MiniLM-L6-v2")

        # Create Metric Cards
        card_1 = MetricCard(self.metrics_container, "Parsed Vector Chunks", f"{total_chunks} Chunks", f"From {total_docs} files ({format_size(total_size)})")
        card_1.grid(row=0, column=0, padx=8, sticky="ew")
        
        card_2 = MetricCard(self.metrics_container, "RAG Response Latency", avg_response_time, f"Model engine: {provider}")
        card_2.grid(row=0, column=1, padx=8, sticky="ew")
        
        card_3 = MetricCard(self.metrics_container, "Active Embedding Model", embed_name, "Used for similarity search indexing")
        card_3.grid(row=0, column=2, padx=8, sticky="ew")

        # Columns
        # Column Left: Topics
        left_card = customtkinter.CTkFrame(self.details_container, corner_radius=12, fg_color=("#FFFFFF", "#0B0B0B"), border_width=1, border_color=("#E2E8F0", "#1C1C1C"))
        left_card.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")
        left_card.grid_columnconfigure(0, weight=1)
        
        lbl_left_title = customtkinter.CTkLabel(left_card, text="🔥 Most Asked Topics", font=customtkinter.CTkFont(family="Outfit", size=14, weight="bold"), text_color="#4F46E5", anchor="w")
        lbl_left_title.pack(fill="x", padx=15, pady=(15, 10))

        # Word frequency calculator
        topics = self.calculate_top_topics()
        if not topics:
            lbl_empty = customtkinter.CTkLabel(left_card, text="No topics recorded. Start chatting to log queries!", font=customtkinter.CTkFont(family="Inter", size=11), text_color="gray")
            lbl_empty.pack(pady=40)
        else:
            for idx, (word, freq) in enumerate(topics):
                row = customtkinter.CTkFrame(left_card, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=4)
                lbl_rank = customtkinter.CTkLabel(row, text=f"#{idx+1}", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), width=30, anchor="w", text_color="gray")
                lbl_rank.pack(side="left")
                lbl_word = customtkinter.CTkLabel(row, text=word, font=customtkinter.CTkFont(family="Inter", size=12), anchor="w")
                lbl_word.pack(side="left", fill="x", expand=True)
                lbl_freq = customtkinter.CTkLabel(row, text=f"{freq} times", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), text_color="#10B981")
                lbl_freq.pack(side="right")

        # Column Right: Used documents
        right_card = customtkinter.CTkFrame(self.details_container, corner_radius=12, fg_color=("#FFFFFF", "#0B0B0B"), border_width=1, border_color=("#E2E8F0", "#1C1C1C"))
        right_card.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")
        right_card.grid_columnconfigure(0, weight=1)

        lbl_right_title = customtkinter.CTkLabel(right_card, text="📄 Most Cited Documents", font=customtkinter.CTkFont(family="Outfit", size=14, weight="bold"), text_color="#4F46E5", anchor="w")
        lbl_right_title.pack(fill="x", padx=15, pady=(15, 10))

        cited = self.calculate_top_cited()
        if not cited:
            lbl_empty = customtkinter.CTkLabel(right_card, text="No citations logged. Documents are cited during conversation answers.", font=customtkinter.CTkFont(family="Inter", size=11), text_color="gray")
            lbl_empty.pack(pady=40)
        else:
            for idx, (doc_name, count) in enumerate(cited):
                row = customtkinter.CTkFrame(right_card, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=4)
                lbl_rank = customtkinter.CTkLabel(row, text=f"#{idx+1}", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), width=30, anchor="w", text_color="gray")
                lbl_rank.pack(side="left")
                
                # Truncate filename
                disp_name = doc_name[:32] + "..." if len(doc_name) > 35 else doc_name
                lbl_doc = customtkinter.CTkLabel(row, text=disp_name, font=customtkinter.CTkFont(family="Inter", size=12), anchor="w")
                lbl_doc.pack(side="left", fill="x", expand=True)
                lbl_count = customtkinter.CTkLabel(row, text=f"{count} citations", font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"), text_color="#F59E0B")
                lbl_count.pack(side="right")


    def calculate_top_topics(self):
        """Calculates frequent keywords from user prompts."""
        try:
            with DatabaseManager.get_db_connection(DatabaseManager.HISTORY_DB) as conn:
                cursor = conn.execute(
                    "SELECT content FROM messages WHERE sender = 'user' AND chat_id IN (SELECT id FROM chats WHERE user_id = ?)",
                    (self.user_id,)
                )
                user_texts = [row['content'] for row in cursor.fetchall()]
        except Exception:
            return []

        stopwords = {
            "the", "a", "an", "is", "of", "and", "in", "to", "for", "with", "on", "at", "by", "from", 
            "about", "what", "how", "why", "who", "which", "whose", "this", "that", "these", "those", 
            "it", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", 
            "can", "could", "will", "would", "shall", "should", "may", "might", "must", "me", "my", "your", 
            "his", "her", "its", "our", "their", "us", "them", "i", "you", "he", "she", "we", "they", "please",
            "give", "tell", "explain", "summarize", "find", "get", "show"
        }
        
        words = []
        for text in user_texts:
            text_cleaned = re.sub(r'[^\w\s]', '', text.lower())
            for w in text_cleaned.split():
                if len(w) > 2 and w not in stopwords:
                    words.append(w)
                    
        return Counter(words).most_common(5)

    def calculate_top_cited(self):
        """Calculates citation frequencies from assistant responses."""
        try:
            with DatabaseManager.get_db_connection(DatabaseManager.HISTORY_DB) as conn:
                cursor = conn.execute(
                    "SELECT sources FROM messages WHERE sender = 'assistant' AND chat_id IN (SELECT id FROM chats WHERE user_id = ?)",
                    (self.user_id,)
                )
                source_jsons = [row['sources'] for row in cursor.fetchall() if row['sources']]
        except Exception:
            return []

        cited_docs = []
        for s_json in source_jsons:
            try:
                sources = json.loads(s_json)
                for src in sources:
                    doc_name = src.get("document")
                    if doc_name:
                        cited_docs.append(doc_name)
            except Exception:
                pass
                
        return Counter(cited_docs).most_common(5)
