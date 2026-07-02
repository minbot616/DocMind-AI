import customtkinter
from database import DatabaseManager
from llm_manager import LLMManager
from tkinter import messagebox
from typing import Dict, Any, Callable

class SettingsFrame(customtkinter.CTkFrame):
    """Allows users to customize their AI settings, API keys, appearance, and clear history."""

    def __init__(self, parent: customtkinter.CTk, user_id: int, on_theme_change: Callable[[str], None]):
        super().__init__(parent, fg_color="transparent")
        self.user_id = user_id
        self.on_theme_change = on_theme_change
        self.settings = DatabaseManager.get_settings(user_id)

        # Main Layout Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Form Scrollable Frame

        # 1. Header
        header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=30, pady=(20, 10), sticky="ew")
        
        header_label = customtkinter.CTkLabel(
            header_frame,
            text="Settings & Preferences",
            font=customtkinter.CTkFont(family="Outfit", size=24, weight="bold")
        )
        header_label.pack(side="left")

        # 2. Form (Scrollable for scalability)
        self.form_frame = customtkinter.CTkScrollableFrame(self, fg_color="transparent")
        self.form_frame.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="nsew")
        self.form_frame.grid_columnconfigure(0, weight=1)

        # --- Section: Appearance ---
        self.create_section_header("Appearance")
        
        # Theme Choice
        self.theme_var = customtkinter.StringVar(value=self.settings.get("theme", "Dark"))
        theme_frame = self.create_form_row("App Theme", "Select the visual theme for the application.")
        self.theme_menu = customtkinter.CTkOptionMenu(
            theme_frame,
            values=["Dark", "Light", "System"],
            variable=self.theme_var,
            width=180,
            command=self.change_theme
        )
        self.theme_menu.pack(side="right")

        # --- Section: Embeddings Model ---
        self.create_section_header("Embeddings Settings")
        
        self.embed_var = customtkinter.StringVar(value=self.settings.get("embedding_model", "all-MiniLM-L6-v2"))
        embed_frame = self.create_form_row("Embedding Model", "Used to index document text. Requires re-uploading documents if changed.")
        self.embed_menu = customtkinter.CTkOptionMenu(
            embed_frame,
            values=["all-MiniLM-L6-v2", "all-mpnet-base-v2", "openai"],
            variable=self.embed_var,
            width=180
        )
        self.embed_menu.pack(side="right")

        # Chunk Size
        self.chunk_size_var = customtkinter.StringVar(value=str(self.settings.get("chunk_size", 500)))
        chunk_size_frame = self.create_form_row("Chunk Size (characters)", "Size of parsed document text chunks.")
        self.chunk_size_menu = customtkinter.CTkOptionMenu(
            chunk_size_frame,
            values=["300", "500", "800", "1000", "1500"],
            variable=self.chunk_size_var,
            width=180
        )
        self.chunk_size_menu.pack(side="right")

        # Chunk Overlap
        self.chunk_overlap_var = customtkinter.StringVar(value=str(self.settings.get("chunk_overlap", 50)))
        chunk_overlap_frame = self.create_form_row("Chunk Overlap (characters)", "Overlap between consecutive chunks to maintain context.")
        self.chunk_overlap_menu = customtkinter.CTkOptionMenu(
            chunk_overlap_frame,
            values=["30", "50", "100", "150", "200"],
            variable=self.chunk_overlap_var,
            width=180
        )
        self.chunk_overlap_menu.pack(side="right")

        # --- Section: AI Provider ---
        self.create_section_header("AI LLM Settings")

        # LLM Provider Choice
        self.provider_var = customtkinter.StringVar(value=self.settings.get("llm_provider", "Ollama"))
        provider_frame = self.create_form_row("LLM Provider", "Choose between local Ollama or cloud LLMs.")
        self.provider_menu = customtkinter.CTkOptionMenu(
            provider_frame,
            values=["Ollama", "Groq", "OpenAI"],
            variable=self.provider_var,
            width=180,
            command=self.update_models_list
        )
        self.provider_menu.pack(side="right")

        # LLM Model Choice
        self.model_var = customtkinter.StringVar(value=self.settings.get("llm_model", "llama3"))
        model_frame = self.create_form_row("Active Model", "Select the specific model to process RAG queries.")
        self.model_menu = customtkinter.CTkOptionMenu(
            model_frame,
            values=[],
            variable=self.model_var,
            width=180
        )
        self.model_menu.pack(side="right")

        # API Key Input
        self.key_var = customtkinter.StringVar(value=self.settings.get("api_key", ""))
        key_frame = self.create_form_row("API Key / Host Connection", "Required for OpenAI/Groq. Leave blank for Ollama.")
        self.key_entry = customtkinter.CTkEntry(
            key_frame,
            textvariable=self.key_var,
            width=280,
            placeholder_text="Enter API key or Ollama custom host URL",
            show="*",
            fg_color=("#F8FAFC", "#000000"),
            border_color=("#E2E8F0", "#1C1C1C"),
            text_color=("#0F172A", "#F8FAFC"),
            placeholder_text_color="gray"
        )
        self.key_entry.pack(side="right")

        # Temperature
        self.temp_var = customtkinter.StringVar(value=str(self.settings.get("temperature", 0.2)))
        temp_frame = self.create_form_row("Temperature", "Controls creativity. Lower is more precise and factual.")
        self.temp_menu = customtkinter.CTkOptionMenu(
            temp_frame,
            values=["0.0", "0.2", "0.5", "0.7", "1.0"],
            variable=self.temp_var,
            width=180
        )
        self.temp_menu.pack(side="right")

        # Max Tokens
        self.max_tokens_var = customtkinter.StringVar(value=str(self.settings.get("max_tokens", 1024)))
        max_tokens_frame = self.create_form_row("Maximum Tokens", "Upper limit on the length of generated answers.")
        self.max_tokens_menu = customtkinter.CTkOptionMenu(
            max_tokens_frame,
            values=["256", "512", "1024", "2048", "4096"],
            variable=self.max_tokens_var,
            width=180
        )
        self.max_tokens_menu.pack(side="right")

        # --- Section: Data Management ---
        self.create_section_header("Danger Zone")
        
        danger_frame = self.create_form_row("Clear Conversation History", "Permenently erase all saved chat messages and records.")
        self.clear_btn = customtkinter.CTkButton(
            danger_frame,
            text="Erase Chat History",
            fg_color="#EF4444",      # Red-500
            hover_color="#DC2626",  # Red-600
            width=150,
            command=self.clear_chat_history
        )
        self.clear_btn.pack(side="right")

        # Save Button at Bottom
        save_btn_frame = customtkinter.CTkFrame(self.form_frame, fg_color="transparent")
        save_btn_frame.pack(fill="x", pady=(30, 20))
        
        self.save_btn = customtkinter.CTkButton(
            save_btn_frame,
            text="Save Preferences",
            fg_color="#4F46E5",
            hover_color="#4338CA",
            font=customtkinter.CTkFont(family="Inter", size=14, weight="bold"),
            width=200,
            height=40,
            command=self.save_settings
        )
        self.save_btn.pack(side="left")

        self.test_btn = customtkinter.CTkButton(
            save_btn_frame,
            text="Test LLM Connection",
            fg_color="transparent",
            border_color="#4F46E5",
            border_width=1.5,
            text_color=("#111827", "#E5E7EB"),
            hover_color=("gray90", "gray15"),
            width=180,
            height=40,
            command=self.test_llm_connection
        )
        self.test_btn.pack(side="left", padx=15)

        # Initial loading triggers
        self.update_models_list(self.provider_var.get())

    def create_section_header(self, title: str):
        """Creates a stylized header line for form categories."""
        header_frame = customtkinter.CTkFrame(self.form_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10))
        
        lbl = customtkinter.CTkLabel(
            header_frame,
            text=title,
            font=customtkinter.CTkFont(family="Outfit", size=16, weight="bold"),
            text_color="#4F46E5"
        )
        lbl.pack(side="left")
        
        divider = customtkinter.CTkFrame(header_frame, height=2, fg_color=("gray85", "gray25"))
        divider.pack(side="left", fill="x", expand=True, padx=(10, 0), pady=10)

    def create_form_row(self, label_text: str, desc_text: str) -> customtkinter.CTkFrame:
        """Helper to create a row in settings form containing labels and descriptions."""
        row_frame = customtkinter.CTkFrame(self.form_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=10)
        
        text_container = customtkinter.CTkFrame(row_frame, fg_color="transparent")
        text_container.pack(side="left", fill="both", expand=True)
        
        lbl = customtkinter.CTkLabel(
            text_container,
            text=label_text,
            font=customtkinter.CTkFont(family="Inter", size=14, weight="bold"),
            anchor="w"
        )
        lbl.pack(fill="x")
        
        desc = customtkinter.CTkLabel(
            text_container,
            text=desc_text,
            font=customtkinter.CTkFont(family="Inter", size=11),
            text_color="gray",
            anchor="w"
        )
        desc.pack(fill="x")
        
        return row_frame

    def update_models_list(self, provider: str):
        """Fetches and inserts the models according to selected provider.
        If it's Ollama, fetches dynamically in the background to avoid blocking the main UI thread.
        """
        import threading
        
        # 1. Get predefined models first (works instantly)
        models = LLMManager.PROVIDER_MODELS.get(provider, [])
        self.model_menu.configure(values=models)
        
        current_model = self.settings.get("llm_model")
        if current_model in models:
            self.model_var.set(current_model)
        else:
            self.model_var.set(models[0] if models else "")

        # 2. If Ollama is selected, spin a thread to query active local models and update UI on completion
        if provider == "Ollama":
            def fetch_ollama():
                try:
                    dynamic_models = LLMManager.get_available_models("Ollama")
                    if dynamic_models:
                        self.after(0, lambda: self._apply_dynamic_models(dynamic_models))
                except Exception:
                    pass
            
            threading.Thread(target=fetch_ollama, daemon=True).start()

    def _apply_dynamic_models(self, models: list):
        """Callback to update models dropdown in the main GUI thread once fetched."""
        try:
            self.model_menu.configure(values=models)
            current_model = self.settings.get("llm_model")
            if current_model in models:
                self.model_var.set(current_model)
            else:
                self.model_var.set(models[0] if models else "")
        except Exception:
            pass

    def change_theme(self, theme: str):
        """Immediately sets application theme."""
        self.on_theme_change(theme)

    def save_settings(self):
        """Persists choices into database."""
        try:
            chunk_size = int(self.chunk_size_var.get())
            chunk_overlap = int(self.chunk_overlap_var.get())
            temperature = float(self.temp_var.get())
            max_tokens = int(self.max_tokens_var.get())
        except ValueError:
            messagebox.showerror("Error", "Chunk size, overlap, temperature, and max tokens must be valid numbers.")
            return

        provider = self.provider_var.get()
        api_key = self.key_var.get().strip()
        embed_model = self.embed_var.get()

        if provider in ["Groq", "OpenAI"] and not api_key:
            messagebox.showerror("Validation Error", f"API Key is required for provider {provider}.")
            return

        if embed_model == "openai" and not api_key:
            messagebox.showerror("Validation Error", "API Key is required to use OpenAI embeddings.")
            return

        updated_settings = {
            "theme": self.theme_var.get(),
            "embedding_model": embed_model,
            "llm_provider": provider,
            "llm_model": self.model_var.get(),
            "api_key": api_key,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        success = DatabaseManager.update_settings(self.user_id, updated_settings)
        if success:
            self.settings = updated_settings
            messagebox.showinfo("Success", "Preferences saved successfully.")
        else:
            messagebox.showerror("Error", "Failed to update preferences database.")

    def test_llm_connection(self):
        """Runs background task to check connection to LLM to prevent GUI freeze."""
        provider = self.provider_var.get()
        model = self.model_var.get()
        key = self.key_var.get().strip()

        if provider in ["Groq", "OpenAI"] and not key:
            messagebox.showerror("Validation Error", f"API Key is required to test the connection for {provider}.")
            return

        self.test_btn.configure(state="disabled", text="Testing...")
        self.update()

        import threading
        def run_test():
            from utils import logger
            logger.info(f"Testing LLM connection in background for provider: '{provider}', model: '{model}'...")
            try:
                success = LLMManager.test_connection(provider, model, key)
            except Exception:
                logger.exception("LLM connection test failed.")
                success = False
            self.after(0, lambda: self.on_test_complete(success, provider, model))

        threading.Thread(target=run_test, daemon=True).start()

    def on_test_complete(self, success: bool, provider: str, model: str):
        self.test_btn.configure(state="normal", text="Test LLM Connection")
        if success:
            messagebox.showinfo("Connection Successful", f"Successfully reached {provider} ({model}) LLM!")
        else:
            messagebox.showerror("Connection Failed", f"Could not connect to {provider} using model {model}.\nEnsure the model is loaded/running, and your API keys/connection settings are correct.")

    def clear_chat_history(self):
        """Asks confirmation to purge histories."""
        confirm = messagebox.askyesno(
            "Clear History",
            "Are you absolutely sure you want to delete all chat history?\nThis cannot be undone.",
            icon='warning'
        )
        if confirm:
            success = DatabaseManager.clear_all_history(self.user_id)
            if success:
                messagebox.showinfo("Success", "All conversation history cleared.")
            else:
                messagebox.showerror("Error", "Could not delete conversation histories.")
