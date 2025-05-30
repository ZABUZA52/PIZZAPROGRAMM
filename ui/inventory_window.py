# ui/inventory_window.py
import tkinter as tk
from tkinter import simpledialog, messagebox
from models import Ingredient
from utils import center_window

class InventoryWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление складом")
        self.root.geometry("600x400")
        center_window(self.root, 600, 400)
        self.create_widgets()
        self.load_ingredients()

    def create_widgets(self):
        tk.Label(self.root, text="Ингредиенты на складе", font=("Arial", 16)).pack(pady=20)
        self.tree = tk.ttk.Treeview(self.root, columns=("ingredient", "quantity"), show="headings")
        self.tree.heading("ingredient", text="Ингредиент")
        self.tree.heading("quantity", text="Количество")
        self.tree.column("ingredient", width=400)
        self.tree.column("quantity", width=100)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Button(self.root, text="Пополнить ингредиент", command=self.update_inventory).pack(pady=10)
        tk.Button(self.root, text="Назад", command=self.back_to_staff_menu).pack(pady=10)

    def load_ingredients(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        ingredients = Ingredient.get_all()
        for ing in ingredients:
            self.tree.insert("", "end", values=(ing["name"], ing["quantity"]))

    def update_inventory(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Ошибка", "Выберите ингредиент для пополнения")
            return

        item = self.tree.item(selected_item)
        ingredient_name = item["values"][0]
        new_amount = simpledialog.askinteger("Пополнение склада", f"Введите новое количество для '{ingredient_name}':")
        if new_amount is None or new_amount < 0:
            return

        Ingredient.update_quantity(ingredient_name, new_amount)
        messagebox.showinfo("Успех", f"Количество '{ingredient_name}' обновлено на {new_amount}")
        self.load_ingredients()

    def back_to_staff_menu(self):
        self.root.destroy()
        from ui.staff_window import StaffMainWindow
        StaffMainWindow(tk.Tk())