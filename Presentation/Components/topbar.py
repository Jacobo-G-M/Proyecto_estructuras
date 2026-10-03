import customtkinter as ctk
from tkinter import filedialog, messagebox

FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"

class Topbar(ctk.CTkFrame):
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color="#0b131c", corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory
        
        self.grid_columnconfigure(3, weight=1)

        # 1. Reloj de Simulación
        self.clock_frame = ctk.CTkFrame(self, fg_color="#0e1620", border_color="#1e2d3d", border_width=1, corner_radius=10)
        self.clock_frame.grid(row=0, column=0, padx=20, pady=12, sticky="w")
        
        self.indicator = ctk.CTkFrame(self.clock_frame, width=8, height=8, corner_radius=4, fg_color="#2ecc71")
        self.indicator.grid(row=0, column=0, rowspan=2, padx=(15, 10), pady=12)
        
        self.lbl_clock_title = ctk.CTkLabel(self.clock_frame, text="SIM CLOCK · UTC", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#8a9bb0")
        self.lbl_clock_title.grid(row=0, column=1, sticky="w", pady=(8, 0))
        
        self.lbl_clock_time = ctk.CTkLabel(self.clock_frame, text="--", font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"), text_color="#e8eef3")
        self.lbl_clock_time.grid(row=1, column=1, sticky="w", pady=(0, 8), padx=(0, 15))
        
        self.btn_add_time = ctk.CTkButton(
            self.clock_frame, text="+1h", width=50, height=28, corner_radius=6,
            fg_color="#22d3ee", text_color="#06202a", font=ctk.CTkFont(family=FONT_MAIN, weight="bold"),
            command=self._on_add_hour
        )
        self.btn_add_time.grid(row=0, column=2, rowspan=2, padx=(0, 12))

        # 2. Módulo de Estrés
        self.stress_frame = ctk.CTkFrame(self, fg_color="#0e1620", border_color="#1e2d3d", border_width=1, corner_radius=10)
        self.stress_frame.grid(row=0, column=1, padx=10, pady=12, sticky="w")
        
        self.lbl_stress = ctk.CTkLabel(self.stress_frame, text="Estrés: Inactivo", text_color="#2ecc71", font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"))
        self.lbl_stress.grid(row=0, column=0, padx=15, pady=10)
        
        self.btn_recover = ctk.CTkButton(
            self.stress_frame, text="Recuperar Equilibrio AVL", height=28, corner_radius=6,
            fg_color="#ff7a1a", text_color="#fff4e8", hover_color="#d96311",
            font=ctk.CTkFont(family=FONT_MAIN, weight="bold"),
            command=self._on_toggle_stress_or_recover
        )
        self.btn_recover.grid(row=0, column=1, padx=(0, 10))

        # 3. Acciones (Deshacer, Exportar)
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=0, column=3, padx=20, pady=12, sticky="e")
        
        self.btn_undo = ctk.CTkButton(
            self.actions_frame, text="↩ Deshacer", height=32, corner_radius=8,
            fg_color="#0e1620", border_color="#1e2d3d", border_width=1,
            text_color="#e8eef3", hover_color="#111c28", font=ctk.CTkFont(family=FONT_MAIN, size=12),
            command=self._on_undo
        )
        self.btn_undo.pack(side="left", padx=5)
        
        self.btn_export = ctk.CTkButton(
            self.actions_frame, text="▾ Guardar JSON", height=32, corner_radius=8,
            fg_color="#0e1620", border_color="#1e2d3d", border_width=1,
            text_color="#e8eef3", hover_color="#111c28", font=ctk.CTkFont(family=FONT_MAIN, size=12),
            command=self._on_save_json
        )
        self.btn_export.pack(side="left", padx=5)

        self.btn_import = ctk.CTkButton(
            self.actions_frame, text="▴ Cargar JSON", height=32, corner_radius=8,
            fg_color="#0e1620", border_color="#1e2d3d", border_width=1,
            text_color="#e8eef3", hover_color="#111c28", font=ctk.CTkFont(family=FONT_MAIN, size=12),
            command=self._on_load_json
        )
        self.btn_import.pack(side="left", padx=5)

        self.refresh()

    def refresh(self):
        """Actualiza el reloj y el estado de estrés desde el observatorio."""
        if self.observatory is None:
            return

        dt = self.observatory.clock_simulation
        self.lbl_clock_time.configure(text=dt.strftime("%Y-%m-%dT%H:%M:%SZ"))

        if self.observatory.stress_mode:
            self.lbl_stress.configure(text="Estrés: Activo", text_color="#ff7a1a")
            self.btn_recover.configure(text="Recuperar Equilibrio AVL", fg_color="#ff7a1a")
        else:
            self.lbl_stress.configure(text="Estrés: Inactivo", text_color="#2ecc71")
            self.btn_recover.configure(text="Activar Estrés (BST)", fg_color="#111c28")

    def _on_add_hour(self):
        if self.observatory and self.app:
            self.observatory.update_clock(hours=1.0)
            archived = self.observatory.archive_expired_events()
            self.app.refresh_all()

    def _on_toggle_stress_or_recover(self):
        if not self.observatory or not self.app:
            return
        if self.observatory.stress_mode:
            self.observatory.global_recovery()
        else:
            self.observatory.stress_mode = True
        self.app.refresh_all()

    def _on_undo(self):
        if not self.observatory or not self.app:
            return
        success = self.observatory.undo_action()
        if not success:
            messagebox.showinfo("Deshacer", "No hay más acciones en la pila de deshacer.")
        self.app.refresh_all()

    def _on_save_json(self):
        if not self.observatory:
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Archivos JSON", "*.json")])
        if filepath:
            try:
                self.observatory.save_scenario(filepath)
                messagebox.showinfo("Éxito", f"Escenario exportado con éxito a:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Fallo al guardar: {e}")

    def _on_load_json(self):
        if not self.observatory or not self.app:
            return
        filepath = filedialog.askopenfilename(filetypes=[("Archivos JSON", "*.json")])
        if filepath:
            try:
                success, errors = self.observatory.load_scenario_by_topology(filepath)
                if success:
                    messagebox.showinfo("Éxito", "Escenario cargado exitosamente.")
                    self.app.refresh_all()
                else:
                    messagebox.showwarning("Advertencia", f"Errores al cargar:\n" + "\n".join(errors[:5]))
            except Exception as e:
                messagebox.showerror("Error", f"Fallo al cargar escenario: {e}")
