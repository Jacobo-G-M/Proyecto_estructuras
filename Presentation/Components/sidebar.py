import os
from PIL import Image
import customtkinter as ctk

FONT_MAIN = "Segoe UI"

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color="#0b131c", corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory
        self.active_key = "dashboard"
        self.menu_items = {}

        self.grid_rowconfigure(2, weight=1)

        # 1. Official Title and Logo
        self.logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=14, pady=20, sticky="ew")
        
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                pil_logo = Image.open(logo_path)
                self.logo_img = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(38, 38))
                self.icon_label = ctk.CTkLabel(self.logo_frame, image=self.logo_img, text="")
                self.icon_label.pack(side="left")
            except Exception:
                self._create_fallback_logo()
        else:
            self._create_fallback_logo()
        
        self.title_frame = ctk.CTkFrame(self.logo_frame, fg_color="transparent")
        self.title_frame.pack(side="left", padx=10)
        
        self.title_lbl = ctk.CTkLabel(self.title_frame, text="SismoLab AVL", font=ctk.CTkFont(family=FONT_MAIN, size=14, weight="bold"), text_color="#e8eef3")
        self.title_lbl.pack(anchor="w", pady=0)
        self.subtitle_lbl = ctk.CTkLabel(self.title_frame, text="v1.0", font=ctk.CTkFont(family=FONT_MAIN, size=10), text_color="#8a9bb0")
        self.subtitle_lbl.pack(anchor="w", pady=0)

        # 2. Interactive Navigation Menu
        self.menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.menu_frame.grid(row=1, column=0, padx=8, pady=8, sticky="ew")
        self.menu_frame.grid_columnconfigure(0, weight=1)
        
        self._create_nav_item("dashboard", "Panel de Control", row=0)
        self._create_nav_item("arboles", "Árboles", row=1)
        self._create_nav_item("mapa", "Mapa", row=2)
        self._create_nav_item("eventos", "Eventos", row=3)
        self._create_nav_item("consultas", "Consultas", row=4)

        # 3. Global Balance
        self.balance_frame = ctk.CTkFrame(self, fg_color="#0e1620", border_color="#1e2d3d", border_width=1, corner_radius=10)
        self.balance_frame.grid(row=3, column=0, padx=12, pady=18, sticky="ew")
        
        self.lbl_balance_title = ctk.CTkLabel(self.balance_frame, text="BALANCE GLOBAL", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#8a9bb0")
        self.lbl_balance_title.pack(anchor="w", padx=12, pady=(12, 0))
        
        val_frame = ctk.CTkFrame(self.balance_frame, fg_color="transparent")
        val_frame.pack(anchor="w", padx=12, fill="x")
        self.lbl_balance_val = ctk.CTkLabel(val_frame, text="100%", font=ctk.CTkFont(family=FONT_MAIN, size=22, weight="bold"), text_color="#2ecc71")
        self.lbl_balance_val.pack(side="left")
        self.lbl_balance_status = ctk.CTkLabel(val_frame, text="AVL OK", font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"), text_color="#2ecc71")
        self.lbl_balance_status.pack(side="left", padx=5, pady=(6, 0))
        
        self.progress_bar = ctk.CTkProgressBar(self.balance_frame, height=5, corner_radius=2, fg_color="#1e2d3d", progress_color="#2ecc71")
        self.progress_bar.pack(fill="x", padx=12, pady=(6, 12))
        self.progress_bar.set(1.0)

        self.set_active("dashboard")
        self.refresh()

    def _create_fallback_logo(self):
        icon_frame = ctk.CTkFrame(self.logo_frame, fg_color="#22d3ee", width=34, height=34, corner_radius=17)
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        self.icon_label = ctk.CTkLabel(icon_frame, text="S", text_color="#06202a", font=ctk.CTkFont(family=FONT_MAIN, size=16, weight="bold"))
        self.icon_label.place(relx=0.5, rely=0.5, anchor="center")

    def _create_nav_item(self, key: str, title: str, row: int):
        container = ctk.CTkFrame(self.menu_frame, fg_color="transparent", corner_radius=8, border_width=0, border_color="#0b131c")
        container.grid(row=row, column=0, sticky="ew", pady=3, padx=5)
        container.grid_columnconfigure(1, weight=1)
        
        # Indicator dot
        dot = ctk.CTkFrame(container, width=6, height=6, corner_radius=3, fg_color="#8a9bb0")
        dot.grid(row=0, column=0, padx=(15, 10), pady=10)
        
        # Main title
        lbl_title = ctk.CTkLabel(container, text=title, font=ctk.CTkFont(family=FONT_MAIN, size=14), text_color="#8a9bb0")
        lbl_title.grid(row=0, column=1, sticky="w", pady=8)
        
        # Right dot
        dot_right = ctk.CTkFrame(container, width=4, height=4, corner_radius=2, fg_color="#22d3ee")
        dot_right.grid(row=0, column=2, padx=15)
        dot_right.grid_remove()

        # Save references
        self.menu_items[key] = {
            "container": container,
            "dot": dot,
            "title": lbl_title,
            "dot_right": dot_right
        }

        # Bind clicks on all sub-elements
        for widget in (container, dot, lbl_title):
            widget.bind("<Button-1>", lambda e, k=key: self._on_item_click(k))
            widget.bind("<Enter>", lambda e, k=key: self._on_item_hover(k, True))
            widget.bind("<Leave>", lambda e, k=key: self._on_item_hover(k, False))

    def _on_item_click(self, key: str):
        if self.app:
            self.app.switch_view(key)

    def _on_item_hover(self, key: str, is_hover: bool):
        if key == self.active_key:
            return
        item = self.menu_items.get(key)
        if item:
            item["container"].configure(fg_color="#101924" if is_hover else "transparent")

    def set_active(self, key: str):
        """Updates the visual style of the active element in the menu."""
        self.active_key = key
        for k, item in self.menu_items.items():
            is_active = (k == key)
            if is_active:
                item["container"].configure(fg_color="#111c28", border_width=1, border_color="#22d3ee")
                item["dot"].configure(fg_color="#22d3ee")
                item["title"].configure(text_color="#e8eef3", font=ctk.CTkFont(family=FONT_MAIN, size=14, weight="bold"))
                item["dot_right"].grid()
            else:
                item["container"].configure(fg_color="transparent", border_width=0, border_color="#0b131c")
                item["dot"].configure(fg_color="#8a9bb0")
                item["title"].configure(text_color="#8a9bb0", font=ctk.CTkFont(family=FONT_MAIN, size=14, weight="normal"))
                item["dot_right"].grid_remove()

    def refresh(self):
        """Calculates the actual global balance factor of the active AVL tree."""
        if not self.observatory or not self.observatory.tree:
            return

        nodes = self.observatory.tree.inorder()
        total = len(nodes)
        height_val = self.observatory.tree.height()

        if total > 0:
            balanced = sum(1 for n in nodes if abs(n.balance_factor()) <= 1)
            ratio = round(balanced / total, 2)
        else:
            ratio = 1.00

        color = "#2ecc71" if ratio >= 0.8 else ("#ff7a1a" if ratio >= 0.5 else "#ff3b5c")
        status_text = "AVL OK" if ratio >= 0.8 else "DESBALANCE"
        pct = int(ratio * 100)

        self.lbl_balance_val.configure(text=f"{pct}%", text_color=color)
        self.lbl_balance_status.configure(text=status_text, text_color=color)
        self.progress_bar.configure(progress_color=color)
        self.progress_bar.set(ratio)
