import numpy as np
from tkinter import filedialog, messagebox
from motion.core.segment import MotionSegment
from motion.core.cam_motion import compute_cam_motion

def export_to_ibl(project, plot_type):
    all_t = []
    y_data = []

    for profile in project["profiles"]:
        if not profile["visible"] or not profile["laws"]:
            continue

        unit_x = profile.get("unit_x", "s")
        key_name = "duration" if unit_x == "s" else "phase"
        
        segs = [MotionSegment(l["type"], l["stroke"], l.get(key_name, 0.0), proportions=l.get("proportions"), params={"proportions": l.get("proportions")} if l.get("proportions") is not None else {}) for l in profile["laws"]]
        t, s, v, a, j = compute_cam_motion(segs)

        s_offset = profile["start_pos"] - s[0]
        s = s + s_offset

        all_t = t
        if plot_type == "displacement":
            y_data = s
        elif plot_type == "speed":
            y_data = v
        elif plot_type == "acceleration":
            y_data = a
        elif plot_type == "jerk":
            y_data = j
        break

    if not all_t:
        messagebox.showwarning("Attenzione", "Nessun dato visibile da esportare.")
        return

    filename = filedialog.asksaveasfilename(
        title="Salva file IBL",
        defaultextension=".ibl", 
        filetypes=[("IBL files", "*.ibl"), ("All files", "*.*")]
    )
    
    if not filename:
        return

    try:
        with open(filename, "w") as f:
            f.write("open\narclength\nbegin section ! 1\nbegin curve ! 1\n")
            for tx, ty in zip(all_t, y_data):
                f.write(f"{tx}\t{ty}\t0.0\n")
        messagebox.showinfo("Successo", f"File IBL '{filename}' esportato correttamente.")
    except Exception as e:
        messagebox.showerror("Errore", f"Impossibile salvare il file: {e}")
