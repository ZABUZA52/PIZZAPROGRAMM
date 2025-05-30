# ui/staff_register.py

import tkinter as tk
from tkinter import messagebox
from models import Staff


class StaffRegisterWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Регистрация сотрудника")
        self.root.geometry("400x300")
        from utils import center_window
        center_window(self.root, 400, 300)

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Регистрация сотрудника", font=("Arial", 16)).pack(pady=20)

        tk.Label(self.root, text="Логин", font=("Arial", 12)).pack()
        self.username_entry = tk.Entry(self.root, width=30)
        self.username_entry.pack(pady=5)

        tk.Label(self.root, text="Пароль", font=("Arial", 12)).pack()
        self.password_entry = tk.Entry(self.root, width=30, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.root, text="Зарегистрироваться", command=self.register).pack(pady=15)
        tk.Button(self.root, text="Назад ко входу", command=self.back_to_login).pack()

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return

        if len(password) < 4:
            messagebox.showerror("Ошибка", "Пароль должен быть не менее 4 символов")
            return

        if Staff.create(username, password):
            messagebox.showinfo("Успех", "Сотрудник зарегистрирован!")
            self.back_to_login()
        else:
            messagebox.showerror("Ошибка", "Этот логин уже занят")

    def back_to_login(self):
        self.root.destroy()
        from ui.staff_login import StaffLoginWindow
        StaffLoginWindow(tk.Tk())