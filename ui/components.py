import customtkinter

class MetricCard(customtkinter.CTkFrame):
    """A reusable card component for displaying metrics in the dashboard and analytics views."""

    def __init__(self, parent, title: str, main_val: str, footer_val: str, **kwargs):
        super().__init__(
            parent,
            corner_radius=10,
            height=100,
            fg_color=("#FFFFFF", "#0B0B0B"),
            border_width=1,
            border_color=("#E2E8F0", "#1C1C1C"),
            **kwargs
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        self.title_lbl = customtkinter.CTkLabel(
            self,
            text=title,
            font=customtkinter.CTkFont(family="Inter", size=11, weight="bold"),
            text_color="gray",
            anchor="w"
        )
        self.title_lbl.pack(fill="x", padx=15, pady=(10, 2))

        # Truncate main value if needed
        display_val = main_val[:25] + "..." if len(main_val) > 28 else main_val
        self.main_lbl = customtkinter.CTkLabel(
            self,
            text=display_val,
            font=customtkinter.CTkFont(family="Outfit", size=18, weight="bold"),
            anchor="w"
        )
        self.main_lbl.pack(fill="x", padx=15, pady=0)

        self.footer_lbl = customtkinter.CTkLabel(
            self,
            text=footer_val,
            font=customtkinter.CTkFont(family="Inter", size=10),
            text_color="gray",
            anchor="w"
        )
        self.footer_lbl.pack(fill="x", padx=15, pady=(2, 8))

    def update_values(self, main_val: str, footer_val: str):
        """Allows dynamically updating values on the metric card."""
        display_val = main_val[:25] + "..." if len(main_val) > 28 else main_val
        self.main_lbl.configure(text=display_val)
        self.footer_lbl.configure(text=footer_val)
