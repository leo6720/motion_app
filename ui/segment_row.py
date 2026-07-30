import tkinter as tk
from tkinter import ttk


class SegmentRow:
    def __init__(self, parent, row, on_law_change=None, on_delete=None, editor=None):

        self.parent = parent
        self.editor = editor

        self.on_law_change = on_law_change
        self.on_delete = on_delete

        self.params = {}
        self.current_row = None
        self.active_row = None

        # variabili
        self.law = tk.StringVar(value="cicloidale")
        self.stroke = tk.StringVar(value="100")
        self.time = tk.StringVar(value="1.0")

        # =========================
        # combobox legge
        # =========================
        self.cmb = ttk.Combobox(
            parent,
            textvariable=self.law,
            values=[
                "cicloidale",
                "polinomiale 3-4-5",
                "s-curve 4-5-6-7",
                "trapezoidale",
                "triangolare",
                "sosta",
                "trap_gen"
            ],
            state="readonly",
            width=20
        )
        self.cmb.bind("<<ComboboxSelected>>", self._on_change)

        # =========================
        # ΔS
        # =========================
        self.ent_s = ttk.Entry(
            parent,
            textvariable=self.stroke,
            width=10
        )

        # =========================
        # durata
        # =========================
        self.ent_t = ttk.Entry(
            parent,
            textvariable=self.time,
            width=10
        )

        # =========================
        # DELETE
        # =========================
        self.btn_del = ttk.Button(
            parent,
            text="X",
            width=3,
            command=self._delete
        )

        # =========================
        # MOVE
        # =========================
        self.btn_up = ttk.Button(
            parent,
            text="↑",
            width=3,
            command=self._move_up
        )

        self.btn_down = ttk.Button(
            parent,
            text="↓",
            width=3,
            command=self._move_down
        )

        self.grid(row)

    # =========================
    def grid(self, row):
        self.cmb.grid(row=row, column=0, padx=2, pady=2)
        self.ent_s.grid(row=row, column=1, padx=2)
        self.ent_t.grid(row=row, column=2, padx=2)
        self.btn_del.grid(row=row, column=3, padx=2)
        self.btn_up.grid(row=row, column=4)
        self.btn_down.grid(row=row, column=5)

    # =========================
    def _delete(self):
        if self.on_delete:
            self.on_delete(self)

    def _move_up(self):
        if self.editor:
            self.editor.move_up(self)

    def _move_down(self):
        if self.editor:
            self.editor.move_down(self)

    # =========================
    def _on_change(self, event=None):

        law = self.law.get()

        # imposta riga corrente
        if self.editor:
            self.editor.active_row = self

        if self.on_law_change:
            self.on_law_change(law)

        self._auto_adjust(law)


    # =========================
    def _auto_adjust(self, law):

        if law == "sosta":
            self.stroke.set("0")
            self.ent_s.configure(state="disabled")
        else:
            self.ent_s.configure(state="normal")
