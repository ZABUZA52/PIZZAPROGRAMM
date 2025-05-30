# ui/role_selection.py

import tkinter as tk
from tkinter import ttk


class RoleSelectionWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Выбор роли")
        self.root.geometry("400x300")
        from utils import center_window
        center_window(self.root, 400, 300)

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Выберите роль", font=("Arial", 16)).pack(pady=30)

        ttk.Button(self.root, text="Я клиент", width=25, command=self.open_client_login).pack(pady=10)
        ttk.Button(self.root, text="Я сотрудник", width=25, command=self.open_staff_login).pack(pady=10)

    def open_client_login(self):
        self.root.withdraw()
        from ui.login_window import LoginWindow
        LoginWindow(tk.Toplevel())

    def open_staff_login(self):
        self.root.withdraw()
        from ui.staff_login import StaffLoginWindow
        StaffLoginWindow(tk.Toplevel())