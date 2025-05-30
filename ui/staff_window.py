# ui/staff_window.py
import tkinter as tk
from tkinter import ttk
from ui.inventory_window import InventoryWindow

class StaffMainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Меню сотрудника")
        self.root.geometry("800x600")
        from utils import center_window
        center_window(self.root, 800, 600)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Меню сотрудника", font=("Arial", 18)).pack(pady=20)
        ttk.Button(self.root, text="Просмотреть все заказы", width=30, command=self.view_orders).pack(pady=10)
        ttk.Button(self.root, text="Управление складом", width=30, command=self.manage_inventory).pack(pady=10)
        ttk.Button(self.root, text="Выход", width=30, command=self.root.quit).pack(pady=10)

    def view_orders(self):
        self.root.withdraw()
        from ui.order_window import OrdersViewWindow
        OrdersViewWindow(tk.Toplevel())

    def manage_inventory(self):
        self.root.withdraw()
        InventoryWindow(tk.Toplevel())