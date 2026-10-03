import customtkinter as ctk

FONT_MAIN = "Segoe UI"

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color="#0b131c", corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory
        self.grid_rowconfigure(2, weight=1)

        # 1. Título y Logo
        self.logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=20, pady=25, sticky="ew")
        
        self.icon_frame = ctk.CTkFrame(self.logo_frame, fg_color="#22d3ee", width=36, height=36, corner_radius=18)
        self.icon_frame.pack(side="left")
        self.icon_frame.pack_propagate(False)
        self.icon_label = ctk.CTkLabel(self.icon_frame, text="S", text_color="#06202a", font=ctk.CTkFont(family=FONT_MAIN, size=18, weight="bold"))
        self.icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        self.title_frame = ctk.CTkFrame(self.logo_frame, fg_color="transparent")
        self.title_frame.pack(side="left", padx=12)
        
        self.title_lbl = ctk.CTkLabel(self.title_frame, text="SismoLab AVL", font=ctk.CTkFont(family=FONT_MAIN, size=15, weight="bold"), text_color="#e8eef3")
        self.title_lbl.pack(anchor="w", pady=0)
        self.subtitle_lbl = ctk.CTkLabel(self.title_frame, text="OBS-UNI · v2.4.1", font=ctk.CTkFont(family=FONT_MAIN, size=10), text_color="#8a9bb0")
        self.subtitle_lbl.pack(anchor="w", pady=0)

        # 2. Menú de Navegación
        self.menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.menu_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.menu_frame.grid_columnconfigure(0, weight=1)
        
        self.create_menu_item("Dashboard", "Consola Maestra", active=False, row=0)
        self.create_menu_item("Árboles", "AVL vs BST", active=True, row=1)
        self.create_menu_item("Mapa", "1000x1000 km", active=False, row=2)
        self.create_menu_item("Eventos", "CRUD + Cola", active=False, row=3)
        self.create_menu_item("Consultas", "Top-k · Métricas", active=False, row=4)

        # 3. Balance Global
        self.balance_frame = ctk.CTkFrame(self, fg_color="#0e1620", border_color="#1e2d3d", border_width=1, corner_radius=12)
        self.balance_frame.grid(row=3, column=0, padx=15, pady=25, sticky="ew")
        
        self.lbl_balance_title = ctk.CTkLabel(self.balance_frame, text="BALANCE GLOBAL", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#8a9bb0")
        self.lbl_balance_title.pack(anchor="w", padx=15, pady=(15, 0))
        
        val_frame = ctk.CTkFrame(self.balance_frame, fg_color="transparent")
        val_frame.pack(anchor="w", padx=15, fill="x")
        self.lbl_balance_val = ctk.CTkLabel(val_frame, text="1.00", font=ctk.CTkFont(family=FONT_MAIN, size=24, weight="bold"), text_color="#2ecc71")
        self.lbl_balance_val.pack(side="left")
        self.lbl_balance_status = ctk.CTkLabel(val_frame, text="AVL OK", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#2ecc71")
        self.lbl_balance_status.pack(side="left", padx=5, pady=(8, 0))
        
        self.prog_bg = ctk.CTkFrame(self.balance_frame, height=4, fg_color="#1e2d3d", corner_radius=2)
        self.prog_bg.pack(fill="x", padx=15, pady=(5, 5))
        self.prog_fg = ctk.CTkFrame(self.prog_bg, width=150, height=4, fg_color="#2ecc71", corner_radius=2)
        self.prog_fg.pack(side="left", fill="y")
        self.prog_bg.pack_propagate(False)
        
        self.lbl_balance_sub = ctk.CTkLabel(self.balance_frame, text="n=0 · h=0 · BF∈[-1,1]", font=ctk.CTkFont(family=FONT_MAIN, size=9), text_color="#8a9bb0")
        self.lbl_balance_sub.pack(anchor="w", padx=15, pady=(0, 15))

        self.refresh()

    def refresh(self):
        """Calcula el factor de balance global real del árbol AVL activo."""
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

        self.lbl_balance_val.configure(text=f"{ratio:.2f}", text_color=color)
        self.lbl_balance_status.configure(text=status_text, text_color=color)
        self.prog_fg.configure(fg_color=color, width=int(200 * ratio))
        self.lbl_balance_sub.configure(text=f"n={total} · h={height_val} · BF∈[-1,1]")

    def create_menu_item(self, title, subtitle, active, row):
        bg_color = "#111c28" if active else "transparent"
        b_width = 1 if active else 0
        border_color = "#22d3ee" if active else "#0b131c"
        
        container = ctk.CTkFrame(self.menu_frame, fg_color=bg_color, corner_radius=8, border_width=b_width, border_color=border_color)
        container.grid(row=row, column=0, sticky="ew", pady=2, padx=5)
        container.grid_columnconfigure(1, weight=1)
        
        dot_color = "#22d3ee" if active else "#8a9bb0"
        dot = ctk.CTkFrame(container, width=6, height=6, corner_radius=3, fg_color=dot_color)
        dot.grid(row=0, column=0, padx=(15, 10), pady=18)
        
        text_frame = ctk.CTkFrame(container, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="w", pady=8)
        
        ctk.CTkLabel(text_frame, text=title, font=ctk.CTkFont(family=FONT_MAIN, size=13, weight="bold" if active else "normal"), text_color="#e8eef3", height=15).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=subtitle, font=ctk.CTkFont(family=FONT_MAIN, size=10), text_color="#8a9bb0", height=15).pack(anchor="w")
        
        if active:
            dot_right = ctk.CTkFrame(container, width=4, height=4, corner_radius=2, fg_color="#22d3ee")
            dot_right.grid(row=0, column=2, padx=15)
