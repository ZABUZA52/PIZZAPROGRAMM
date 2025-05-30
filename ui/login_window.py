# ui/login_window.py

import tkinter as tk
from tkinter import messagebox
from models import Client
from utils import center_window


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Вход в систему")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        center_window(self.root, 400, 300)

        # Храним введённые цифры
        self.digits = [""] * 10
        self.entries = []

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Вход в систему", font=("Arial", 16)).pack(pady=15)

        tk.Label(self.root, text="Номер телефона", font=("Arial", 12)).pack()
        frame = tk.Frame(self.root)
        frame.pack(pady=5)

        # Фиксированный префикс
        tk.Label(frame, text="+7", font=("Arial", 12)).pack(side="left")

        # Поля ввода (10 штук)
        for i in range(10):
            entry = tk.Entry(frame, width=1, font=("Arial", 12), justify="center")
            entry.pack(side="left", padx=1)
            entry.bind("<KeyRelease>", lambda e, idx=i: self.on_key_release(e, idx))
            entry.bind("<KeyPress>", lambda e, idx=i: self.on_key_press(e, idx))
            self.entries.append(entry)

        # Кнопки
        tk.Button(self.root, text="Войти", command=self.login).pack(pady=15)

        tk.Label(self.root, text="Если вы еще не зарегистрированы", fg="gray").pack()
        tk.Button(self.root, text="Зарегистрироваться", command=self.open_register).pack(pady=5)

    def on_key_press(self, event, idx):
        """Обработка нажатия клавиш"""
        if event.keysym == "BackSpace":
            self.handle_backspace(idx)
            return "break"
        elif not event.char.isdigit():
            return "break"

    def on_key_release(self, event, idx):
        value = event.widget.get()
        if value and value[-1].isdigit():
            self.digits[idx] = value[-1]
            event.widget.delete(0, tk.END)
            event.widget.insert(0, self.digits[idx])

            # Переход к следующему полю
            if idx < 9:
                self.entries[idx + 1].focus_set()
        else:
            self.digits[idx] = ""
            event.widget.delete(0, tk.END)

    def handle_backspace(self, idx):
        """Удаление предыдущей цифры и фокус на предыдущее поле"""
        if idx > 0 and self.digits[idx - 1]:
            self.digits[idx - 1] = ""
            self.entries[idx - 1].delete(0, tk.END)
            self.entries[idx - 1].focus_set()
        elif self.digits[idx]:
            self.digits[idx] = ""
            self.entries[idx].delete(0, tk.END)
            if idx > 0:
                self.entries[idx - 1].focus_set()

    def get_phone_number(self):
        phone_digits = ''.join(self.digits)
        if len(phone_digits) != 10:
            return None
        return "+7" + phone_digits

    def login(self):
        phone = self.get_phone_number()
        if not phone:
            messagebox.showerror("Ошибка", "Введите корректный номер телефона")
            return

        client = Client.get_by_phone(phone)
        if client:
            messagebox.showinfo("Успех", f"Добро пожаловать, {client.name}!")
            self.root.destroy()
            from ui.main_window import MainWindow
            MainWindow(tk.Tk(), client.id)  # ✅ Передаём реальный client.id
        else:
            messagebox.showerror("Ошибка", "Клиент с таким телефоном не найден")

    def open_register(self):
        self.root.withdraw()
        RegisterWindow(tk.Toplevel(self.root))


class RegisterWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Регистрация клиента")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        center_window(self.root, 400, 300)

        self.digits = [""] * 10
        self.entries = []
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Регистрация нового клиента", font=("Arial", 16)).pack(pady=10)

        tk.Label(self.root, text="Имя клиента", font=("Arial", 12)).pack()
        self.name_entry = tk.Entry(self.root, width=30)
        self.name_entry.pack(pady=5)

        tk.Label(self.root, text="Номер телефона", font=("Arial", 12)).pack()
        frame = tk.Frame(self.root)
        frame.pack(pady=5)

        tk.Label(frame, text="+7", font=("Arial", 12)).pack(side="left")

        for i in range(10):
            entry = tk.Entry(frame, width=1, font=("Arial", 12), justify="center")
            entry.pack(side="left", padx=1)
            entry.bind("<KeyRelease>", lambda e, idx=i: self.on_key_release(e, idx))
            entry.bind("<KeyPress>", lambda e, idx=i: self.on_key_press(e, idx))
            self.entries.append(entry)

        tk.Button(self.root, text="Зарегистрироваться", command=self.register).pack(pady=15)
        tk.Button(self.root, text="Назад ко входу", command=self.back_to_login).pack()

    def on_key_press(self, event, idx):
        if event.keysym == "BackSpace":
            self.handle_backspace(idx)
            return "break"
        elif not event.char.isdigit():
            return "break"

    def on_key_release(self, event, idx):
        value = event.widget.get()
        if value and value[-1].isdigit():
            self.digits[idx] = value[-1]
            event.widget.delete(0, tk.END)
            event.widget.insert(0, self.digits[idx])

            if idx < 9:
                self.entries[idx + 1].focus_set()
        else:
            self.digits[idx] = ""
            event.widget.delete(0, tk.END)

    def handle_backspace(self, idx):
        if idx > 0 and self.digits[idx - 1]:
            self.digits[idx - 1] = ""
            self.entries[idx - 1].delete(0, tk.END)
            self.entries[idx - 1].focus_set()
        elif self.digits[idx]:
            self.digits[idx] = ""
            self.entries[idx].delete(0, tk.END)
            if idx > 0:
                self.entries[idx - 1].focus_set()

    def get_phone_number(self):
        phone_digits = ''.join(self.digits)
        if len(phone_digits) != 10:
            return None
        return "+7" + phone_digits

    def register(self):
        name = self.name_entry.get().strip()
        phone = self.get_phone_number()

        if not name or not phone:
            messagebox.showerror("Ошибка", "Введите имя и номер телефона")
            return

        if Client.get_by_phone(phone):
            messagebox.showerror("Ошибка", "Клиент с таким номером уже существует")
            return

        Client.create(name, phone)
        messagebox.showinfo("Успех", "Вы успешно зарегистрированы!")
        self.back_to_login()

    def back_to_login(self):
        self.root.destroy()
        from ui.login_window import LoginWindow
        LoginWindow(tk.Tk())