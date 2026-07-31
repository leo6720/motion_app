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

        self.motion_sets = []
        self.current = None

        self.title("Progettazione Camme - Simulatore Leggi di Moto")
        try:
            self.iconbitmap("Motion_app_logo.ico")
        except Exception:
            pass
        self.geometry("1400x900")

        self._build_menu()
        self._build_ui()

    # ============================
    # MENU BAR
    # ============================
    def _build_menu(self):
        menubar = tk.Menu(self)

        menubar.add_cascade(label="File", menu=tk.Menu(menubar, tearoff=0))
        menubar.add_cascade(label="Modifica", menu=tk.Menu(menubar, tearoff=0))
        menubar.add_cascade(label="Profili di moto", menu=tk.Menu(menubar, tearoff=0))
        menubar.add_cascade(label="Leggi di moto", menu=tk.Menu(menubar, tearoff=0))
        menubar.add_cascade(label="Strumenti", menu=tk.Menu(menubar, tearoff=0))
        menubar.add_cascade(label="Parametrizzazione", menu=tk.Menu(menubar, tearoff=0))
        menubar.add_cascade(label="Opzioni", menu=tk.Menu(menubar, tearoff=0))

        self.config(menu=menubar)

    # ============================
    # UI LAYOUT
    # ============================
    def _build_ui(self):
        # Vertical split: Top (Tree + Plots) / Bottom (Table)
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

        root_node = self.project_tree.insert("", "end", text="Nuovo Progetto", open=True)
        self.profile_node = self.project_tree.insert(root_node, "end", text="☑ Nuovo Profilo", open=True)
        
        # Sample items under profile
        self.project_tree.insert(self.profile_node, "end", text="Trapezoidale generalizzata")
        self.project_tree.insert(self.profile_node, "end", text="Sosta")
        self.project_tree.insert(self.profile_node, "end", text="Trapezoidale generalizzata")
        self.project_tree.insert(self.profile_node, "end", text="Sosta")

        self.markers_node = self.project_tree.insert(root_node, "end", text="Markers", open=True)
        self.project_tree.insert(self.markers_node, "end", text="☑ x = 6.25°")

        self.project_tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # 2. Contextual Editor Frame
        self.editor_container = ttk.LabelFrame(left_frame, text="Editor Legge", padding=5)
        self.editor_container.pack(fill=tk.BOTH, expand=True)

        self._build_profile_editor()

        # ================= RIGHT PLOTS (2x2 Grid) =================
        right_frame = ttk.Frame(top_paned, padding=2)
        top_paned.add(right_frame, weight=1)

        self.fig = Figure(figsize=(8, 6))
        # 2x2 layout for Spostamento, Velocità, Accelerazione, Jerk
        self.axes = self.fig.subplots(2, 2, sharex=True)
        self.ax_pos = self.axes[0, 0]
        self.ax_vel = self.axes[0, 1]
        self.ax_acc = self.axes[1, 0]
        self.ax_jrk = self.axes[1, 1]

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ================= BOTTOM DATA TABLE =================
        bottom_frame = ttk.Frame(v_paned, padding=2)
        v_paned.add(bottom_frame, weight=1)

        self.bottom_notebook = ttk.Notebook(bottom_frame)
        self.bottom_notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Dettaglio input
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
            self.detail_table.column(col_id, width=80, anchor="center")

        # Tab 2: Max/min profilo
        tab_maxmin = ttk.Frame(self.bottom_notebook)
        self.bottom_notebook.add(tab_maxmin, text="Max/min profilo")

    def _build_profile_editor(self):
        for child in self.editor_container.winfo_children():
            child.destroy()

        editor_nb = ttk.Notebook(self.editor_container)
        editor_nb.pack(fill=tk.BOTH, expand=True)

        tab_gen = ttk.Frame(editor_nb, padding=5)
        editor_nb.add(tab_gen, text="Input generici")
        editor_nb.add(ttk.Frame(editor_nb), text="Input specifici")
        editor_nb.add(ttk.Frame(editor_nb), text="Output")

        fields = [
            ("Fase", "125.0 °"),
            ("Durata", "6.25 s"),
            ("Salto", "-600.0 mm"),
            ("Velocità iniziale", "0.0 mm/s"),
            ("Accelerazione iniziale", "0.0 mm/s²"),
            ("Velocità finale", "0.0 mm/s"),
            ("Accelerazione finale", "0.0 mm/s²"),
        ]

        for i, (label_text, val) in enumerate(fields):
            ttk.Label(tab_gen, text=label_text).grid(row=i, column=0, sticky="w", pady=2)
            entry = ttk.Entry(tab_gen, width=12)
            entry.insert(0, val)
            entry.grid(row=i, column=1, sticky="e", pady=2)

    def _on_tree_select(self, event):
        selected = self.project_tree.selection()
        if not selected:
            return
        item_text = self.project_tree.item(selected[0], "text")
        if "Profilo" in item_text:
            self.editor_container.config(text="Editor Profilo")
        elif "x =" in item_text or "Marker" in item_text:
            self.editor_container.config(text="Editor Marker")
        else:
            self.editor_container.config(text="Editor Legge")

    # ============================
    # MOTION LIST
    # ============================
    def add_motion(self):
        self.motion_sets.append([])
        self.motion_list.add(f"Mov {len(self.motion_sets)}")

    # ============================
    # LOAD
    # ============================
    def load(self):

        idx = self.motion_list.get_index()
        if idx is None:
            return

        # ✅ SALVA quello attuale PRIMA di cambiare
        if self.current is not None:
            self.motion_sets[self.current] = self.editor.get_segments()

        self.current = idx

        self.editor.clear()

        data = self.motion_sets[idx]

        for i, (law, s, t) in enumerate(data):

            self.editor.add()

            row = self.editor.rows[-1]

            row.law.set(law)
            row.stroke.set(str(s))
            row.time.set(str(t))

            self.show_params(law)

    # ============================
    # CALCOLO
    # ============================
    def calculate(self):

        try:

            if self.current is None:
                return

            # salva corrente
            self.motion_sets[self.current] = self.editor.get_segments()

            # pulizia
            for ax in self.axes:
                ax.clear()

            # plot tutti i movimenti
            for i, motion in enumerate(self.motion_sets):

                if not motion:
                    continue

                segs = [MotionSegment(l, s, t, p) for l, s, t, p in motion]

                t, s, v, a, j = compute_cam_motion(segs)

                self.axes[0].plot(t, s, label=f"M{i+1}")
                self.axes[1].plot(t, v)
                self.axes[2].plot(t, a)
                self.axes[3].plot(t, j)

            # sistemazione grafici
            titles = ["Posizione", "Velocità", "Accelerazione", "Jerk"]

            for ax, title in zip(self.axes, titles):
                ax.set_title(title)
                ax.grid()

            self.axes[0].legend()

            self.fig.tight_layout()
            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Errore", str(e))
            
    
    def show_params(self, law):
        if law is None:
            return

        # recupera segmento attivo
        row = self.editor.active_row
        if row is None:
            return

        # pulisci UI
        for widget in self.param_frame.winfo_children():
            widget.destroy()

        self.param_widgets = {}

        # =========================
        if law == "trapezoidale":

            ttk.Label(self.param_frame, text="λ accel (0-0.5)").pack()

            var = tk.StringVar(value=str(row.params.get("lam", 0.25)))

            def update(*args):
                try:
                    row.params["lam"] = float(var.get())
                except:
                    pass

            var.trace_add("write", update)

            entry = ttk.Entry(self.param_frame, textvariable=var)
            entry.pack()

        # =========================
        elif law == "trap_gen":

            ttk.Label(
                self.param_frame,
                text="Segmenti (es: 35-30-10-0-10-15-10)"
            ).pack()

            default = row.params.get(
                "profile",
                [35,30,10,0,10,15,10]
            )

            var = tk.StringVar(value="-".join(map(str, default)))

            def update(*args):
                try:
                    values = [float(x) for x in var.get().split("-")]
                    if len(values) == 7:
                        row.params["profile"] = values
                except:
                    pass

            var.trace_add("write", update)

            entry = ttk.Entry(self.param_frame, textvariable=var)
            entry.pack(fill=tk.X)

        # =========================
        else:
            ttk.Label(self.param_frame, text="Nessun parametro").pack()

 
    def remove_motion(self):

        idx = self.motion_list.delete_selected()

        if idx is None:
            return

        del self.motion_sets[idx]

        self.current = None
        self.editor.clear()
        
    def add_segment(self):

        # ✅ se nessun movimento esiste → crealo
        if self.current is None:

            self.motion_sets.append([])
            idx = len(self.motion_sets) - 1

            self.motion_list.add(f"Mov {len(self.motion_sets)}")

            # seleziona automaticamente
            self.motion_list.listbox.selection_clear(0, tk.END)
            self.motion_list.listbox.selection_set(idx)
            self.motion_list.listbox.activate(idx)

            self.current = idx

        self.editor.add()
