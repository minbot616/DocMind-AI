import customtkinter
from database import DatabaseManager
from typing import Callable, Optional

class AuthFrame(customtkinter.CTkFrame):
    """Handles login and registration interfaces within a single card layout."""

    def __init__(self, parent: customtkinter.CTk, on_success: Callable[[dict], None]):
        super().__init__(parent, fg_color=("#F8FAFC", "#000000"))
        self.parent = parent
        self.on_success = on_success
        self.is_register_mode = False

        # Configure grid for centering the auth card
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Auth Card Outer Container (simulating glassmorphism)
        self.card = customtkinter.CTkFrame(self, width=420, height=520, corner_radius=20, fg_color=("#FFFFFF", "#0B0B0B"), border_width=1, border_color=("#E2E8F0", "#1C1C1C"))
        self.card.grid(row=0, column=0, padx=40, pady=40, sticky="ns")
        self.card.grid_propagate(False)

        # Accent decoration bar at top
        self.accent_bar = customtkinter.CTkFrame(self.card, height=6, corner_radius=0, fg_color=("#4F46E5", "#6366F1"))
        self.accent_bar.place(x=0, y=0, relwidth=1)

        # Configure Auth Card Layout
        self.card.grid_columnconfigure(0, weight=1)
        self.card.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)

        # Title / Branding
        self.title_label = customtkinter.CTkLabel(
            self.card, 
            text="🧠 DocMind AI", 
            font=customtkinter.CTkFont(family="Outfit", size=32, weight="bold"),
            text_color=("#4F46E5", "#6366F1")
        )
        self.title_label.grid(row=0, column=0, pady=(45, 5), sticky="s")

        self.subtitle_label = customtkinter.CTkLabel(
            self.card, 
            text="Your intelligent desktop document assistant", 
            font=customtkinter.CTkFont(family="Inter", size=13),
            text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=0, pady=(0, 20), sticky="n")

        # Inputs
        self.username_entry = customtkinter.CTkEntry(
            self.card, 
            width=300, 
            height=45, 
            placeholder_text="Username",
            corner_radius=10,
            fg_color=("#F8FAFC", "#000000"),
            border_color=("#E2E8F0", "#1C1C1C"),
            border_width=1.5,
            text_color=("#0F172A", "#F8FAFC"),
            placeholder_text_color="gray"
        )
        self.username_entry.grid(row=2, column=0, pady=10)

        self.password_entry = customtkinter.CTkEntry(
            self.card, 
            width=300, 
            height=45, 
            placeholder_text="Password", 
            show="*",
            corner_radius=10,
            fg_color=("#F8FAFC", "#000000"),
            border_color=("#E2E8F0", "#1C1C1C"),
            border_width=1.5,
            text_color=("#0F172A", "#F8FAFC"),
            placeholder_text_color="gray"
        )
        self.password_entry.grid(row=3, column=0, pady=10)

        # Error / Feedback Label
        self.error_label = customtkinter.CTkLabel(
            self.card, 
            text="", 
            font=customtkinter.CTkFont(family="Inter", size=12), 
            text_color="#F43F5E"  # soft rose-red
        )
        self.error_label.grid(row=4, column=0, pady=5)

        # Action Buttons
        self.action_button = customtkinter.CTkButton(
            self.card, 
            text="Login", 
            width=300, 
            height=45, 
            corner_radius=10,
            font=customtkinter.CTkFont(family="Inter", size=14, weight="bold"),
            fg_color=("#4F46E5", "#6366F1"),
            hover_color=("#4338CA", "#4F46E5"),
            command=self.handle_auth
        )
        self.action_button.grid(row=5, column=0, pady=(10, 10))

        self.toggle_button = customtkinter.CTkButton(
            self.card, 
            text="New here? Create an account", 
            fg_color="transparent", 
            text_color=("#4F46E5", "#6366F1"),
            hover_color=("gray90", "gray15"),
            font=customtkinter.CTkFont(family="Inter", size=12),
            command=self.toggle_mode
        )
        self.toggle_button.grid(row=6, column=0, pady=(0, 30))

        # Handle Enter key press to submit
        self.username_entry.bind("<Return>", lambda e: self.handle_auth())
        self.password_entry.bind("<Return>", lambda e: self.handle_auth())

    def toggle_mode(self):
        """Switches between login and registration layout."""
        self.is_register_mode = not self.is_register_mode
        self.error_label.configure(text="")
        
        if self.is_register_mode:
            self.title_label.configure(text="🧠 Create Account")
            self.action_button.configure(text="Register")
            self.toggle_button.configure(text="Already have an account? Sign in")
        else:
            self.title_label.configure(text="🧠 DocMind AI")
            self.action_button.configure(text="Login")
            self.toggle_button.configure(text="New here? Create an account")

    def handle_auth(self):
        """Processes login or registration input."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.error_label.configure(text="Both fields are required.")
            return

        if len(password) < 6:
            self.error_label.configure(text="Password must be at least 6 characters.")
            return

        self.action_button.configure(state="disabled", text="Processing...")
        self.update()

        if self.is_register_mode:
            # Handle Registration
            success, msg = DatabaseManager.register_user(username, password)
            if success:
                # Automagic login on success
                user = DatabaseManager.authenticate_user(username, password)
                if user:
                    self.on_success(user)
            else:
                self.error_label.configure(text=msg)
                self.action_button.configure(state="normal", text="Register")
        else:
            # Handle Login
            user = DatabaseManager.authenticate_user(username, password)
            if user:
                self.on_success(user)
            else:
                self.error_label.configure(text="Invalid username or password.")
                self.action_button.configure(state="normal", text="Login")
