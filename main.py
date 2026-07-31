from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from ui.tk_app import MotionApp


if __name__ == "__main__":
    app = MotionApp()
    app.mainloop()
