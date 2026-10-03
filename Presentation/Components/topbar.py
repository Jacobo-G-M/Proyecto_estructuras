import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"

class Topbar(ctk.CTkFrame):
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color="#070c12", corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory
        
        self.grid_columnconfigure(3, weight=1)

        # 1. Módulo del Reloj (Izquierda)
        self.clock_frame = ctk.CTkFrame(
            self, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=10
        )
        self.clock_frame.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        self.indicator = ctk.CTkFrame(self.clock_frame, width=8, height=8, corner_radius=4, fg_color="#2ecc71")
        self.indicator.grid(row=0, column=0, rowspan=2, padx=(12, 8), pady=10)
        
        self.lbl_clock_title = ctk.CTkLabel(
            self.clock_frame, text="Reloj", font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"), text_color="#8a9bb0"
        )
        self.lbl_clock_title.grid(row=0, column=1, sticky="w", pady=(6, 0))
        
        self.lbl_clock_time = ctk.CTkLabel(
            self.clock_frame, text="--", font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"), text_color="#e8eef3"
        )
        self.lbl_clock_time.grid(row=1, column=1, sticky="w", pady=(0, 6), padx=(0, 12))
        
        # Botón +1h rápido
        self.btn_add_time = ctk.CTkButton(
            self.clock_frame, text="+1h", width=44, height=28, corner_radius=6,
            fg_color="#22d3ee", text_color="#06202a", font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            hover_color="#38e1fc", command=self._on_add_hour
        )
        self.btn_add_time.grid(row=0, column=2, rowspan=2, padx=(0, 6), pady=8)

        # Entrada de horas personalizada y botón de suma
        self.entry_custom_hours = ctk.CTkEntry(
            self.clock_frame, width=46, height=28, corner_radius=6,
            placeholder_text="h", justify="center",
            fg_color="#101922", border_color="#1a2736", text_color="#e8eef3",
            font=ctk.CTkFont(family=FONT_MAIN, size=12)
        )
        self.entry_custom_hours.grid(row=0, column=3, rowspan=2, padx=(0, 4), pady=8)
        self.entry_custom_hours.bind("<Return>", self._on_add_custom_hours)

        self.btn_add_custom = ctk.CTkButton(
            self.clock_frame, text="+", width=30, height=28, corner_radius=6,
            fg_color="#101922", border_color="#22d3ee", border_width=1,
            hover_color="#1b2a3a", text_color="#22d3ee",
            font=ctk.CTkFont(family=FONT_MAIN, size=13, weight="bold"),
            command=self._on_add_custom_hours
        )
        self.btn_add_custom.grid(row=0, column=4, rowspan=2, padx=(0, 10), pady=8)

        # 2. Módulo de Estrés (Centro)
        self.stress_frame = ctk.CTkFrame(
            self, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=10
        )
        self.stress_frame.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Switch interactivo en el lado izquierdo
        self.switch_stress = ctk.CTkSwitch(
            self.stress_frame,
            text="Estrés: Inactivo",
            font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            text_color="#2ecc71",
            progress_color="#ff7a1a",
            button_color="#ffffff",
            button_hover_color="#f0f0f0",
            fg_color="#1a2736",
            switch_width=38,
            switch_height=20,
            command=self._on_switch_stress_toggle
        )
        self.switch_stress.grid(row=0, column=0, padx=(12, 10), pady=8)
        
        # Botón de recuperación: se activa solo cuando el switch pone el sistema en estrés
        self.btn_recover = ctk.CTkButton(
            self.stress_frame,
            text="Recuperar Equilibrio AVL",
            height=28,
            corner_radius=6,
            fg_color="#101922",
            text_color="#536477",
            border_color="#1a2736",
            border_width=1,
            hover_color="#101922",
            font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            state="disabled",
            command=self._on_recover_click
        )
        self.btn_recover.grid(row=0, column=1, padx=(0, 10), pady=8)

        # 3. Acciones (Deshacer, JSON, Versión)
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=0, column=3, padx=20, pady=10, sticky="e")
        
        self.btn_undo = ctk.CTkButton(
            self.actions_frame, text="↩ Deshacer", height=30, corner_radius=6,
            fg_color="#0b131c", border_color="#1a2736", border_width=1,
            text_color="#e8eef3", hover_color="#142130", font=ctk.CTkFont(family=FONT_MAIN, size=12),
            command=self._on_undo
        )
        self.btn_undo.pack(side="left", padx=4)
        
        self.btn_load = ctk.CTkButton(
            self.actions_frame, text="▲ Cargar JSON", height=30, corner_radius=6,
            fg_color="#0b131c", border_color="#1a2736", border_width=1,
            text_color="#e8eef3", hover_color="#142130", font=ctk.CTkFont(family=FONT_MAIN, size=12),
            command=self._on_load_json
        )
        self.btn_load.pack(side="left", padx=4)

        self.btn_export = ctk.CTkButton(
            self.actions_frame, text="▾ Exportar JSON", height=30, corner_radius=6,
            fg_color="#0b131c", border_color="#1a2736", border_width=1,
            text_color="#e8eef3", hover_color="#142130", font=ctk.CTkFont(family=FONT_MAIN, size=12),
            command=self._on_save_json
        )
        self.btn_export.pack(side="left", padx=4)

        # Pill de versión
        self.version_pill = ctk.CTkFrame(
            self.actions_frame, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=6
        )
        self.version_pill.pack(side="left", padx=4)
        ctk.CTkLabel(
            self.version_pill, text="▾ v12 · Andina-Norte",
            font=ctk.CTkFont(family=FONT_MAIN, size=12), text_color="#8a9bb0"
        ).pack(padx=10, pady=4)

        self.refresh()

    def refresh(self):
        """Actualiza el reloj y el estado de estrés desde el observatorio."""
        if self.observatory is None:
            return

        dt = self.observatory.clock_simulation
        if dt:
            self.lbl_clock_time.configure(text=dt.strftime("%Y-%m-%d  %H:%M:%S"))
        else:
            self.lbl_clock_time.configure(text="--")

        if self.observatory.stress_mode:
            self.switch_stress.select()
            self.switch_stress.configure(text="Estrés: Activo", text_color="#ff7a1a")
            self.btn_recover.configure(
                state="normal",
                text="Recuperar Equilibrio AVL",
                fg_color="#ff7a1a",
                text_color="#fff4e8",
                hover_color="#d96311",
                border_width=0
            )
        else:
            self.switch_stress.deselect()
            self.switch_stress.configure(text="Estrés: Inactivo", text_color="#2ecc71")
            self.btn_recover.configure(
                state="disabled",
                text="Recuperar Equilibrio AVL",
                fg_color="#101922",
                text_color="#536477",
                hover_color="#101922",
                border_width=1,
                border_color="#1a2736"
            )

    def _on_add_hour(self):
        if self.observatory and self.app:
            self.observatory.update_clock(hours=1.0)
            self.observatory.archive_expired_events()
            self.app.refresh_all()

    def _on_add_custom_hours(self, event=None):
        if not self.observatory or not self.app:
            return
        val_str = self.entry_custom_hours.get().strip()
        if not val_str:
            return
        try:
            hrs = float(val_str)
            if hrs <= 0:
                messagebox.showwarning("Reloj", "Por favor ingresa un número de horas mayor a 0.")
                return
            self.observatory.update_clock(hours=hrs)
            self.observatory.archive_expired_events()
            self.app.refresh_all()
            self.entry_custom_hours.delete(0, "end")
        except ValueError:
            messagebox.showerror("Reloj", f"'{val_str}' no es un número válido de horas.")

    def _on_switch_stress_toggle(self):
        if not self.observatory or not self.app:
            return
        if self.switch_stress.get() == 1:
            self.observatory.stress_mode = True
        else:
            self.observatory.global_recovery()
        self.app.refresh_all()

    def _on_recover_click(self):
        if not self.observatory or not self.app:
            return
        self.observatory.global_recovery()
        self.app.refresh_all()

    def _on_toggle_stress_or_recover(self):
        self._on_recover_click()

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
        target_dir = getattr(self.observatory, "VERSIONS_DIR", None)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
            target_dir = os.path.abspath(target_dir)

        filepath = filedialog.asksaveasfilename(
            title="Exportar Escenario JSON",
            initialdir=target_dir,
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        if filepath:
            try:
                self.observatory.save_scenario(filepath)
                messagebox.showinfo("Éxito", f"Escenario exportado con éxito a:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Fallo al guardar: {e}")

    def _on_load_json(self):
        if not self.observatory or not self.app:
            return
        target_dir = getattr(self.observatory, "VERSIONS_DIR", None)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
            target_dir = os.path.abspath(target_dir)

        filepath = filedialog.askopenfilename(
            title="Cargar Escenario JSON",
            initialdir=target_dir,
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        if filepath:
            try:
                # 1. Intentar carga atómica canónica por topología
                ok, errors = self.observatory.load_scenario_by_topology(filepath)
                if ok:
                    messagebox.showinfo(
                        "Éxito",
                        f"Escenario cargado exitosamente desde:\n{os.path.basename(filepath)}"
                    )
                    self.app.refresh_all()
                else:
                    # 2. Fallback a inserciones si el JSON contiene lista plana de eventos
                    try:
                        res = self.observatory.load_scenario_by_insertions(filepath, adopt_avl=True)
                        if res and "avl" in res:
                            messagebox.showinfo(
                                "Éxito",
                                f"Escenario de eventos cargado exitosamente desde:\n{os.path.basename(filepath)}"
                            )
                            self.app.refresh_all()
                        else:
                            err_msg = "\n".join(errors[:5]) if errors else "Estructura de archivo inválida."
                            messagebox.showerror("Error al Cargar", f"No se pudo cargar el archivo:\n{err_msg}")
                    except Exception:
                        err_msg = "\n".join(errors[:5]) if errors else "Estructura de archivo inválida."
                        messagebox.showerror("Error al Cargar", f"No se pudo cargar el archivo:\n{err_msg}")
            except Exception as e:
                messagebox.showerror("Error", f"Fallo al abrir archivo: {e}")
