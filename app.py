import os
import warnings

# Suppress deprecation and user warnings (e.g., langchain, huggingface hub)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*HuggingFaceEmbeddings.*")
warnings.filterwarnings("ignore", message=".*HF_TOKEN.*")

import customtkinter
from database import DatabaseManager
from ui.login import AuthFrame
from ui.dashboard import DashboardFrame
from ui.upload import UploadFrame
from ui.chat import ChatFrame
from ui.history import HistoryFrame
from ui.settings import SettingsFrame
from ui.analytics import AnalyticsFrame

# App theme defaults
customtkinter.set_appearance_mode("Dark")  # Default mode before login
customtkinter.set_default_color_theme("blue")

class DocMindAIApp(customtkinter.CTk):
    """The main entry point class for DocMind AI desktop application.
    Manages navigation routing, auth state, theme settings, and frames lifecycle.
    """

    def __init__(self):
        super().__init__()

        # Configure Window
        self.title("DocMind AI - Desktop RAG Assistant")
        self.geometry("1150x700")
        self.minsize(1000, 620)
        
        # Center the window on display
        self.center_window(1150, 700)
        self.configure(fg_color=("#F8FAFC", "#000000"))

        # Global Session State
        self.current_user = None
        self.active_chat_id = None
        self.current_tab = "Dashboard"

        # Sidebar and Content Panel Placeholders
        self.sidebar_frame = None
        self.content_frame = None
        self.nav_buttons = {}

        # Show Login / Registration frame initially
        self.show_login_screen()

    def center_window(self, width: int, height: int):
        """Calculates screen dimensions to center window on launch."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def show_login_screen(self):
        """Destroys main app workspace and shows auth screen."""
        self.clear_workspace()
        self.auth_view = AuthFrame(self, on_success=self.on_login_success)
        self.auth_view.pack(fill="both", expand=True)

    def on_login_success(self, user_dict: dict):
        """Handles successful logins: registers session and initializes workspace."""
        self.current_user = user_dict
        
        # Load user theme preference
        settings = DatabaseManager.get_settings(self.current_user["id"])
        customtkinter.set_appearance_mode(settings.get("theme", "Dark"))
        
        # Destroys auth screen and creates layout
        self.auth_view.destroy()
        self.setup_main_layout()
        self.navigate_to("Dashboard")

    def setup_main_layout(self):
        """Builds the classic sidebar + main content panel template."""
        # Main Grid Layout (2 columns: Sidebar [0], Content [1])
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar Frame
        self.sidebar_frame = customtkinter.CTkFrame(self, width=200, corner_radius=0, fg_color=("#F1F5F9", "#0B0B0B"), border_width=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=0)
        self.sidebar_frame.grid_rowconfigure(7, weight=1)  # Spacer
        self.sidebar_frame.grid_rowconfigure(8, weight=0)  # Logout at bottom

        # Branding Header
        logo_lbl = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="🧠 DocMind AI",
            font=customtkinter.CTkFont(family="Outfit", size=22, weight="bold"),
            text_color=("#4F46E5", "#6366F1")
        )
        logo_lbl.grid(row=0, column=0, padx=20, pady=(25, 25))

        # Nav Buttons list with premium icons
        tabs = [
            ("📊  Dashboard", "Dashboard"),
            ("📁  Documents", "Documents"),
            ("💬  AI Chat", "AI Chat"),
            ("📈  Analytics", "Analytics"),
            ("⏳  History Log", "History Log"),
            ("⚙️  Settings", "Settings")
        ]

        for idx, (label, value) in enumerate(tabs):
            btn = customtkinter.CTkButton(
                self.sidebar_frame,
                text=label,
                font=customtkinter.CTkFont(family="Inter", size=13),
                fg_color="transparent",
                text_color=("#334155", "#E2E8F0"),
                hover_color=("#E2E8F0", "#334155"),
                anchor="w",
                height=40,
                corner_radius=10,
                command=lambda val=value: self.navigate_to(val)
            )
            # Row index matches (idx + 1) to account for Logo
            btn.grid(row=idx + 1, column=0, padx=15, pady=6, sticky="ew")
            self.nav_buttons[value] = btn

        # Bottom Logout Button
        logout_btn = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Logout",
            font=customtkinter.CTkFont(family="Inter", size=13),
            fg_color="#EF4444",
            hover_color="#DC2626",
            text_color="#FFFFFF",
            height=35,
            corner_radius=8,
            command=self.logout
        )
        logout_btn.grid(row=8, column=0, padx=15, pady=20, sticky="ew")

        # 2. Main Content Frame Container
        self.content_container = customtkinter.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

    def navigate_to(self, tab_name: str):
        """Switches the right-hand content view and updates sidebar highlights."""
        self.current_tab = tab_name
        
        # Reset colors of navigation buttons
        for key, btn in self.nav_buttons.items():
            btn.configure(
                fg_color="transparent", 
                text_color=("#334155", "#E2E8F0"),
                hover_color=("#E2E8F0", "#334155")
            )
            
        # Highlight selected
        self.nav_buttons[tab_name].configure(
            fg_color="#4F46E5", 
            text_color="#FFFFFF",
            hover_color="#4338CA"
        )

        # Clear active content view
        if self.content_frame:
            self.content_frame.destroy()

        user_id = self.current_user["id"]

        # Instantiate selected view frame
        if tab_name == "Dashboard":
            self.content_frame = DashboardFrame(self.content_container, user_id, self.navigate_to)
        elif tab_name == "Documents":
            self.content_frame = UploadFrame(self.content_container, user_id)
        elif tab_name == "AI Chat":
            self.content_frame = ChatFrame(self.content_container, user_id)
            # If we navigated from history with an active selection
            if self.active_chat_id:
                self.content_frame.start_or_load_chat(self.active_chat_id)
                self.active_chat_id = None  # Reset latch
        elif tab_name == "History Log":
            self.content_frame = HistoryFrame(self.content_container, user_id, self.load_chat_from_history)
        elif tab_name == "Analytics":
            self.content_frame = AnalyticsFrame(self.content_container, user_id)
        elif tab_name == "Settings":
            self.content_frame = SettingsFrame(self.content_container, user_id, self.apply_theme_change)

        self.content_frame.grid(row=0, column=0, sticky="nsew")

    def load_chat_from_history(self, chat_id: int):
        """Transition callback triggered by History screen to open chat logs."""
        self.active_chat_id = chat_id
        self.navigate_to("AI Chat")

    def apply_theme_change(self, theme: str):
        """Updates setting theme instantly across all active views."""
        customtkinter.set_appearance_mode(theme)

    def logout(self):
        """Clears auth state and session settings."""
        self.current_user = None
        self.active_chat_id = None
        self.show_login_screen()

    def clear_workspace(self):
        """Removes layout widgets on logout/re-logins."""
        # Unpack grids
        if self.sidebar_frame:
            self.sidebar_frame.destroy()
            self.sidebar_frame = None
        if hasattr(self, 'content_container') and self.content_container:
            self.content_container.destroy()
            
        self.nav_buttons.clear()

if __name__ == "__main__":
    app = DocMindAIApp()
    app.mainloop()
