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

        self.title("Simulatore Leggi di Moto")
        self.iconbitmap("Motion_app_logo.ico")
        self.geometry("1200x800")

        self._build_ui()

    # ============================
    # UI
    # ============================
    def _build_ui(self):

        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)

        # layout a 3 colonne
        main.columnconfigure(0, weight=0)  # left
        main.columnconfigure(1, weight=0)  # center
        main.columnconfigure(2, weight=1)  # plot

        main.rowconfigure(0, weight=1)

        # ================= LEFT =================
        left = ttk.Frame(main, padding=5)
        left.grid(row=0, column=0, sticky="ns")

        ttk.Label(left, text="Movimenti").pack(anchor="w")

        self.motion_list = MotionList(left, self.load)

        ttk.Button(left, text="+", command=self.add_motion).pack(fill=tk.X)
        ttk.Button(left, text="-", command=self.remove_motion).pack(fill=tk.X)

        # ================= CENTER =================
        center = ttk.Frame(main, padding=5)
        center.grid(row=0, column=1, sticky="ns")

        ttk.Label(center, text="Segmenti").pack(anchor="w")

        
        seg_container = ttk.Frame(center)
        seg_container.pack(fill=tk.X)


        self.editor = SegmentEditor(seg_container)
        
        self.editor.on_law_change = self.show_params

        ttk.Button(center, text="Aggiungi segmento",
                   command=self.add_segment).pack(fill=tk.X, pady=2)

        ttk.Button(center, text="Calcola",
                   command=self.calculate).pack(fill=tk.X, pady=5)
                   
        # ==== parametri legge ====
        param_frame = ttk.LabelFrame(center, text="Parametri legge")
        param_frame.pack(fill=tk.X, pady=10)

        self.param_frame = param_frame

        self.param_widgets = {}

        # ================= RIGHT =================
        right = ttk.Frame(main, padding=5)
        right.grid(row=0, column=2, sticky="nsew")

        self.fig = Figure(figsize=(6, 6))
        self.axes = self.fig.subplots(4, 1, sharex=True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

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
