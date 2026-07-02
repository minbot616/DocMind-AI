import os
import fitz
from PIL import Image
from io import BytesIO
import customtkinter

class PDFPageViewer(customtkinter.CTkToplevel):
    """A pop-up modal dialog that renders and displays a specific PDF page as an image,
    or page text for other file formats, directly inside the CustomTkinter GUI.
    """
    
    def __init__(self, parent, file_path: str, page_num: int):
        super().__init__(parent)
        self.file_path = file_path
        self.page_num = page_num
        
        self.title(f"Page Viewer - {os.path.basename(file_path)} (Page {page_num})")
        self.geometry("640x780")
        
        # Center popup on parent
        self.center_window()
        self.grab_set()
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Title header
        self.grid_rowconfigure(1, weight=1) # Scrollable area
        
        # Title Label
        title_lbl = customtkinter.CTkLabel(
            self,
            text=f"📄 Page {page_num} of {os.path.basename(file_path)}",
            font=customtkinter.CTkFont(family="Outfit", size=15, weight="bold")
        )
        title_lbl.grid(row=0, column=0, padx=20, pady=(15, 5))
        
        # Scrollable image/text frame
        self.scroll_frame = customtkinter.CTkScrollableFrame(self, fg_color=("#F1F5F9", "#0B0B0B"))
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(5, 15))
        
        # Load and render content
        ext = os.path.splitext(self.file_path.lower())[1]
        if ext != ".pdf":
            self.render_text_page()
        else:
            self.render_pdf_page()
        
    def center_window(self):
        self.update_idletasks()
        width = 640
        height = 780
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def render_pdf_page(self):
        if not os.path.exists(self.file_path):
            lbl = customtkinter.CTkLabel(self.scroll_frame, text="Error: Source file not found on disk.", text_color="red")
            lbl.pack(pady=40)
            return
            
        try:
            # 1. Render page image using PyMuPDF (fitz)
            doc = fitz.open(self.file_path)
            
            # Bound page number
            tot_pages = len(doc)
            page_idx = max(0, min(tot_pages - 1, self.page_num - 1))
            
            page = doc.load_page(page_idx)
            # Use 150 DPI for high quality rendering
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("ppm")
            doc.close()
            
            # 2. Open PIL image
            pil_img = Image.open(BytesIO(img_bytes))
            
            # 3. Scale PIL image to fit CTkToplevel width
            w, h = pil_img.size
            max_width = 560
            scale = max_width / w
            scaled_w = int(w * scale)
            scaled_h = int(h * scale)
            
            # 4. Convert to CTkImage
            ctk_img = customtkinter.CTkImage(
                light_image=pil_img,
                dark_image=pil_img,
                size=(scaled_w, scaled_h)
            )
            
            # Keep a reference to prevent garbage collection
            self.rendered_image = ctk_img
            
            # 5. Pack in scrollable container
            img_lbl = customtkinter.CTkLabel(self.scroll_frame, image=ctk_img, text="")
            img_lbl.pack(padx=10, pady=10)
            
        except Exception as e:
            lbl = customtkinter.CTkLabel(self.scroll_frame, text=f"Failed to render page image: {str(e)}", text_color="red")
            lbl.pack(pady=40)

    def render_text_page(self):
        try:
            # Extract text using DocumentProcessor
            from document_processor import DocumentProcessor
            pages = DocumentProcessor.process_document(self.file_path)
            
            # Find the text of the matching page
            page_idx = max(0, min(len(pages) - 1, self.page_num - 1))
            page_text = pages[page_idx]["text"] if pages else "No text content found on this page."
            
            # Display inside a read-only CTkTextbox
            textbox = customtkinter.CTkTextbox(
                self.scroll_frame,
                width=560,
                height=650,
                font=customtkinter.CTkFont(family="Inter", size=12),
                fg_color=("#FFFFFF", "#000000"),
                border_color=("#E2E8F0", "#1C1C1C"),
                border_width=1
            )
            textbox.pack(padx=10, pady=10, fill="both", expand=True)
            textbox.insert("1.0", page_text)
            textbox.configure(state="disabled")
        except Exception as e:
            lbl = customtkinter.CTkLabel(self.scroll_frame, text=f"Failed to extract page text: {str(e)}", text_color="red")
            lbl.pack(pady=40)
