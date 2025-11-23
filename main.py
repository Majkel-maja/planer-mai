# main.py

import tkinter as tk
from app import TodoApp

if __name__ == "__main__":
    root = tk.Tk()

    # tworzymy aplikację (ona sama ustawia geometry, fullscreen button itd.)
    app = TodoApp(root)

    # zamykanie okna z X w rogu -> też zapisuje
    root.protocol("WM_DELETE_WINDOW", app.exit_app)

    root.mainloop()
