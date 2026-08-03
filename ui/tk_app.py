import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import ctypes
import os

import matplotlib
matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from motion.core.segment import MotionSegment
from motion.core.cam_motion import compute_cam_motion
from motion.ibl_export import export_to_ibl, export_all_data

from ui.segment_editor import SegmentEditor
from ui.motion_list import MotionList

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # If not bundled, use the directory of the main script (root)
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MotionApp(tk.Tk):

    def __init__(self):
        super().__init__()

        # Fix taskbar icon on Windows
        if os.name == 'nt':
            myappid = 'marchesini.motionapp.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        self.title("Progettazione Camme")
        try:
            self.iconbitmap(resource_path("Motion_app_logo.ico"))
        except Exception:
            pass
        self.geometry("1400x900")

        self.project = None
        self.node_map = {}

        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self._show_homepage()

    # ============================
    # HOMEPAGE & NAVIGATION
    # ============================
    def _show_homepage(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        self.project = None
        self._build_menu(full=False)

        frame = ttk.Frame(self.main_container)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        ttk.Button(frame, text="Nuovo Progetto", width=25, command=self.new_project).pack(pady=10)
        ttk.Button(frame, text="Apri...", width=25, command=lambda: None).pack(pady=10)

    def _build_menu(self, full=True):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nuovo Progetto", command=self.new_project)
        file_menu.add_command(label="Apri...", command=lambda: None)
        if full:
            file_menu.add_command(label="Salva", command=lambda: None)
            file_menu.add_command(label="Salva con nome...", command=lambda: None)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        if full:
            menubar.add_cascade(label="Modifica", menu=tk.Menu(menubar, tearoff=0))

            prof_menu = tk.Menu(menubar, tearoff=0)
            prof_menu.add_command(label="Nuovo profilo", command=self.add_profile)
            prof_menu.add_command(label="Elimina profilo", command=self.remove_profile)
            menubar.add_cascade(label="Profili di moto", menu=prof_menu)

            laws_menu = tk.Menu(menubar, tearoff=0)
            new_law_menu = tk.Menu(laws_menu, tearoff=0)
            new_law_menu.add_command(label="Trapezoidale", command=lambda: self.add_law("trapezoidal", "Trapezoidale"))
            new_law_menu.add_command(label="Trapezoidale generalizzata", command=lambda: self.add_law("trap_gen", "Trapezoidale generalizzata"))
            new_law_menu.add_command(label="Sosta", command=lambda: self.add_law("dwell", "Sosta"))
            new_law_menu.add_command(label="Cicloidale", command=lambda: self.add_law("cycloidal", "Cicloidale"))
            new_law_menu.add_command(label="Polinomiale 3-4-5", command=lambda: self.add_law("poly_345", "Polinomiale 3-4-5"))
            laws_menu.add_cascade(label="Nuova legge di moto", menu=new_law_menu)
            laws_menu.add_command(label="Elimina legge", command=self.remove_law)
            menubar.add_cascade(label="Leggi di moto", menu=laws_menu)

            tools_menu = tk.Menu(menubar, tearoff=0)
            tools_menu.add_command(label="Nuovo marker", command=self.add_marker)
            export_menu = tk.Menu(tools_menu, tearoff=0)
            export_menu.add_command(label="Spostamento", command=lambda: export_to_ibl(self.project, "displacement"))
            export_menu.add_command(label="Velocità", command=lambda: export_to_ibl(self.project, "speed"))
            export_menu.add_command(label="Accelerazione", command=lambda: export_to_ibl(self.project, "acceleration"))
            export_menu.add_command(label="Jerk", command=lambda: export_to_ibl(self.project, "jerk"))
            tools_menu.add_cascade(label="Esporta IBL", menu=export_menu)
            tools_menu.add_command(label="Esporta CSV", command=lambda: export_all_data(self.project, "csv"))
            tools_menu.add_command(label="Esporta TXT", command=lambda: export_all_data(self.project, "txt"))
            menubar.add_cascade(label="Strumenti", menu=tools_menu)

            menubar.add_cascade(label="Parametrizzazione", menu=tk.Menu(menubar, tearoff=0))
            menubar.add_cascade(label="Opzioni", menu=tk.Menu(menubar, tearoff=0))

        self.config(menu=menubar)

    # ============================
    # UI LAYOUT
    # ============================
    def _build_ui(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        v_paned = ttk.PanedWindow(self.main_container, orient=tk.VERTICAL)
        v_paned.pack(fill=tk.BOTH, expand=True)

        top_paned = ttk.PanedWindow(v_paned, orient=tk.HORIZONTAL)
        v_paned.add(top_paned, weight=5)

        # ================= LEFT SIDEBAR =================
        left_frame = ttk.Frame(top_paned, width=400, padding=4)
        top_paned.add(left_frame, weight=0)

        # 1. Project Hierarchy Tree
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.project_tree = ttk.Treeview(tree_frame, show="tree")
        self.project_tree.pack(fill=tk.BOTH, expand=True)
        self.project_tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.project_tree.bind("<Double-1>", self._on_tree_double_click)
        
        # Right-click context menu
        self.project_tree.bind("<Button-3>", self._on_tree_right_click)
        # For macOS compatibility
        self.project_tree.bind("<Button-2>", self._on_tree_right_click)

        # Drag and drop bindings
        self.project_tree.bind("<ButtonPress-1>", self._on_drag_start)
        self.project_tree.bind("<B1-Motion>", self._on_drag_motion)
        self.project_tree.bind("<ButtonRelease-1>", self._on_drag_release)
        self._drag_node = None

        # 2. Contextual Editor Frame
        self.editor_container = ttk.LabelFrame(left_frame, text="Editor Profilo", padding=5)
        self.editor_container.pack(fill=tk.BOTH, expand=True)

        # ================= RIGHT PLOTS (2x2 Grid) =================
        right_frame = ttk.Frame(top_paned, padding=2)
        top_paned.add(right_frame, weight=1)

        # Container to allow overlaying buttons
        plot_container = ttk.Frame(right_frame)
        plot_container.pack(fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(8, 6))
        self.axes = self.fig.subplots(2, 2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_container)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Pan & Zoom state
        self._pan_start = None
        self._hover_annotations = {}
        
        # Bind canvas events
        self.canvas.mpl_connect("button_press_event", self._on_plot_press)
        self.canvas.mpl_connect("button_release_event", self._on_plot_release)
        self.canvas.mpl_connect("motion_notify_event", self._on_plot_motion)
        self.canvas.mpl_connect("scroll_event", self._on_plot_scroll)

        # Create 4 separate navigation overlays, one for each subplot
        self.nav_frames = []
        for i, ax in enumerate(self.axes.flat):
            frame = ttk.Frame(plot_container)
            # We will place them dynamically in self._update_nav_positions()
            self.nav_frames.append(frame)
            
            # Capture ax in closures
            def make_home(a=ax): return lambda: self._zoom_home_ax(a)
            def make_zoom(factor, a=ax): return lambda: self._zoom_button_ax(factor, a)
            
            ttk.Button(frame, text="🏠", width=3, command=make_home()).pack(side=tk.LEFT, padx=1)
            ttk.Button(frame, text="➕", width=3, command=make_zoom(0.8)).pack(side=tk.LEFT, padx=1)
            ttk.Button(frame, text="➖", width=3, command=make_zoom(1.25)).pack(side=tk.LEFT, padx=1)

        # Update button positions when canvas is resized/drawn.
        # We use "+" to append the binding so we don't overwrite Matplotlib's internal resize handler.
        self.canvas.get_tk_widget().bind("<Configure>", lambda e: self._update_nav_positions(), "+")

        # ================= BOTTOM DATA TABLE =================
        bottom_frame = ttk.Frame(v_paned, padding=2)
        v_paned.add(bottom_frame, weight=1)

        self.bottom_notebook = ttk.Notebook(bottom_frame)
        self.bottom_notebook.pack(fill=tk.BOTH, expand=True)

        tab_detail = ttk.Frame(self.bottom_notebook)
        self.bottom_notebook.add(tab_detail, text="Dettaglio input")

        table_cols = ("tipo", "cv", "ca", "fase_t", "fase_e", "salto_t", "salto_e", 
                      "v_ini_t", "v_ini_e", "v_fin_t", "v_fin_e", 
                      "a_ini_t", "a_ini_e", "a_fin_t", "a_fin_e", 
                      "j_ini_t", "j_ini_e", "j_fin_t", "j_fin_e")

        self.detail_table = ttk.Treeview(tab_detail, columns=table_cols, show="headings", height=5)
        self.detail_table.pack(fill=tk.BOTH, expand=True)

        headers = [
            ("tipo", "Tipo"), ("cv", "Cv"), ("ca", "Ca"),
            ("fase_t", "Fase Teorica"), ("fase_e", "Fase Effettiva"),
            ("salto_t", "Salto Teorico"), ("salto_e", "Salto Effettivo"),
            ("v_ini_t", "V.Ini Teorica"), ("v_ini_e", "V.Ini Effettiva"),
            ("v_fin_t", "V.Fin Teorica"), ("v_fin_e", "V.Fin Effettiva"),
            ("a_ini_t", "A.Ini Teorica"), ("a_ini_e", "A.Ini Effettiva"),
            ("a_fin_t", "A.Fin Teorica"), ("a_fin_e", "A.Fin Effettiva"),
            ("j_ini_t", "J.Ini Teorico"), ("j_ini_e", "J.Ini Effettivo"),
            ("j_fin_t", "J.Fin Teorico"), ("j_fin_e", "J.Fin Effettivo")
        ]
        for col_id, col_name in headers:
            self.detail_table.heading(col_id, text=col_name)
            self.detail_table.column(col_id, width=85, anchor="center")

        tab_maxmin = ttk.Frame(self.bottom_notebook)
        self.bottom_notebook.add(tab_maxmin, text="Max/min profilo")

        maxmin_cols = ("tipo", "s_min", "s_max", "v_min", "v_max", "a_min", "a_max", "j_min", "j_max")
        self.maxmin_table = ttk.Treeview(tab_maxmin, columns=maxmin_cols, show="headings", height=5)
        self.maxmin_table.pack(fill=tk.BOTH, expand=True)

        maxmin_headers = [
            ("tipo", "Tipo"),
            ("s_min", "Min Spostamento"), ("s_max", "Max Spostamento"),
            ("v_min", "Min Velocità"), ("v_max", "Max Velocità"),
            ("a_min", "Min Accelerazione"), ("a_max", "Max Accelerazione"),
            ("j_min", "Min Jerk"), ("j_max", "Max Jerk")
        ]
        for col_id, col_name in maxmin_headers:
            self.maxmin_table.heading(col_id, text=col_name)
            self.maxmin_table.column(col_id, width=100, anchor="center")

    # ============================
    # TREE MANAGEMENT
    # ============================
    def _populate_tree(self):
        self.project_tree.delete(*self.project_tree.get_children())
        self.node_map.clear()

        # Root node
        root_id = self.project_tree.insert("", "end", text=self.project["title"], open=True)
        self.node_map[root_id] = ("project", None)

        # Profiles
        for p_idx, profile in enumerate(self.project["profiles"]):
            p_text = f"☑ {profile['name']}" if profile['visible'] else f"☐ {profile['name']}"
            p_node = self.project_tree.insert(root_id, "end", text=p_text, open=True)
            self.node_map[p_node] = ("profile", p_idx)

            for l_idx, law in enumerate(profile["laws"]):
                l_node = self.project_tree.insert(p_node, "end", text=law["name"])
                self.node_map[l_node] = ("law", (p_idx, l_idx))

        # Markers
        m_root = self.project_tree.insert(root_id, "end", text="Markers", open=True)
        self.node_map[m_root] = ("markers_group", None)

        for m_idx, marker in enumerate(self.project["markers"]):
            m_text = f"☑ {marker['label']}" if marker['visible'] else f"☐ {marker['label']}"
            m_node = self.project_tree.insert(m_root, "end", text=m_text)
            self.node_map[m_node] = ("marker", m_idx)

    def _toggle_profile_visibility(self, p_idx):
        self.project["profiles"][p_idx]["visible"] = not self.project["profiles"][p_idx]["visible"]
        self._populate_tree()
        self.calculate()

    def _toggle_marker_visibility(self, m_idx):
        self.project["markers"][m_idx]["visible"] = not self.project["markers"][m_idx]["visible"]
        self._populate_tree()
        self.calculate()

    def _on_tree_select(self, event):
        selected = self.project_tree.selection()
        if not selected:
            return
        node_id = selected[0]
        if node_id not in self.node_map:
            return

        node_type, data = self.node_map[node_id]

        if node_type in ("project", "profile"):
            p_idx = data if node_type == "profile" else 0
            self._show_profile_editor(p_idx)
        elif node_type == "law":
            p_idx, l_idx = data
            self._show_law_editor(p_idx, l_idx)
        elif node_type == "marker":
            m_idx = data
            self._show_marker_editor(m_idx)

        self.calculate()

    def _on_tree_right_click(self, event):
        iid = self.project_tree.identify_row(event.y)
        if not iid:
            return
        self.project_tree.selection_set(iid)
        node_type, data = self.node_map.get(iid, (None, None))

        menu = tk.Menu(self, tearoff=0)
        if node_type == "profile":
            label = "Nascondi Profilo" if self.project["profiles"][data]["visible"] else "Mostra Profilo"
            menu.add_command(label=label, command=lambda: self._toggle_profile_visibility(data))
            menu.add_command(label="Cambia colore...", command=lambda: self._choose_profile_color(data))
            menu.add_separator()
            menu.add_command(label="Elimina Profilo", command=lambda: self._delete_profile_by_idx(data))
        elif node_type == "law":
            p_idx, l_idx = data
            menu.add_command(label="Elimina Legge", command=lambda: self._delete_law_by_idx(p_idx, l_idx))
        elif node_type == "marker":
            label = "Nascondi Marker" if self.project["markers"][data]["visible"] else "Mostra Marker"
            menu.add_command(label=label, command=lambda: self._toggle_marker_visibility(data))
            menu.add_command(label="Cambia colore...", command=lambda: self._choose_marker_color(data))
            menu.add_separator()
            menu.add_command(label="Elimina Marker", command=lambda: self._delete_marker_by_idx(data))
        else:
            return

        menu.post(event.x_root, event.y_root)

    def _choose_marker_color(self, m_idx):
        marker = self.project["markers"][m_idx]
        current_color = marker.get("color", "#FF0000")

        dialog = tk.Toplevel(self)
        dialog.title("Scegli Colore Marker")
        dialog.geometry("320x300")
        dialog.transient(self)
        dialog.grab_set()

        colors = [
            "#FF0000", "#FF4500", "#FFA500", "#FFD700", "#FFFF00",
            "#9ACD32", "#32CD32", "#008000", "#00FA9A", "#00FFFF",
            "#1E90FF", "#0000FF", "#8A2BE2", "#4B0082", "#9932CC",
            "#FF00FF", "#FF1493", "#A52A2A", "#808080", "#000000"
        ]

        lbl_frame = ttk.LabelFrame(dialog, text="Tavolozza colori", padding=10)
        lbl_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        selected_hex = tk.StringVar(value=current_color)

        def set_color(hex_val):
            selected_hex.set(hex_val)

        for idx, hex_val in enumerate(colors):
            r = idx // 5
            c = idx % 5
            btn = tk.Button(lbl_frame, bg=hex_val, activebackground=hex_val, width=4, height=1,
                            command=lambda h=hex_val: set_color(h))
            btn.grid(row=r, column=c, padx=3, pady=3)

        hex_frame = ttk.Frame(dialog, padding=10)
        hex_frame.pack(fill=tk.X, padx=10)

        ttk.Label(hex_frame, text="Codice HEX:").pack(side=tk.LEFT, padx=(0, 5))
        e_hex = ttk.Entry(hex_frame, textvariable=selected_hex, width=12)
        e_hex.pack(side=tk.LEFT)

        def on_confirm():
            color = selected_hex.get().strip()
            if color:
                marker["color"] = color
                self.calculate()
            dialog.destroy()

        btn_frame = ttk.Frame(dialog, padding=5)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="OK", command=on_confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.RIGHT)

    def _choose_profile_color(self, p_idx):
        profile = self.project["profiles"][p_idx]
        current_color = profile.get("color", "#FFA500")

        dialog = tk.Toplevel(self)
        dialog.title("Scegli Colore Profilo")
        dialog.geometry("320x300")
        dialog.transient(self)
        dialog.grab_set()

        colors = [
            "#FF0000", "#FF4500", "#FFA500", "#FFD700", "#FFFF00",
            "#9ACD32", "#32CD32", "#008000", "#00FA9A", "#00FFFF",
            "#1E90FF", "#0000FF", "#8A2BE2", "#4B0082", "#9932CC",
            "#FF00FF", "#FF1493", "#A52A2A", "#808080", "#000000"
        ]

        lbl_frame = ttk.LabelFrame(dialog, text="Tavolozza colori", padding=10)
        lbl_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        selected_hex = tk.StringVar(value=current_color)

        def set_color(hex_val):
            selected_hex.set(hex_val)

        for idx, hex_val in enumerate(colors):
            r = idx // 5
            c = idx % 5
            btn = tk.Button(lbl_frame, bg=hex_val, activebackground=hex_val, width=4, height=1,
                            command=lambda h=hex_val: set_color(h))
            btn.grid(row=r, column=c, padx=3, pady=3)

        hex_frame = ttk.Frame(dialog, padding=10)
        hex_frame.pack(fill=tk.X, padx=10)

        ttk.Label(hex_frame, text="Codice HEX:").pack(side=tk.LEFT, padx=(0, 5))
        e_hex = ttk.Entry(hex_frame, textvariable=selected_hex, width=12)
        e_hex.pack(side=tk.LEFT)

        def on_confirm():
            color = selected_hex.get().strip()
            if color:
                profile["color"] = color
                self.calculate()
            dialog.destroy()

        btn_frame = ttk.Frame(dialog, padding=5)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="OK", command=on_confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.RIGHT)

    def _delete_profile_by_idx(self, p_idx):
        if messagebox.askyesno("Conferma", "Vuoi davvero eliminare questo profilo?"):
            del self.project["profiles"][p_idx]
            self._populate_tree()
            self.calculate()

    def _delete_law_by_idx(self, p_idx, l_idx):
        if messagebox.askyesno("Conferma", "Vuoi davvero eliminare questa legge?"):
            del self.project["profiles"][p_idx]["laws"][l_idx]
            self._populate_tree()
            self.calculate()

    def _delete_marker_by_idx(self, m_idx):
        if messagebox.askyesno("Conferma", "Vuoi davvero eliminare questo marker?"):
            del self.project["markers"][m_idx]
            self._populate_tree()
            self.calculate()

    def _on_drag_start(self, event):
        iid = self.project_tree.identify_row(event.y)
        if iid:
            node_type, data = self.node_map.get(iid, (None, None))
            if node_type in ("profile", "law", "marker"):
                self._drag_node = iid

    def _on_drag_motion(self, event):
        pass

    def _on_drag_release(self, event):
        if not self._drag_node:
            return
        
        target_iid = self.project_tree.identify_row(event.y)
        if not target_iid or target_iid == self._drag_node:
            self._drag_node = None
            return

        src_type, src_data = self.node_map.get(self._drag_node, (None, None))
        tgt_type, tgt_data = self.node_map.get(target_iid, (None, None))

        if src_type == "profile" and tgt_type == "profile":
            # Reorder profiles
            profiles = self.project["profiles"]
            val = profiles.pop(src_data)
            profiles.insert(tgt_data, val)
            self._populate_tree()
            self.calculate()
        elif src_type == "law" and tgt_type == "law":
            src_p, src_l = src_data
            tgt_p, tgt_l = tgt_data
            if src_p == tgt_p: # Only allow reordering within the same profile
                laws = self.project["profiles"][src_p]["laws"]
                val = laws.pop(src_l)
                laws.insert(tgt_l, val)
                self._populate_tree()
                self.calculate()
        elif src_type == "marker" and tgt_type == "marker":
            # Reorder markers
            markers = self.project["markers"]
            val = markers.pop(src_data)
            markers.insert(tgt_data, val)
            self._populate_tree()
            self.calculate()

        self._drag_node = None

    def _on_tree_double_click(self, event):
        selected = self.project_tree.selection()
        if not selected:
            return
        node_id = selected[0]
        node_type, data = self.node_map.get(node_id, (None, None))

        if node_type == "profile":
            p_idx = data
            curr_name = self.project["profiles"][p_idx]["name"]
            new_name = tk.simpledialog.askstring("Rinomina Profilo", "Inserisci nuovo nome:", initialvalue=curr_name)
            if new_name:
                self.project["profiles"][p_idx]["name"] = new_name
                self._populate_tree()

    # ============================
    # EDITORS
    # ============================
    def _clear_editor(self):
        for widget in self.editor_container.winfo_children():
            widget.destroy()

    def _show_profile_editor(self, p_idx):
        self._clear_editor()
        self.editor_container.config(text="Editor Profilo")
        profile = self.project["profiles"][p_idx]

        nb = ttk.Notebook(self.editor_container)
        nb.pack(fill=tk.BOTH, expand=True)

        tab_gen = ttk.Frame(nb, padding=5)
        nb.add(tab_gen, text="Input generici")
        nb.add(ttk.Frame(nb), text="Visualizzazione")
        nb.add(ttk.Frame(nb), text="Avanzate")

        fields = [
            ("Nome", "name", str, ""),
            ("Punti per ciclo", "points_per_cycle", int, ""),
            ("Posizione iniziale", "start_pos", float, f" {profile.get('unit_y', 'mm')}"),
            ("Sfasamento iniziale", "start_phase", float, f" {profile.get('unit_x', 's')}"),
            ("Modulo ciclo", "cycle_mod", str, ""),
            ("Unità (asse x)", "unit_x", str, ""),
            ("Velocità ciclo", "cycle_vel", float, " rpm"),
            ("Durata ciclo", "cycle_duration", float, f" {profile.get('unit_x', 's')}"),
            ("Unità (asse y)", "unit_y", str, ""),
        ]

        unit_x = profile.get("unit_x", "s")
        key_dur = "duration" if unit_x == "s" else "phase"
        laws_sum = sum(l.get(key_dur, 0.0) for l in profile.get("laws", []))
        cycle_dur = profile.get("cycle_duration", 1.0)
        can_enable_mod = abs(laws_sum - cycle_dur) < 1e-5

        if not can_enable_mod:
            profile["cycle_mod"] = "No"

        for i, (label_text, key, val_type, unit) in enumerate(fields):
            ttk.Label(tab_gen, text=label_text).grid(row=i, column=0, sticky="w", pady=2)
            if key == "cycle_mod":
                combobox_state = "readonly" if can_enable_mod else "disabled"
                widget = ttk.Combobox(tab_gen, values=["No", "Sì"], width=12, state=combobox_state)
                raw_val = profile.get(key, "No")
                if raw_val not in ("No", "Sì"):
                    raw_val = "No"
                widget.set(raw_val)
                widget.grid(row=i, column=1, sticky="e", pady=2)

                def make_cycle_mod_updater(w, p):
                    def on_combobox_selected(event):
                        p["cycle_mod"] = w.get()
                        self.calculate()
                    return on_combobox_selected
                widget.bind("<<ComboboxSelected>>", make_cycle_mod_updater(widget, profile))
            elif key == "unit_x":
                widget = ttk.Combobox(tab_gen, values=["°", "s"], width=12, state="readonly")
                raw_val = profile.get(key, "s")
                widget.set(raw_val)
                widget.grid(row=i, column=1, sticky="e", pady=2)

                def make_unit_x_updater(w, p):
                    def on_combobox_selected(event):
                        val = w.get()
                        p["unit_x"] = val
                        if val == "°":
                            p["cycle_duration"] = 360.0
                        else:
                            p["cycle_duration"] = 18.0
                        self._show_profile_editor(p_idx)
                        self.calculate()
                    return on_combobox_selected
                widget.bind("<<ComboboxSelected>>", make_unit_x_updater(widget, profile))
            elif key == "unit_y":
                widget = ttk.Combobox(tab_gen, values=["mm", "cm", "m"], width=12, state="readonly")
                raw_val = profile.get(key, "mm")
                widget.set(raw_val)
                widget.grid(row=i, column=1, sticky="e", pady=2)

                def make_unit_y_updater(w, p):
                    def on_combobox_selected(event):
                        p["unit_y"] = w.get()
                        self._show_profile_editor(p_idx)
                        self.calculate()
                    return on_combobox_selected
                widget.bind("<<ComboboxSelected>>", make_unit_y_updater(widget, profile))
            else:
                entry = ttk.Entry(tab_gen, width=12)
                raw_val = profile.get(key, "")
                entry.insert(0, str(raw_val))
                entry.grid(row=i, column=1, sticky="e", pady=2)
                clean_unit = unit.strip()
                if clean_unit:
                    ttk.Label(tab_gen, text=clean_unit).grid(row=i, column=2, sticky="w", padx=2, pady=2)

                def make_profile_updater(k, t, ent):
                    def updater(event):
                        val_str = ent.get()
                        try:
                            profile[k] = t(val_str.strip())
                            if k == "name":
                                self._populate_tree()
                            self.calculate()
                        except ValueError:
                            pass
                    return updater

                entry.bind("<KeyRelease>", make_profile_updater(key, val_type, entry))

    def _show_law_editor(self, p_idx, l_idx):
        self._clear_editor()
        self.editor_container.config(text="Editor Legge")
        profile = self.project["profiles"][p_idx]
        law = profile["laws"][l_idx]

        nb = ttk.Notebook(self.editor_container)
        nb.pack(fill=tk.BOTH, expand=True)

        tab_gen = ttk.Frame(nb, padding=5)
        nb.add(tab_gen, text="Input generici")
        
        tab_spec = ttk.Frame(nb, padding=5)
        nb.add(tab_spec, text="Input specifici")
        
        tab_out = ttk.Frame(nb, padding=5)
        nb.add(tab_out, text="Output")

        unit_x = profile.get("unit_x", "s")
        if law["type"] == "dwell":
            nb.tab(tab_spec, state="disabled")
            fields = [
                ("Fase", "phase", float, " °"),
                ("Durata", "duration", float, f" {unit_x}"),
            ]
        else:
            fields = [
                ("Fase", "phase", float, " °"),
                ("Durata", "duration", float, f" {unit_x}"),
                ("Salto", "stroke", float, " mm"),
                ("Velocità iniziale", "v_ini", float, " mm/s"),
                ("Accelerazione iniziale", "a_ini", float, " mm/s²"),
                ("Velocità finale", "v_fin", float, " mm/s"),
                ("Accelerazione finale", "a_fin", float, " mm/s²"),
                ("Parz. iniziale", "parz_ini", float, " s"),
                ("Parz. finale", "parz_fin", float, " s"),
            ]

            # Populate specific inputs for trapezoidale generalizzata
            if law["type"] == "trap_gen":
                prop_defaults = [10, 20, 10, 0, 10, 20, 10]
                if "proportions" not in law:
                    law["proportions"] = prop_defaults
                
                for i, val in enumerate(law["proportions"]):
                    ttk.Label(tab_spec, text=f"Sezione {i+1}").grid(row=i, column=0, sticky="w", pady=2)
                    entry = ttk.Entry(tab_spec, width=12)
                    entry.insert(0, str(val))
                    entry.grid(row=i, column=1, sticky="e", pady=2)
                    
                    # Bind changes to update the law proportions
                    def make_updater(idx, ent):
                        return lambda event: self._update_law_proportion(p_idx, l_idx, idx, ent.get())
                    entry.bind("<KeyRelease>", make_updater(i, entry))

        for i, (label_text, key, val_type, unit) in enumerate(fields):
            ttk.Label(tab_gen, text=label_text).grid(row=i, column=0, sticky="w", pady=2)
            entry = ttk.Entry(tab_gen, width=12)
            raw_val = law.get(key, "")
            entry.insert(0, str(raw_val))
            entry.grid(row=i, column=1, sticky="e", pady=2)
            
            if unit_x == "s" and key == "phase":
                entry.config(state="disabled")
            elif unit_x == "°" and key == "duration":
                entry.config(state="disabled")

            clean_unit = unit.strip()
            if clean_unit:
                ttk.Label(tab_gen, text=clean_unit).grid(row=i, column=2, sticky="w", padx=2, pady=2)

            def make_law_updater(k, t, ent):
                def updater(event):
                    val_str = ent.get()
                    try:
                        law[k] = t(val_str.strip())
                        self.calculate()
                    except ValueError:
                        pass
                return updater

            entry.bind("<KeyRelease>", make_law_updater(key, val_type, entry))

    def _update_law_proportion(self, p_idx, l_idx, prop_idx, val_str):
        try:
            val = float(val_str)
            self.project["profiles"][p_idx]["laws"][l_idx]["proportions"][prop_idx] = val
            self.calculate()
        except ValueError:
            pass

    def _show_marker_editor(self, m_idx):
        self._clear_editor()
        self.editor_container.config(text="Editor Marker")
        marker = self.project["markers"][m_idx]
        unit_x = self.project["profiles"][0]["unit_x"] if self.project["profiles"] else "s"

        frame = ttk.Frame(self.editor_container, padding=5)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="x").grid(row=0, column=0, sticky="w", pady=5)
        e_x = ttk.Entry(frame, width=10)
        e_x.insert(0, f"{marker['value']}")
        e_x.grid(row=0, column=1, sticky="w", pady=5)
        ttk.Label(frame, text=unit_x).grid(row=0, column=2, sticky="w", padx=2, pady=5)

        ttk.Label(frame, text="Etichetta").grid(row=1, column=0, sticky="w", pady=5)
        e_lbl = ttk.Entry(frame, width=15)
        e_lbl.insert(0, marker["label"])
        e_lbl.grid(row=1, column=1, sticky="w", pady=5)

        def on_x_change(event):
            try:
                val = float(e_x.get())
                marker["value"] = val
                if not marker.get("custom_label", False):
                    marker["label"] = f"x = {val}{unit_x}"
                    e_lbl.delete(0, tk.END)
                    e_lbl.insert(0, marker["label"])
                self._populate_tree()
                self.calculate()
            except ValueError:
                pass

        def on_label_change(event):
            marker["label"] = e_lbl.get()
            marker["custom_label"] = True
            self._populate_tree()
            self.calculate()

        e_x.bind("<KeyRelease>", on_x_change)
        e_lbl.bind("<KeyRelease>", on_label_change)

    # ============================
    # PROJECT & MENU ACTIONS
    # ============================
    def new_project(self):
        dialog = tk.Toplevel(self)
        dialog.title("Nuovo Progetto")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Nome Progetto:").pack(pady=(10, 0))
        e_name = ttk.Entry(dialog)
        e_name.insert(0, "Nuovo Progetto")
        e_name.pack(pady=5, padx=10, fill=tk.X)

        show_example = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="mostra leggi di moto di esempio", variable=show_example).pack(pady=5)

        def on_ok():
            name = e_name.get()
            if not name:
                messagebox.showerror("Errore", "Inserisci un nome per il progetto")
                return

            if show_example.get():
                self.project = {
                    "title": name,
                    "profiles": [
                        {
                            "name": "Nuovo Profilo",
                            "visible": True,
                            "points_per_cycle": 1440,
                            "start_pos": 600.0,
                            "start_phase": 0.0,
                            "cycle_mod": "No",
                            "unit_x": "s",
                            "cycle_vel": 3.33333333,
                            "cycle_duration": 18.0,
                            "unit_y": "mm",
                            "laws": [
                                {
                                    "type": "trap_gen",
                                    "name": "Trapezoidale generalizzata",
                                    "phase": 40.0,
                                    "duration": 2.0,
                                    "stroke": -60.0,
                                    "v_ini": 0.0, "a_ini": 0.0, "v_fin": 0.0, "a_fin": 0.0,
                                    "parz_ini": 0.0, "parz_fin": 0.25,
                                    "proportions": [10, 20, 10, 0, 10, 20, 10]
                                },
                                {
                                    "type": "dwell",
                                    "name": "Sosta",
                                    "phase": 10.0, "duration": 0.5, "stroke": 0.0,
                                    "v_ini": 0.0, "a_ini": 0.0, "v_fin": 0.0, "a_fin": 0.0,
                                    "parz_ini": 0.0, "parz_fin": 0.0
                                }
                            ]
                        }
                    ],
                    "markers": [{"value": 6.25, "visible": True, "label": "x = 6.25°"}]
                }
            else:
                self.project = {
                    "title": name,
                    "profiles": [],
                    "markers": []
                }

            dialog.destroy()
            self.title(f"Progettazione Camme - {name}")
            self._build_menu(full=True)
            self._build_ui()
            self._populate_tree()
            self.calculate()

        ttk.Button(dialog, text="OK", command=on_ok).pack(pady=10)

    def add_profile(self):
        new_p = {
            "name": f"Profilo {len(self.project['profiles'])+1}",
            "visible": True,
            "points_per_cycle": 1440,
            "start_pos": 600.0,
            "start_phase": 0.0,
            "cycle_mod": "No",
            "unit_x": "s",
            "cycle_vel": 3.33333333,
            "cycle_duration": 18.0,
            "unit_y": "mm",
            "laws": []
        }
        self.project["profiles"].append(new_p)
        self._populate_tree()

    def remove_profile(self):
        selected = self.project_tree.selection()
        if not selected:
            return
        node_type, data = self.node_map.get(selected[0], (None, None))
        if node_type == "profile":
            del self.project["profiles"][data]
            self._populate_tree()
            self.calculate()

    def add_law(self, law_type, law_name):
        selected = self.project_tree.selection()
        p_idx = 0
        if selected:
            node_type, data = self.node_map.get(selected[0], (None, None))
            if node_type == "profile":
                p_idx = data
            elif node_type == "law":
                p_idx = data[0]

        if not self.project["profiles"]:
            self.add_profile()
            p_idx = 0

        law = {
            "type": law_type,
            "name": law_name,
            "phase": 40.0 if law_type != "dwell" else 10.0,
            "duration": 2.0 if law_type != "dwell" else 0.5,
            "stroke": -60.0 if law_type != "dwell" else 0.0,
            "v_ini": 0.0,
            "a_ini": 0.0,
            "v_fin": 0.0,
            "a_fin": 0.0,
            "parz_ini": 0.0,
            "parz_fin": 0.0 if law_type != "trap_gen" else 0.25,
            "proportions": [10, 20, 10, 0, 10, 20, 10] if law_type == "trap_gen" else []
        }
        self.project["profiles"][p_idx]["laws"].append(law)
        self._populate_tree()
        self.calculate()

    def remove_law(self):
        selected = self.project_tree.selection()
        if not selected:
            return
        node_type, data = self.node_map.get(selected[0], (None, None))
        if node_type == "law":
            p_idx, l_idx = data
            del self.project["profiles"][p_idx]["laws"][l_idx]
            self._populate_tree()
            self.calculate()

    def add_marker(self):
        val_str = tk.simpledialog.askstring("Nuovo Marker", "Inserisci il valore x del marker:")
        if val_str is None:
            return
        try:
            val = float(val_str)
        except ValueError:
            messagebox.showerror("Errore", "Inserisci un valore numerico valido.")
            return

        unit_x = self.project["profiles"][0]["unit_x"] if self.project["profiles"] else "s"
        marker = {
            "value": val,
            "visible": True,
            "label": f"x = {val}{unit_x}",
            "custom_label": False
        }
        self.project["markers"].append(marker)
        self._populate_tree()
        self.calculate()


    # ============================
    # PLOT NAVIGATION & HOVER
    # ============================
    def _update_nav_positions(self):
        self.fig.tight_layout()
        # Position each navigation frame at the top-right of its corresponding subplot
        for ax, frame in zip(self.axes.flat, self.nav_frames):
            bbox = ax.get_position()
            # bbox coordinates are in figure fraction: [x0, y0, x1, y1]
            # Tkinter place uses relx, rely from top-left
            relx = bbox.x1
            rely = 1.0 - bbox.y1
            frame.place(relx=relx, rely=rely, anchor="ne", x=-5, y=5)

    def _zoom_home_ax(self, ax):
        xlim_right = 1.0
        for profile in self.project["profiles"]:
            if profile["visible"]:
                xlim_right = profile.get("cycle_duration", 1.0)
                break
        ax.set_xlim(0, xlim_right)

        # Manually calculate y-limits for all lines on this axis within the x-range
        y_min, y_max = None, None
        for line in ax.get_lines():
            xdata = np.asarray(line.get_xdata())
            ydata = np.asarray(line.get_ydata())
            if xdata is None or ydata is None or len(ydata) == 0:
                continue
            mask = (xdata >= 0) & (xdata <= xlim_right)
            y_visible = ydata[mask] if np.any(mask) else ydata
            if len(y_visible) > 0:
                ymin, ymax = np.min(y_visible), np.max(y_visible)
                y_min = ymin if y_min is None else min(y_min, ymin)
                y_max = ymax if y_max is None else max(y_max, ymax)

        if y_min is not None and y_max is not None:
            dy = y_max - y_min
            if dy == 0:
                dy = 1.0
            ax.set_ylim(y_min - 0.05 * dy, y_max + 0.05 * dy)
        else:
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)

        self.canvas.draw()
        self._update_nav_positions()

    def _zoom_button_ax(self, factor, ax):
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_mid = sum(xlim) / 2
        y_mid = sum(ylim) / 2
        dx = (xlim[1] - xlim[0]) * factor / 2
        dy = (ylim[1] - ylim[0]) * factor / 2
        ax.set_xlim(x_mid - dx, x_mid + dx)
        ax.set_ylim(y_mid - dy, y_mid + dy)
        self.canvas.draw()
        self._update_nav_positions()

    def _on_plot_press(self, event):
        if event.button == 1 and event.inaxes:
            self._pan_start = (event.xdata, event.ydata, event.inaxes)

    def _on_plot_release(self, event):
        self._pan_start = None

    def _on_plot_scroll(self, event):
        if not event.inaxes:
            return
        ax = event.inaxes
        factor = 0.8 if event.button == 'up' else 1.25
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        xdata = event.xdata if event.xdata is not None else sum(xlim)/2
        ydata = event.ydata if event.ydata is not None else sum(ylim)/2
        ax.set_xlim(xdata - (xdata - xlim[0]) * factor, xdata + (xlim[1] - xdata) * factor)
        ax.set_ylim(ydata - (ydata - ylim[0]) * factor, ydata + (ylim[1] - ydata) * factor)
        self.canvas.draw()
        self._update_nav_positions()

    def _on_plot_motion(self, event):
        # Handle Panning
        if self._pan_start is not None and event.inaxes == self._pan_start[2]:
            ax = event.inaxes
            dx = event.xdata - self._pan_start[0]
            dy = event.ydata - self._pan_start[1]
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
            ax.set_ylim(ylim[0] - dy, ylim[1] - dy)
            self.canvas.draw()
            self._update_nav_positions()
            return

        # Handle Hover Tooltips
        for ax in self.axes.flat:
            if ax in self._hover_annotations:
                self._hover_annotations[ax].set_visible(False)

        if event.inaxes:
            ax = event.inaxes
            # Find closest point on any line in this axis
            closest_point = None
            min_dist = float('inf')
            for line in ax.get_lines():
                xdata = line.get_xdata()
                ydata = line.get_ydata()
                if xdata is None or len(xdata) == 0:
                    continue
                # Find index of closest x
                idx = np.abs(xdata - event.xdata).argmin()
                dist = np.hypot(xdata[idx] - event.xdata, ydata[idx] - event.ydata)
                if dist < min_dist:
                    min_dist = dist
                    closest_point = (xdata[idx], ydata[idx])

            if closest_point is not None:
                if ax not in self._hover_annotations:
                    self._hover_annotations[ax] = ax.annotate(
                        "", xy=(0, 0), xytext=(10, 10),
                        textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="yellow", alpha=0.8),
                        arrowprops=dict(arrowstyle="->")
                    )
                annot = self._hover_annotations[ax]
                annot.xy = closest_point
                annot.set_text(f"x: {closest_point[0]:.3f}\ny: {closest_point[1]:.3f}")
                annot.set_visible(True)
            
        self.canvas.draw_idle()

    # ============================
    # CALCULATION & PLOTTING
    # ============================
    def calculate(self):
        for ax in self.axes.flat:
            ax.clear()

        # Clear tables
        for item in self.detail_table.get_children():
            self.detail_table.delete(item)
        for item in self.maxmin_table.get_children():
            self.maxmin_table.delete(item)

        selected_node = self.project_tree.selection()
        selected_law_idx = None
        selected_profile_idx = None
        if selected_node:
            node_type, data = self.node_map.get(selected_node[0], (None, None))
            if node_type == "profile":
                selected_profile_idx = data
            elif node_type == "law":
                selected_profile_idx = data[0]
                selected_law_idx = data[1]

        # Process profiles
        for p_idx, profile in enumerate(self.project["profiles"]):
            if not profile["visible"] or not profile["laws"]:
                continue

            unit_x = profile.get("unit_x", "s")
            key_name = "duration" if unit_x == "s" else "phase"
            
            sum_laws = sum(l.get(key_name, 0.0) for l in profile["laws"])
            cycle_duration = profile.get("cycle_duration", sum_laws if sum_laws > 0 else 1.0)

            segs = [MotionSegment(l["type"], l["stroke"], l.get(key_name, 0.0), proportions=l.get("proportions"), params={"proportions": l.get("proportions")} if l.get("proportions") is not None else {}) for l in profile["laws"]]
            t, s, v, a, j = compute_cam_motion(segs)

            # Offset initial phase and position
            start_phase = profile.get("start_phase", 0.0)
            t = t + start_phase
            s_offset = profile["start_pos"] - s[0]
            s = s + s_offset

            # Segment splitting for calculated properties
            pts_per_seg = len(t) // max(1, len(profile["laws"]))
            
            for l_idx, l in enumerate(profile["laws"]):
                i_start = l_idx * pts_per_seg
                i_end = (l_idx + 1) * pts_per_seg if l_idx < len(profile["laws"]) - 1 else len(t)

                t_seg = t[i_start:i_end]
                s_seg = s[i_start:i_end]
                v_seg = v[i_start:i_end]
                a_seg = a[i_start:i_end]
                j_seg = j[i_start:i_end]

                dur_t = l.get(key_name, 0.0)
                dur_e = t_seg[-1] - t_seg[0] if len(t_seg) > 1 else dur_t
                stroke_t = l.get("stroke", 0.0)
                stroke_e = s_seg[-1] - s_seg[0] if len(s_seg) > 0 else 0.0

                v_ini_e = v_seg[0] if len(v_seg) > 0 else 0.0
                v_fin_e = v_seg[-1] if len(v_seg) > 0 else 0.0
                a_ini_e = a_seg[0] if len(a_seg) > 0 else 0.0
                a_fin_e = a_seg[-1] if len(a_seg) > 0 else 0.0
                j_ini_e = j_seg[0] if len(j_seg) > 0 else 0.0
                j_fin_e = j_seg[-1] if len(j_seg) > 0 else 0.0

                j_ini_t = j_seg[0] if len(j_seg) > 0 else 0.0
                j_fin_t = j_seg[-1] if len(j_seg) > 0 else 0.0

                # Calculate Cv and Ca coefficients
                if l["type"] != "dwell" and abs(stroke_t) > 1e-9 and dur_t > 0:
                    v_max = np.max(np.abs(v_seg))
                    a_max = np.max(np.abs(a_seg))
                    cv_val = f"{v_max * dur_t / abs(stroke_t):.3f}"
                    ca_val = f"{a_max * (dur_t**2) / abs(stroke_t):.3f}"
                else:
                    cv_val = "-"
                    ca_val = "-"

                # Show in tables:
                # - If a specific law is selected, only show that specific law
                # - If a profile is selected, show all laws in that profile
                # - Otherwise show all laws across all visible profiles
                show_in_table = False
                if selected_law_idx is not None:
                    if p_idx == selected_profile_idx and l_idx == selected_law_idx:
                        show_in_table = True
                elif selected_profile_idx is not None:
                    if p_idx == selected_profile_idx:
                        show_in_table = True
                else:
                    show_in_table = True

                if show_in_table:
                    # Dettaglio input row
                    self.detail_table.insert("", "end", values=(
                        l["name"], cv_val, ca_val,
                        f"{dur_t} {unit_x}", f"{dur_e:.3f} {unit_x}",
                        f"{stroke_t} mm", f"{stroke_e:.3f} mm",
                        f"{l.get('v_ini', 0.0)} mm/s", f"{v_ini_e:.3f} mm/s",
                        f"{l.get('v_fin', 0.0)} mm/s", f"{v_fin_e:.3f} mm/s",
                        f"{l.get('a_ini', 0.0)} mm/s²", f"{a_ini_e:.3f} mm/s²",
                        f"{l.get('a_fin', 0.0)} mm/s²", f"{a_fin_e:.3f} mm/s²",
                        f"{j_ini_t:.3f} mm/s³", f"{j_ini_e:.3f} mm/s³",
                        f"{j_fin_t:.3f} mm/s³", f"{j_fin_e:.3f} mm/s³"
                    ))

                    # Max/min profilo row
                    self.maxmin_table.insert("", "end", values=(
                        l["name"],
                        f"{np.min(s_seg):.2f}", f"{np.max(s_seg):.2f}",
                        f"{np.min(v_seg):.2f}", f"{np.max(v_seg):.2f}",
                        f"{np.min(a_seg):.2f}", f"{np.max(a_seg):.2f}",
                        f"{np.min(j_seg):.2f}", f"{np.max(j_seg):.2f}"
                    ))

                color = "blue" if (selected_law_idx is not None and l_idx == selected_law_idx) else profile.get("color", "#FFA500")

                is_mod = (profile.get("cycle_mod") == "Sì") and (cycle_duration > 0)
                if is_mod:
                    t_mod = t_seg % cycle_duration
                    split_indices = np.where(np.diff(t_mod) < 0)[0] + 1
                    t_sub_list = np.split(t_mod, split_indices)
                    s_sub_list = np.split(s_seg, split_indices)
                    v_sub_list = np.split(v_seg, split_indices)
                    a_sub_list = np.split(a_seg, split_indices)
                    j_sub_list = np.split(j_seg, split_indices)

                    for ts, ss, vs, as_, js in zip(t_sub_list, s_sub_list, v_sub_list, a_sub_list, j_sub_list):
                        if len(ts) > 0:
                            self.axes[0, 0].plot(ts, ss, color=color)
                            self.axes[0, 1].plot(ts, vs, color=color)
                            self.axes[1, 0].plot(ts, as_, color=color)
                            self.axes[1, 1].plot(ts, js, color=color)
                else:
                    self.axes[0, 0].plot(t_seg, s_seg, color=color)
                    self.axes[0, 1].plot(t_seg, v_seg, color=color)
                    self.axes[1, 0].plot(t_seg, a_seg, color=color)
                    self.axes[1, 1].plot(t_seg, j_seg, color=color)

        # Plot markers
        for marker in self.project["markers"]:
            if marker["visible"]:
                color = marker.get("color", "#FF0000")
                for ax in self.axes.flat:
                    ax.axvline(x=marker["value"], color=color, linestyle="-", alpha=0.7)

        titles = [["Spostamento", "Velocità"], ["Accelerazione", "Jerk"]]
        for row in range(2):
            for col in range(2):
                ax = self.axes[row, col]
                ax.set_title(titles[row][col])
                ax.grid(True, linestyle="--", alpha=0.5)
                for profile in self.project["profiles"]:
                    if profile["visible"]:
                        ax.set_xlim(left=0, right=profile.get("cycle_duration", 1.0))
                        break

        self.fig.tight_layout()
        self.canvas.draw()
        self._update_nav_positions()
