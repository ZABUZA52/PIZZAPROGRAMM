# ui/staff_login.py

import tkinter as tk
from tkinter import messagebox
from models import Staff


class StaffLoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Вход для сотрудника")
        self.root.geometry("400x300")
        from utils import center_window
        center_window(self.root, 400, 300)

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Авторизация сотрудника", font=("Arial", 16)).pack(pady=20)

        tk.Label(self.root, text="Логин", font=("Arial", 12)).pack()
        self.username_entry = tk.Entry(self.root, width=30)
        self.username_entry.pack(pady=5)

        tk.Label(self.root, text="Пароль", font=("Arial", 12)).pack()
        self.password_entry = tk.Entry(self.root, width=30, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.root, text="Войти", command=self.login).pack(pady=15)

        tk.Label(self.root, text="Еще не зарегистрированы?", fg="gray").pack()
        tk.Button(self.root, text="Зарегистрироваться", command=self.open_register).pack(pady=5)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if Staff.authenticate(username, password):
            self.root.destroy()
            from ui.staff_window import StaffMainWindow
            StaffMainWindow(tk.Tk())
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

    def open_register(self):
        self.root.withdraw()
        from ui.staff_register import StaffRegisterWindow
        StaffRegisterWindow(tk.Toplevel())