from ui.segment_row import SegmentRow


class SegmentEditor:

    def __init__(self, frame):

        self.frame = frame
        self.rows = []

        self.on_law_change = None

    # =========================
    def add(self):

        row = SegmentRow(
            self.frame,
            len(self.rows),
            on_law_change=self.on_law_change,
            on_delete=self.remove_row,
            editor=self
        )

        self.rows.append(row)
        self.refresh()

    # =========================
    def remove_row(self, row):

        if row in self.rows:
            self.rows.remove(row)

            for w in [
                row.cmb, row.ent_s, row.ent_t,
                row.btn_del, row.btn_up, row.btn_down
            ]:
                w.destroy()

        self.refresh()

    # =========================
    def move_up(self, row):

        i = self.rows.index(row)
        if i == 0:
            return

        self.rows[i], self.rows[i - 1] = self.rows[i - 1], self.rows[i]
        self.refresh()

    # =========================
    def move_down(self, row):

        i = self.rows.index(row)
        if i == len(self.rows) - 1:
            return

        self.rows[i], self.rows[i + 1] = self.rows[i + 1], self.rows[i]
        self.refresh()

    # =========================
    def clear(self):

        for r in self.rows:
            for w in [
                r.cmb, r.ent_s, r.ent_t,
                r.btn_del, r.btn_up, r.btn_down
            ]:
                w.destroy()

        self.rows = []

    # =========================
    def refresh(self):

        for i, r in enumerate(self.rows):
            r.grid(i)

    # =========================
    def get_segments(self):

        segments = []

        for r in self.rows:
            try:
                law = r.law.get()
                stroke = float(r.stroke.get())
                duration = float(r.time.get())

                segments.append((law, stroke, duration, r.params))

            except ValueError:
                continue

        return segments
