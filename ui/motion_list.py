import tkinter as tk

class MotionList:

    def __init__(self, parent, on_select):

        self.listbox = tk.Listbox(parent)
        self.listbox.pack()

        self.on_select = on_select
        self.listbox.bind("<<ListboxSelect>>", self._selected)

    def add(self, name):
        self.listbox.insert(tk.END, name)

    def get_index(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def delete_selected(self):
        idx = self.get_index()
        if idx is None:
            return None

        self.listbox.delete(idx)
        return idx

    def _selected(self, event):
        self.on_select()
