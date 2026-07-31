#
#i now need to edit the behaviour of th fase and durata text boxes in the leggi. in editor profilo unità asse x needs to be a drop down menu where you select between ° and s. based on the selection durata ciclo should change unit of measue and its value should be the length of the x axis of the plots. based on that same selection in the editor legge one between fase and durata shoul gray out. is s is selected then fase should be greyed out and if ° is selected then durata shoul be grayed out. the one not greyed out is the one dictating the duration of that legge on the x axis. 

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from motion.core.segment import MotionSegment
from motion.core.cam_motion import compute_cam_motion

from ui.segment_editor import SegmentEditor
from ui.motion_list import MotionList


class MotionApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Progettazione Camme - Marchesini Group S.p.A.")
        try:
            self.iconbitmap("Motion_app_logo.ico")
        except Exception:
            pass
        self.geometry("1400x900")

        # Data structure:
        # project = { 'title': 'Nuovo Progetto', 'profiles': [...], 'markers': [...] }
        self.project = {
            "title": "Nuovo Progetto",
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
                            "v_ini": 0.0,
                            "a_ini": 0.0,
                            "v_fin": 0.0,
                            "a_fin": 0.0,
                            "parz_ini": 0.0,
                            "parz_fin": 0.25,
                            "cv": 2.0,
                            "ca": 4.888
                        },
                        {
                            "type": "dwell",
                            "name": "Sosta",
                            "phase": 10.0,
                            "duration": 0.5,
                            "stroke": 0.0,
                            "v_ini": 0.0,
                            "a_ini": 0.0,
                            "v_fin": 0.0,
                            "a_fin": 0.0,
                            "parz_ini": 0.0,
                            "parz_fin": 0.0,
                            "cv": "NaN",
                            "ca": "NaN"
                        },
                        {
                            "type": "trap_gen",
                            "name": "Trapezoidale generalizzata",
                            "phase": 125.0,
                            "duration": 6.25,
                            "stroke": -600.0,
                            "v_ini": 0.0,
                            "a_ini": 0.0,
                            "v_fin": 0.0,
                            "a_fin": 0.0,
                            "parz_ini": 0.0,
                            "parz_fin": 0.013,
                            "cv": 2.0,
                            "ca": 4.888
                        },
                        {
                            "type": "dwell",
                            "name": "Sosta",
                            "phase": 10.0,
                            "duration": 0.5,
                            "stroke": 0.0,
                            "v_ini": 0.0,
                            "a_ini": 0.0,
                            "v_fin": 0.0,
                            "a_fin": 0.0,
                            "parz_ini": 0.0,
                            "parz_fin": 0.0,
                            "cv": "NaN",
                            "ca": "NaN"
                        }
                    ]
                }
            ],
            "markers": [
                {"value": 6.25, "visible": True, "label": "x = 6.25°"}
            ]
        }

        self.node_map = {}

        self._build_menu()
        self._build_ui()
        self._populate_tree()
        self.calculate()

    # ============================
    # MENU BAR
    # ============================
    def _build_menu(self):
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nuovo Progetto", command=self.new_project)
        file_menu.add_command(label="Apri...", command=lambda: None)
        file_menu.add_command(label="Salva", command=lambda: None)
        file_menu.add_command(label="Salva con nome...", command=lambda: None)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        menubar.add_cascade(label="Modifica", menu=tk.Menu(menubar, tearoff=0))

        # Profili di moto menu
        prof_menu = tk.Menu(menubar, tearoff=0)
        prof_menu.add_command(label="Nuovo profilo", command=self.add_profile)
        prof_menu.add_command(label="Elimina profilo", command=self.remove_profile)
        menubar.add_cascade(label="Profili di moto", menu=prof_menu)

        # Leggi di moto menu
        laws_menu = tk.Menu(menubar, tearoff=0)
        new_law_menu = tk.Menu(laws_menu, tearoff=0)
        new_law_menu.add_command(label="Trapezoidale generalizzata", command=lambda: self.add_law("trap_gen", "Trapezoidale generalizzata"))
        new_law_menu.add_command(label="Sosta", command=lambda: self.add_law("dwell", "Sosta"))
        new_law_menu.add_command(label="Cicloidale", command=lambda: self.add_law("cycloidal", "Cicloidale"))
        new_law_menu.add_command(label="Polinomiale 3-4-5", command=lambda: self.add_law("poly_345", "Polinomiale 3-4-5"))

        laws_menu.add_cascade(label="Nuova legge di moto", menu=new_law_menu)
        laws_menu.add_command(label="Elimina legge", command=self.remove_law)
        menubar.add_cascade(label="Leggi di moto", menu=laws_menu)

        # Strumenti menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Nuovo marker", command=self.add_marker)
        menubar.add_cascade(label="Strumenti", menu=tools_menu)

        menubar.add_cascade(label="Parametrizzazione", menu=tk.Menu(menubar, tearoff=0))
        menubar.add_cascade(label="Opzioni", menu=tk.Menu(menubar, tearoff=0))

        self.config(menu=menubar)

    # ============================
    # UI LAYOUT
    # ============================
    def _build_ui(self):
        v_paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        v_paned.pack(fill=tk.BOTH, expand=True)

        top_paned = ttk.PanedWindow(v_paned, orient=tk.HORIZONTAL)
        v_paned.add(top_paned, weight=4)

        # ================= LEFT SIDEBAR =================
        left_frame = ttk.Frame(top_paned, width=320, padding=2)
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

        self.fig = Figure(figsize=(8, 6))
        self.axes = self.fig.subplots(2, 2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

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
            menu.add_command(label="Elimina Profilo", command=lambda: self._delete_profile_by_idx(data))
        elif node_type == "law":
            p_idx, l_idx = data
            menu.add_command(label="Elimina Legge", command=lambda: self._delete_law_by_idx(p_idx, l_idx))
        elif node_type == "marker":
            menu.add_command(label="Elimina Marker", command=lambda: self._delete_marker_by_idx(data))
        else:
            return

        menu.post(event.x_root, event.y_root)

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
            ("Posizione iniziale", "start_pos", float, " mm"),
            ("Sfasamento iniziale", "start_phase", float, " s"),
            ("Modulo ciclo", "cycle_mod", str, ""),
            ("Unità (asse x)", "unit_x", str, ""),
            ("Velocità ciclo", "cycle_vel", float, " rpm"),
            ("Durata ciclo", "cycle_duration", float, " s"),
            ("Unità (asse y)", "unit_y", str, ""),
        ]

        for i, (label_text, key, val_type, unit) in enumerate(fields):
            ttk.Label(tab_gen, text=label_text).grid(row=i, column=0, sticky="w", pady=2)
            if key == "unit_x":
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
            else:
                if key == "cycle_duration":
                    unit = f" {profile.get('unit_x', 's')}"
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
            clean_unit = unit.strip()
            if clean_unit:
                ttk.Label(tab_gen, text=clean_unit).grid(row=i, column=2, sticky="w", padx=2, pady=2)

            if unit_x == "s" and key == "phase":
                entry.config(state="disabled")
            elif unit_x == "°" and key == "duration":
                entry.config(state="disabled")

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

        frame = ttk.Frame(self.editor_container, padding=5)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="x").grid(row=0, column=0, sticky="w", pady=5)
        e_x = ttk.Entry(frame, width=10)
        e_x.insert(0, f"{marker['value']}")
        e_x.grid(row=0, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Etichetta").grid(row=1, column=0, sticky="w", pady=5)
        e_lbl = ttk.Entry(frame, width=15)
        e_lbl.insert(0, marker["label"])
        e_lbl.grid(row=1, column=1, sticky="w", pady=5)

        def on_x_change(event):
            try:
                val = float(e_x.get())
                marker["value"] = val
                if not marker.get("custom_label", False):
                    marker["label"] = f"x = {val}°"
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
        self.project = {
            "title": "Nuovo Progetto",
            "profiles": [],
            "markers": []
        }
        self._populate_tree()
        self.calculate()

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
            "parz_fin": 0.0,
            "cv": 2.0 if law_type != "dwell" else "NaN",
            "ca": 4.888 if law_type != "dwell" else "NaN"
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

        marker = {
            "value": val,
            "visible": True,
            "label": f"x = {val}°",
            "custom_label": False
        }
        self.project["markers"].append(marker)
        self._populate_tree()
        self.calculate()

    # ============================
    # CALCULATION & PLOTTING
    # ============================
    def calculate(self):
        for ax in self.axes.flat:
            ax.clear()

        # Clear table
        for item in self.detail_table.get_children():
            self.detail_table.delete(item)

        selected_node = self.project_tree.selection()
        selected_law_idx = None
        if selected_node:
            node_type, data = self.node_map.get(selected_node[0], (None, None))
            if node_type == "law":
                selected_law_idx = data[1]

        # Process profiles
        for p_idx, profile in enumerate(self.project["profiles"]):
            if not profile["visible"] or not profile["laws"]:
                continue

            unit_x = profile.get("unit_x", "s")
            key_name = "duration" if unit_x == "s" else "phase"
            
            sum_laws = sum(l.get(key_name, 0.0) for l in profile["laws"])
            cycle_duration = profile.get("cycle_duration", sum_laws if sum_laws > 0 else 1.0)

            segs = [MotionSegment(l["type"], l["stroke"], l.get(key_name, 0.0)) for l in profile["laws"]]
            t, s, v, a, j = compute_cam_motion(segs)

            # Offset initial position
            s = s + profile["start_pos"] - s[0]

            # Populate table
            for l in profile["laws"]:
                self.detail_table.insert("", "end", values=(
                    l["name"], l["cv"], l["ca"],
                    f"{l['duration']} s", f"{l['parz_fin']} s" if l['parz_fin'] else f"{l['duration']} s",
                    f"{l['stroke']} mm", f"{l['stroke']} mm",
                    f"{l['v_ini']} mm/s", f"{l['v_ini']} mm/s",
                    f"{l['v_fin']} mm/s", f"{l['v_fin']} mm/s",
                    f"{l['a_ini']} mm/s²", f"{l['a_ini']} mm/s²",
                    f"{l['a_fin']} mm/s²", f"{l['a_fin']} mm/s²",
                    "0 mm/s³", "-460.695 mm/s³",
                    "0 mm/s³", "-460.695 mm/s³"
                ))

            # Segment splitting for highlighting
            pts_per_seg = len(t) // max(1, len(profile["laws"]))
            
            for l_idx in range(len(profile["laws"])):
                i_start = l_idx * pts_per_seg
                i_end = (l_idx + 1) * pts_per_seg if l_idx < len(profile["laws"]) - 1 else len(t)

                color = "blue" if (selected_law_idx is not None and l_idx == selected_law_idx) else "orange"

                self.axes[0, 0].plot(t[i_start:i_end], s[i_start:i_end], color=color)
                self.axes[0, 1].plot(t[i_start:i_end], v[i_start:i_end], color=color)
                self.axes[1, 0].plot(t[i_start:i_end], a[i_start:i_end], color=color)
                self.axes[1, 1].plot(t[i_start:i_end], j[i_start:i_end], color=color)

        # Plot markers
        for marker in self.project["markers"]:
            if marker["visible"]:
                for ax in self.axes.flat:
                    ax.axvline(x=marker["value"], color="red", linestyle="-", alpha=0.7)

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
