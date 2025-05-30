# main.py

import tkinter as tk
from ui.role_selection import RoleSelectionWindow

if __name__ == "__main__":
    root = tk.Tk()
    RoleSelectionWindow(root)
    root.mainloop()