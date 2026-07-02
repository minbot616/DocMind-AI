import customtkinter
from database import DatabaseManager
from datetime import datetime
from tkinter import simpledialog, messagebox
from typing import Callable

class HistoryFrame(customtkinter.CTkFrame):
    """The historical conversation archive. Allows users to browse, reload, rename,
    and delete past chat logs.
    """

    def __init__(self, parent: customtkinter.CTk, user_id: int, on_chat_selected: Callable[[int], None]):
        super().__init__(parent, fg_color="transparent")
        self.user_id = user_id
        self.on_chat_selected = on_chat_selected

        # Grid config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # Search bar
        self.grid_rowconfigure(2, weight=1)  # Scrollable List

        # 1. Header
        header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=30, pady=(20, 15), sticky="ew")
        
        header_label = customtkinter.CTkLabel(
            header_frame,
            text="Conversation Archive",
            font=customtkinter.CTkFont(family="Outfit", size=24, weight="bold")
        )
        header_label.pack(side="left")

        # Clear Archive Button
        self.clear_archive_btn = customtkinter.CTkButton(
            header_frame,
            text="Clear Archive",
            font=customtkinter.CTkFont(family="Inter", size=12, weight="bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            width=110,
            height=30,
            command=self.clear_all_chats
        )
        self.clear_archive_btn.pack(side="right")

        # Search Bar
        self.search_var = customtkinter.StringVar()
        self.search_var.trace_add("write", lambda *args: self.load_history_list())
        
        self.search_entry = customtkinter.CTkEntry(
            self,
            placeholder_text="Search conversation titles...",
            textvariable=self.search_var,
            height=35,
            corner_radius=8,
            font=customtkinter.CTkFont(family="Inter", size=12),
            fg_color=("#FFFFFF", "#000000"),
            border_color=("#E2E8F0", "#1C1C1C")
        )
        self.search_entry.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="ew")

        # 2. Scrollable List of Chats
        self.list_scroll = customtkinter.CTkScrollableFrame(self, fg_color="transparent")
        self.list_scroll.grid(row=2, column=0, padx=30, pady=(0, 20), sticky="nsew")

        self.load_history_list()

    def load_history_list(self):
        """Fetches chats and draws interactive items in the list scroll."""
        # Clear existing list items
        for widget in self.list_scroll.winfo_children():
            widget.destroy()

        chats = DatabaseManager.get_chats(self.user_id)
        
        search_query = self.search_var.get().strip().lower()
        if search_query:
            chats = [c for c in chats if search_query in c["title"].lower()]

        if not chats:
            empty_lbl = customtkinter.CTkLabel(
                self.list_scroll,
                text="No matching conversations found." if search_query else "No saved conversations found.\nStart chatting in the AI Chat tab to create logs!",
                font=customtkinter.CTkFont(family="Inter", size=13),
                text_color="gray"
            )
            empty_lbl.pack(pady=60)
            return

        for chat in chats:
            self.create_history_row(chat)

    def create_history_row(self, chat: dict):
        """Creates a styled row card representing a single conversation."""
        row_card = customtkinter.CTkFrame(self.list_scroll, height=55, corner_radius=8, fg_color=("#FFFFFF", "#0B0B0B"), border_width=1, border_color=("#E2E8F0", "#1C1C1C"))
        row_card.pack(fill="x", pady=4, ipady=3)
        row_card.pack_propagate(False)

        # Chat Title
        title_text = chat["title"]
        if len(title_text) > 45:
            title_text = title_text[:42] + "..."

        # Left Info Stack
        info_frame = customtkinter.CTkFrame(row_card, fg_color="transparent")
        info_frame.pack(side="left", padx=15, fill="both", expand=True)

        lbl_title = customtkinter.CTkLabel(
            info_frame,
            text=title_text,
            font=customtkinter.CTkFont(family="Inter", size=12, weight="bold"),
            anchor="w"
        )
        lbl_title.pack(fill="x", pady=(8, 0))

        # Format time
        try:
            dt = datetime.strptime(chat["created_at"], "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%b %d, %Y - %H:%M")
        except Exception:
            time_str = chat["created_at"]

        lbl_date = customtkinter.CTkLabel(
            info_frame,
            text=f"Created on: {time_str}",
            font=customtkinter.CTkFont(family="Inter", size=10),
            text_color="gray",
            anchor="w"
        )
        lbl_date.pack(fill="x")

        # Right Controls
        ctrl_frame = customtkinter.CTkFrame(row_card, fg_color="transparent")
        ctrl_frame.pack(side="right", padx=15)

        # 1. Load Button
        load_btn = customtkinter.CTkButton(
            ctrl_frame,
            text="Reload Chat",
            font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            width=90,
            height=28,
            command=lambda cid=chat["id"]: self.on_chat_selected(cid)
        )
        load_btn.pack(side="left", padx=3)

        # 2. Rename Button
        rename_btn = customtkinter.CTkButton(
            ctrl_frame,
            text="Rename",
            font=customtkinter.CTkFont(family="Inter", size=11),
            fg_color="transparent",
            text_color=("#1F2937", "#E5E7EB"),
            hover_color=("gray90", "gray25"),
            width=65,
            height=28,
            command=lambda chat_dict=chat: self.rename_chat(chat_dict)
        )
        rename_btn.pack(side="left", padx=3)

        # 3. Delete Button
        delete_btn = customtkinter.CTkButton(
            ctrl_frame,
            text="Delete",
            font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"),
            fg_color="transparent",
            text_color="#EF4444",
            hover_color=("gray90", "gray25"),
            width=50,
            height=28,
            command=lambda cid=chat["id"]: self.delete_chat(cid)
        )
        delete_btn.pack(side="left", padx=3)

        # 4. Export Button
        export_btn = customtkinter.CTkButton(
            ctrl_frame,
            text="Export",
            font=customtkinter.CTkFont(family="Inter", size=11),
            fg_color="transparent",
            text_color=("#1F2937", "#E5E7EB"),
            hover_color=("gray90", "gray25"),
            width=50,
            height=28,
            command=lambda cid=chat["id"]: self.export_chat(cid)
        )
        export_btn.pack(side="left", padx=3)

    def rename_chat(self, chat: dict):
        """Asks user for a new chat session title."""
        current_title = chat["title"]
        new_title = simpledialog.askstring("Rename Chat", "Enter new conversation title:", initialvalue=current_title)
        
        if new_title and new_title.strip() != current_title:
            success = DatabaseManager.rename_chat(chat["id"], new_title.strip())
            if success:
                self.load_history_list()
                messagebox.showinfo("Success", "Conversation renamed successfully.")
            else:
                messagebox.showerror("Error", "Could not rename conversation.")

    def delete_chat(self, chat_id: int):
        """Deletes chat session and references from DB."""
        confirm = messagebox.askyesno(
            "Delete Chat",
            "Are you sure you want to permanently delete this conversation and all its messages?",
            icon="warning"
        )
        if confirm:
            success = DatabaseManager.delete_chat(chat_id)
            if success:
                self.load_history_list()
                messagebox.showinfo("Success", "Conversation deleted successfully.")
            else:
                messagebox.showerror("Error", "Could not delete conversation.")

    def export_chat(self, chat_id: int):
        """Prompts the user to export the conversation transcript as a PDF or TXT."""
        from chat_manager import ChatManager
        from tkinter import filedialog
        
        # Show prompt option
        export_format = messagebox.askyesnocancel(
            "Export Conversation",
            "Would you like to export as PDF? (Click 'No' to export as plain TXT, 'Cancel' to abort)"
        )
        if export_format is None:
            return  # Cancelled
            
        if export_format:
            # Export as PDF
            save_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Document", "*.pdf")],
                title="Export PDF Transcript"
            )
            if save_path:
                success = ChatManager.export_chat_to_pdf(chat_id, save_path)
                if success:
                    messagebox.showinfo("Export Successful", f"PDF saved successfully to:\n{save_path}")
                else:
                    messagebox.showerror("Export Failed", "Could not compile PDF transcript.")
        else:
            # Export as TXT
            save_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Document", "*.txt")],
                title="Export Plain Text Transcript"
            )
            if save_path:
                success = ChatManager.export_chat_to_txt(chat_id, save_path)
                if success:
                    messagebox.showinfo("Export Successful", f"Plain text saved successfully to:\n{save_path}")
                else:
                    messagebox.showerror("Export Failed", "Could not write plain text transcript.")

    def clear_all_chats(self):
        """Purges all conversations for this user from SQLite."""
        confirm = messagebox.askyesno(
            "Clear Archive",
            "Are you absolutely sure you want to permanently delete ALL conversation logs?\nThis action cannot be undone.",
            icon="warning"
        )
        if confirm:
            success = DatabaseManager.clear_all_history(self.user_id)
            if success:
                self.load_history_list()
                messagebox.showinfo("Success", "All conversation history has been cleared.")
            else:
                messagebox.showerror("Error", "Failed to clear conversations database.")
