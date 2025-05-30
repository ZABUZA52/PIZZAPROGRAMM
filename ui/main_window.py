import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from database import get_connection
from utils import center_window

class MainWindow:
    def __init__(self, root, client_id):
        self.root = root
        self.root.title("Главное меню")
        self.root.geometry("800x600")
        center_window(self.root, 800, 600)

        self.client_id = client_id  # ✅ Сохраняем ID клиента

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Главное меню", font=("Arial", 18)).pack(pady=20)
        ttk.Button(self.root, text="Новый заказ", command=self.open_order).pack(pady=10)
        ttk.Button(self.root, text="Статус заказа", command=self.open_status).pack(pady=10)
        ttk.Button(self.root, text="Выход", command=self.root.quit).pack(pady=10)

    def open_order(self):
        from ui.order_window import OrderWindow
        OrderWindow(tk.Toplevel(), client_id=self.client_id)  # ✅ Передаём свой ID дальше

    def open_status(self):
        conn = get_connection()
        cursor = conn.cursor()
        # Теперь показываем все активные заказы, включая отменённые
        cursor.execute("SELECT id FROM orders WHERE client_id = ?", (self.client_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            order_id = row[0]
            from ui.status_window import StatusWindow
            StatusWindow(tk.Toplevel(), order_id=order_id)
        else:
            messagebox.showinfo("Статус заказа", "Активных заказов нет")