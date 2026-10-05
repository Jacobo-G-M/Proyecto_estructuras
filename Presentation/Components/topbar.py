import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"

class Topbar(ctk.CTkFrame):
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color="#070c12", corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory
        
        self.grid_columnconfigure(3, weight=1)

        self._is_compact = False

        # 1. Clock Module (Left)
        self.clock_frame = ctk.CTkFrame(
            self, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=10
        )
        self.clock_frame.grid(row=0, column=0, padx=(10, 5), pady=8, sticky="w")
        
        # Symmetrical container for Label, Time and Date
        time_box = ctk.CTkFrame(self.clock_frame, fg_color="transparent")
        time_box.grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=4)
        
        # Top context label
        self.lbl_clock_tag = ctk.CTkLabel(
            time_box, text="RELOJ", height=12,
            font=ctk.CTkFont(family=FONT_MAIN, size=9, weight="bold"),
            text_color="#22d3ee"
        )
        self.lbl_clock_tag.pack(anchor="center", pady=(1, 0))

        # Prominent time in the center
        self.lbl_clock_time = ctk.CTkLabel(
            time_box, text="--:--:--", height=18,
            font=ctk.CTkFont(family=FONT_MONO, size=14, weight="bold"),
            text_color="#ffffff"
        )
        self.lbl_clock_time.pack(anchor="center", pady=(0, 0))
        
        # Date below
        self.lbl_clock_date = ctk.CTkLabel(
            time_box, text="----/--/--", height=12,
            font=ctk.CTkFont(family=FONT_MAIN, size=10),
            text_color="#8a9bb0"
        )
        self.lbl_clock_date.pack(anchor="center", pady=(0, 1))
        
        # Quick +1h button
        self.btn_add_time = ctk.CTkButton(
            self.clock_frame, text="+1h", width=40, height=28, corner_radius=6,
            fg_color="#22d3ee", text_color="#06202a", font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            hover_color="#38e1fc", command=self._on_add_hour
        )
        self.btn_add_time.grid(row=0, column=1, rowspan=2, padx=(0, 4), pady=6)

        # Custom time input and add button
        self.entry_custom_hours = ctk.CTkEntry(
            self.clock_frame, width=42, height=28, corner_radius=6,
            placeholder_text="h", justify="center",
            fg_color="#101922", border_color="#1a2736", text_color="#e8eef3",
            font=ctk.CTkFont(family=FONT_MAIN, size=12)
        )
        self.entry_custom_hours.grid(row=0, column=2, rowspan=2, padx=(0, 4), pady=6)
        self.entry_custom_hours.bind("<Return>", self._on_add_custom_hours)

        self.btn_add_custom = ctk.CTkButton(
            self.clock_frame, text="+", width=28, height=28, corner_radius=6,
            fg_color="#101922", border_color="#22d3ee", border_width=1,
            hover_color="#1b2a3a", text_color="#22d3ee",
            font=ctk.CTkFont(family=FONT_MAIN, size=13, weight="bold"),
            command=self._on_add_custom_hours
        )
        self.btn_add_custom.grid(row=0, column=3, rowspan=2, padx=(0, 8), pady=6)

        # 2. Stress Module (Center)
        self.stress_frame = ctk.CTkFrame(
            self, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=10
        )
        self.stress_frame.grid(row=0, column=1, padx=5, pady=8, sticky="w")
        
        # Interactive switch on the left side
        self.switch_stress = ctk.CTkSwitch(
            self.stress_frame,
            text="Estrés: Inactivo",
            font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            text_color="#2ecc71",
            progress_color="#ff7a1a",
            button_color="#ffffff",
            button_hover_color="#f0f0f0",
            fg_color="#1a2736",
            switch_width=36,
            switch_height=18,
            command=self._on_switch_stress_toggle
        )
        self.switch_stress.grid(row=0, column=0, padx=(10, 8), pady=6)
        
        # Recovery button: activated only when the switch puts the system in stress
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
            font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"),
            state="disabled",
            command=self._on_recover_click
        )
        self.btn_recover.grid(row=0, column=1, padx=(0, 8), pady=6)

        # 3. Actions (Undo, JSON, Version)
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=0, column=3, padx=(5, 12), pady=8, sticky="e")
        
        self.btn_undo = ctk.CTkButton(
            self.actions_frame, text="↩ Deshacer", height=30, corner_radius=6,
            fg_color="#0b131c", border_color="#1a2736", border_width=1,
            text_color="#e8eef3", hover_color="#142130", font=ctk.CTkFont(family=FONT_MAIN, size=12),
            command=self._on_undo
        )
        self.btn_undo.pack(side="left", padx=3)
        
        # Interactive version pill / Active Scenario
        self.current_scenario_name = getattr(self.observatory, 'current_scenario_name', "Sin_titulo") if self.observatory else "Sin_titulo"
        self.current_scenario_filepath = getattr(self.observatory, 'current_scenario_filepath', None) if self.observatory else None
        self.version_pill = ctk.CTkFrame(
            self.actions_frame, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=6,
            cursor="hand2"
        )
        self.version_pill.pack(side="left", padx=3)
        display = self.current_scenario_name if len(self.current_scenario_name) <= 16 else f"{self.current_scenario_name[:13]}..."
        self.lbl_version = ctk.CTkLabel(
            self.version_pill, text=f"▾ {display}",
            font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"), text_color="#38bdf8",
            cursor="hand2"
        )
        self.lbl_version.pack(padx=8, pady=4)

        for widget in (self.version_pill, self.lbl_version):
            widget.bind("<Button-1>", self._on_scenario_pill_click)
            widget.bind("<Enter>", lambda e: self.version_pill.configure(border_color="#38bdf8", fg_color="#101a26"))
            widget.bind("<Leave>", lambda e: self.version_pill.configure(border_color="#1a2736", fg_color="#0b131c"))

        # Automatic adaptability to window size changes
        self.bind("<Configure>", self._on_resize)
        self.refresh()

    def _on_resize(self, event):
        """Dynamically adjusts buttons and components to avoid clipping."""
        if event.width <= 10:
            return

        is_narrow = event.width < 980
        if is_narrow != self._is_compact:
            self._is_compact = is_narrow
            if hasattr(self, "btn_recover"):
                self.btn_recover.configure(text="Recuperar AVL" if is_narrow else "Recuperar Equilibrio AVL")

    def refresh(self):
        """Updates the clock and the stress state from the observatory."""
        if self.observatory is None:
            return

        dt = self.observatory.clock_simulation
        if dt:
            self.lbl_clock_time.configure(text=dt.strftime("%H:%M:%S"))
            self.lbl_clock_date.configure(text=dt.strftime("%Y-%m-%d"))
        else:
            self.lbl_clock_time.configure(text="--:--:--")
            self.lbl_clock_date.configure(text="--")

        recover_text = "Recuperar AVL" if self._is_compact else "Recuperar Equilibrio AVL"
        if self.observatory.stress_mode:
            self.switch_stress.select()
            self.switch_stress.configure(text="Estrés: Activo", text_color="#ff7a1a")
            self.btn_recover.configure(
                state="normal",
                text=recover_text,
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
                text=recover_text,
                fg_color="#101922",
                text_color="#536477",
                hover_color="#101922",
                border_width=1,
                border_color="#1a2736"
            )

        # Synchronize active scenario with the observatory
        if self.observatory and hasattr(self.observatory, 'current_scenario_name'):
            obs_name = self.observatory.current_scenario_name or "Demo Activo"
            if self.current_scenario_name != obs_name:
                self.set_scenario_name(obs_name)
            self.current_scenario_filepath = getattr(self.observatory, 'current_scenario_filepath', None)

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
            self.app.refresh_all()
        else:
            self._execute_recovery_flow()

    def _on_recover_click(self):
        self._execute_recovery_flow()

    def _execute_recovery_flow(self):
        """
        Executes the global AVL balance recovery protocol:
        1. Pauses continuous report processing if active (official requirement).
        2. Executes in-place global rebalance in the observatory.
        3. Refreshes all application views.
        4. Displays informative popup with rotation breakdowns and costs.
        """
        if not self.observatory or not self.app:
            return

        # 1. Pause report processing if the events view is running in burst mode
        if hasattr(self.app, "views") and isinstance(self.app.views, dict):
            events_view = self.app.views.get("eventos")
            if events_view and getattr(events_view, "burst_running", False):
                if hasattr(events_view, "_handle_pause_burst"):
                    events_view._handle_pause_burst()

        # 2. Global in-situ rebalancing
        result = self.observatory.global_recovery()

        # 3. Refresh all screens to reflect new tree and normal state
        self.app.refresh_all()

        # 4. Show informative popup window with changes report and costs
        if result:
            from Presentation.Components.Molecules.recovery_modal import RecoveryReportModal
            RecoveryReportModal(self.app, result=result)

    def _on_toggle_stress_or_recover(self):
        self._on_recover_click()

    def _on_undo(self):
        if not self.observatory or not self.app:
            return
        try:
            success = self.observatory.undo_action()
            if not success:
                messagebox.showinfo("Deshacer", "No hay más acciones en la pila de deshacer.")
        except ValueError as e:
            messagebox.showinfo("Deshacer", str(e))
        self.app.refresh_all()

    def set_scenario_name(self, name: str):
        """Updates the active scenario name in the top pill and in the observatory."""
        if not name:
            name = "Demo Activo"
        if name.endswith(".json"):
            name = name[:-5]
        self.current_scenario_name = name
        if self.observatory and hasattr(self.observatory, 'current_scenario_name'):
            self.observatory.current_scenario_name = name
        if hasattr(self, 'current_scenario_filepath') and self.observatory and hasattr(self.observatory, 'current_scenario_filepath'):
            self.observatory.current_scenario_filepath = self.current_scenario_filepath
        display = name if len(name) <= 16 else f"{name[:13]}..."
        if hasattr(self, "lbl_version"):
            self.lbl_version.configure(text=f"▾ {display}")

    def _on_scenario_pill_click(self, event=None):
        """Displays a popup menu with available scenarios in saved_versions/."""
        if not self.observatory:
            return

        target_dir = getattr(self.observatory, "VERSIONS_DIR", None)
        if not target_dir:
            target_dir = os.path.abspath("saved_versions")
        os.makedirs(target_dir, exist_ok=True)

        self.version_pill.update_idletasks()

        menu = tk.Menu(
            self,
            tearoff=0,
            bg="#0b131c",
            fg="#e8eef3",
            activebackground="#1e293b",
            activeforeground="#38bdf8",
            relief="solid",
            bd=1,
            font=(FONT_MAIN, 10)
        )

        menu.add_command(
            label="📁 Escenarios Guardados:",
            state="disabled"
        )
        menu.add_separator()

        # List existing JSON files in saved_versions/
        json_files = []
        try:
            for f in sorted(os.listdir(target_dir)):
                if f.lower().endswith(".json"):
                    json_files.append(f)
        except Exception:
            pass

        if json_files:
            for fname in json_files:
                stem = os.path.splitext(fname)[0]
                is_active = (stem.lower() == self.current_scenario_name.lower())
                prefix = "● " if is_active else "   "
                full_path = os.path.join(target_dir, fname)
                menu.add_command(
                    label=f"{prefix}{stem}",
                    command=lambda p=full_path, s=stem: self._load_specific_scenario(p, s)
                )

        # List subdirectories as organized submenus (e.g. test_cases)
        try:
            subdirs = [
                d for d in sorted(os.listdir(target_dir))
                if os.path.isdir(os.path.join(target_dir, d)) and not d.startswith(".")
            ]
            for sname in subdirs:
                subpath = os.path.join(target_dir, sname)
                sub_files = [f for f in sorted(os.listdir(subpath)) if f.lower().endswith(".json")]
                if sub_files:
                    submenu = tk.Menu(
                        menu,
                        tearoff=0,
                        bg="#0b131c",
                        fg="#e8eef3",
                        activebackground="#1e293b",
                        activeforeground="#38bdf8",
                        relief="solid",
                        bd=1,
                        font=(FONT_MAIN, 10)
                    )
                    for sfname in sub_files:
                        s_stem = os.path.splitext(sfname)[0]
                        s_active = (s_stem.lower() == self.current_scenario_name.lower())
                        s_prefix = "● " if s_active else "   "
                        s_full_path = os.path.join(subpath, sfname)
                        submenu.add_command(
                            label=f"{s_prefix}{s_stem}",
                            command=lambda p=s_full_path, s=s_stem: self._load_specific_scenario(p, s)
                        )
                    label_display = f"🧪 {sname.replace('_', ' ').title()}"
                    menu.add_cascade(label=label_display, menu=submenu)
        except Exception:
            pass

        if not json_files and not subdirs:
            menu.add_command(label="  (Sin archivos en saved_versions/)", state="disabled")

        menu.add_separator()
        disp_current = self.current_scenario_name if len(self.current_scenario_name) <= 15 else f"{self.current_scenario_name[:12]}..."
        menu.add_command(
            label=f"💾 Guardar versión actual ({disp_current})",
            command=self._on_save_current_version
        )
        menu.add_command(
            label="💾 Guardar como nueva versión...",
            command=self._on_save_json
        )
        menu.add_command(
            label="📂 Cargar otra versión (examinar archivo)...",
            command=self._on_load_json
        )

        try:
            x = self.version_pill.winfo_rootx()
            y = self.version_pill.winfo_rooty() + self.version_pill.winfo_height() + 4
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _on_save_current_version(self):
        """Directly overwrites and saves the current scenario/version."""
        if not self.observatory:
            return

        target_dir = getattr(self.observatory, "VERSIONS_DIR", None)
        if not target_dir:
            target_dir = os.path.abspath("saved_versions")
        os.makedirs(target_dir, exist_ok=True)

        filepath = self.current_scenario_filepath
        if not filepath:
            filepath = os.path.join(target_dir, f"{self.current_scenario_name}.json")

        try:
            self.observatory.save_scenario(filepath)
            self.current_scenario_filepath = os.path.abspath(filepath)
            name = os.path.splitext(os.path.basename(filepath))[0]
            self.set_scenario_name(name)
            if self.app and hasattr(self.app, 'capture_saved_state'):
                self.app.capture_saved_state()
            messagebox.showinfo(
                "Versión Guardada",
                f"Se sobrescribió con éxito la versión actual:\n'{name}'\n({os.path.basename(filepath)})"
            )
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"No se pudo guardar la versión actual:\n{e}")

    def _load_specific_scenario(self, filepath: str, name: str = None):
        """Loads a specific JSON scenario file and updates the application."""
        if not self.observatory or not self.app:
            return
        if not name:
            name = os.path.splitext(os.path.basename(filepath))[0]
        try:
            # 1. Attempt canonical atomic load by topology
            ok, errors = self.observatory.load_scenario_by_topology(filepath)
            if ok:
                self.current_scenario_filepath = os.path.abspath(filepath)
                self.set_scenario_name(name)
                if self.app and hasattr(self.app, 'capture_saved_state'):
                    self.app.capture_saved_state()
                messagebox.showinfo(
                    "Éxito",
                    f"Escenario '{name}' cargado exitosamente desde:\n{os.path.basename(filepath)}"
                )
                self.app.refresh_all()
            else:
                # 2. Fallback to insertions if the JSON contains a flat list of events
                try:
                    res = self.observatory.load_scenario_by_insertions(filepath, adopt_avl=True)
                    if res and "avl" in res:
                        self.current_scenario_filepath = os.path.abspath(filepath)
                        self.set_scenario_name(name)
                        if self.app and hasattr(self.app, 'capture_saved_state'):
                            self.app.capture_saved_state()
                        messagebox.showinfo(
                            "Éxito",
                            f"Escenario de eventos '{name}' cargado exitosamente desde:\n{os.path.basename(filepath)}"
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

    def _on_save_json(self):
        if not self.observatory:
            return
        target_dir = getattr(self.observatory, "VERSIONS_DIR", None)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
            target_dir = os.path.abspath(target_dir)

        filepath = filedialog.asksaveasfilename(
            title="Guardar Nueva Versión",
            initialdir=target_dir,
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        if filepath:
            try:
                self.observatory.save_scenario(filepath)
                self.current_scenario_filepath = os.path.abspath(filepath)
                name = os.path.splitext(os.path.basename(filepath))[0]
                self.set_scenario_name(name)
                if self.app and hasattr(self.app, 'capture_saved_state'):
                    self.app.capture_saved_state()
                messagebox.showinfo("Éxito", f"Versión guardada con éxito en:\n{filepath}")
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
            title="Cargar Versión desde Archivo",
            initialdir=target_dir,
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        if filepath:
            self._load_specific_scenario(filepath)
