# ui/order_window.py
import json
import tkinter as tk
from tkinter import ttk, messagebox
from models import Order
from database import get_connection
from datetime import datetime, timedelta
from utils import center_window

class OrderWindow:
    def __init__(self, root, client_id):
        self.root = root
        self.root.title("Оформление заказа")
        self.root.geometry("600x500")
        center_window(self.root, 600, 500)
        self.client_id = client_id
        self.items = [
            {"name": "Пепперони", "price": 350},
            {"name": "Маргарита", "price": 300},
            {"name": "Гавайская", "price": 400},
            {"name": "Четыре сыра", "price": 450},
        ]
        self.selected_items = []
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Выберите пиццы", font=("Arial", 16)).pack(pady=10)
        self.item_vars = []

        for item in self.items:
            var = tk.IntVar()
            frame = tk.Frame(self.root)
            frame.pack(anchor="w", padx=20, pady=5)

            # Проверяем наличие ингредиентов
            available, reason = self.check_pizza_availability(item["name"], 1)
            state = "normal" if available else "disabled"

            checkbox = tk.Checkbutton(frame, variable=var, state=state)
            checkbox.pack(side="left")

            label_text = f"{item['name']} — {item['price']} руб"
            if not available:
                label_text += f" ({reason})"

            tk.Label(frame, text=label_text).pack(side="left", padx=10)
            qty = tk.Spinbox(frame, from_=1, to=10, width=5, state=state)
            qty.pack(side="left")
            self.item_vars.append((var, qty, item))

        tk.Button(self.root, text="Посчитать сумму", command=self.calculate_total).pack(pady=10)
        self.summary_label = tk.Label(self.root, text="", justify="left")
        self.summary_label.pack(pady=10)
        self.confirm_button = tk.Button(self.root, text="Оформить заказ", command=self.confirm_order)
        self.confirm_button.pack(pady=10)
        self.confirm_button.pack_forget()  # Скрыта до подсчёта

    def check_pizza_availability(self, pizza_name, quantity):
        """Проверяет, достаточно ли ингредиентов для данной пиццы"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT i.name, pi.required_quantity 
            FROM pizza_ingredients pi
            JOIN ingredients i ON pi.ingredient_id = i.id
            WHERE pi.pizza_name = ?
        ''', (pizza_name,))
        required_ingredients = cursor.fetchall()

        for ing_name, req_qty_per_pizza in required_ingredients:
            cursor.execute("SELECT quantity FROM ingredients WHERE name=?", (ing_name,))
            current_qty = cursor.fetchone()[0]
            total_needed = req_qty_per_pizza * quantity

            if current_qty < total_needed:
                conn.close()
                return False, f"Недостаточно {ing_name} ({current_qty} из {total_needed})"
        
        conn.close()
        return True, ""

    def calculate_total(self):
        self.selected_items = []
        for var, qty, item in self.item_vars:
            if var.get() == 1:
                quantity = int(qty.get())
                # Проверяем наличие ингредиентов для данной пиццы
                available, reason = self.check_pizza_availability(item["name"], quantity)
                if not available:
                    messagebox.showwarning("Недостаточно ингредиентов", f"Не хватает ингредиентов для {item['name']} (x{quantity}): {reason}")
                    return

                self.selected_items.append({
                    "name": item["name"],
                    "price": item["price"],
                    "quantity": quantity
                })

        if not self.selected_items:
            self.summary_label.config(text="Выберите хотя бы одну пиццу.")
            self.confirm_button.pack_forget()
            return

        summary_text = ""
        total = 0
        for item in self.selected_items:
            price = item["price"] * item["quantity"]
            total += price
            summary_text += f"{item['name']} x{item['quantity']} — {price:.2f} руб\n"
        summary_text += f"\nИтого: {total:.2f} руб"

        self.summary_label.config(text=summary_text)
        self.confirm_button.pack(pady=10)

    def check_pizza_availability(self, pizza_name, quantity):
        """Проверяет, достаточно ли ингредиентов для заданного количества пицц"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT i.name, pi.required_quantity 
            FROM pizza_ingredients pi
            JOIN ingredients i ON pi.ingredient_id = i.id
            WHERE pi.pizza_name = ?
        ''', (pizza_name,))
        required_ingredients = cursor.fetchall()

        for ing_name, req_qty_per_pizza in required_ingredients:
            total_required = req_qty_per_pizza * quantity
            cursor.execute("SELECT quantity FROM ingredients WHERE name=?", (ing_name,))
            current_qty = cursor.fetchone()[0]
            if current_qty < total_required:
                conn.close()
                return False, f"{ing_name}: требуется {total_required}, доступно {current_qty}"

        conn.close()
        return True, ""

    def confirm_order(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE client_id = ? AND status NOT IN ('Выдан', 'Отменён')", (self.client_id,))
        active_order = cursor.fetchone()
        conn.close()
        if active_order:
            messagebox.showwarning("Ошибка", "У вас уже есть активный заказ.")
            return

        total_price = sum(item["price"] * item["quantity"] for item in self.selected_items)
        Order.create(self.client_id, total_price, self.selected_items)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT last_insert_rowid()")
        order_id = cursor.fetchone()[0]
        conn.close()
        messagebox.showinfo("Заказ оформлен", "Ваш заказ создан!")
        self.root.destroy()
        from ui.main_window import MainWindow
        MainWindow(tk.Tk(), client_id=self.client_id)


# ==============================
# Клиентская часть: отслеживание статуса заказа
# ==============================

class StatusWindow:
    def __init__(self, root, order_id):
        self.root = root
        self.root.title("Статус заказа")
        self.root.geometry("600x450")
        center_window(self.root, 600, 450)
        self.order_id = order_id
        self.create_widgets()
        self.load_order_info()
        self.start_auto_update()

    def create_widgets(self):
        self.status_label = tk.Label(self.root, text="Статус: Загрузка...", font=("Arial", 16))
        self.status_label.pack(pady=20)

        self.time_label = tk.Label(self.root, text="Время до готовности: --", font=("Arial", 14))
        self.time_label.pack(pady=10)

        self.progress = tk.Label(self.root, text="Этапы готовки:", font=("Arial", 14))
        self.progress.pack(pady=10)

        self.steps_labels = []
        steps = ["Заказ принят", "Добавление ингредиентов", "Выпекание", "Упаковка", "Готов к выдаче"]
        for step in steps:
            label = tk.Label(self.root, text=f"🔹 {step}")
            label.pack(anchor="w", padx=40)
            self.steps_labels.append(label)

        self.cancel_button = tk.Button(self.root, text="Отменить заказ", fg="red", command=self.cancel_order)
        self.cancel_button.pack(pady=10)

        tk.Button(self.root, text="Назад в меню", command=self.back_to_menu).pack(pady=10)

    def load_order_info(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status, created_at, details, cancel_reason FROM orders WHERE id=?", (self.order_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            self.status, created_at, details_json, self.cancel_reason = row
            self.created_time = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            self.cooking_ends = self.created_time + timedelta(minutes=15)
        else:
            self.status = "Не найден"
            self.cancel_reason = None

    def start_auto_update(self):
        self.update_status()
        self.root.after(3000, self.start_auto_update)

    def update_status(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status, cancel_reason FROM orders WHERE id=?", (self.order_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            new_status, cancel_reason = row
            self.status = new_status
            self.cancel_reason = cancel_reason

            colors = {
                "Ожидание принятия": "gray",
                "Принят": "orange",
                "Готовится": "blue",
                "Готов": "green",
                "Выдан": "darkgreen",
                "Отменён": "red"
            }

            self.status_label.config(text=f"Статус: {self.status}", fg=colors.get(self.status, "black"))

            now = datetime.now()
            if self.status == "Готовится":
                remaining = self.cooking_ends - now
                minutes, seconds = divmod(remaining.seconds, 60)
                self.time_label.config(text=f"Время до готовности: {minutes} мин {seconds} сек")
            elif self.status == "Готов":
                self.time_label.config(text="Время до готовности: Готов!")
            else:
                self.time_label.config(text="---")

            if self.status == "Ожидание принятия":
                self._set_steps(["✔ Ожидание принятия"], reset=True)
            elif self.status == "Принят":
                self._set_steps([
                    "✔ Принят",
                    "🔸 Добавление ингредиентов",
                    "🔸 Выпекание",
                    "🔸 Упаковка",
                    "🔸 Готов к выдаче"
                ])
            elif self.status == "Готовится":
                self._set_steps([
                    "✔ Принят",
                    "✔ Добавление ингредиентов",
                    "✔ Выпекание",
                    "✔ Упаковка",
                    "🔸 Готов к выдаче"
                ])
            elif self.status == "Готов":
                self._set_steps([
                    "✔ Принят",
                    "✔ Добавление ингредиентов",
                    "✔ Выпекание",
                    "✔ Упаковка",
                    "✔ Готов к выдаче"
                ])

    def _set_steps(self, texts, reset=False):
        for i in range(len(self.steps_labels)):
            if i < len(texts) and texts[i]:
                self.steps_labels[i].config(text=texts[i])
            else:
                self.steps_labels[i].config(text="🔸 Этап")

    def back_to_menu(self):
        # Проверяем, нужно ли удалить заказ
        if self.status == "Отменён" or self.status == "Выдан":
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM orders WHERE id=?", (self.order_id,))
            conn.commit()
            conn.close()

        self.root.destroy()
        from ui.main_window import MainWindow
        MainWindow(tk.Tk(), client_id=self.client_id)

    def cancel_order(self):
        reason = "Клиент отменил заказ"
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status='Отменён', cancel_reason=? WHERE id=?", (reason, self.order_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("Заказ отменён", "Ваш заказ был успешно отменён.")
        self.root.destroy()
        # ✅ Импорт внутри метода
        from ui.main_window import MainWindow
        MainWindow(tk.Tk())


# ==============================
# Сотрудническая часть: изменение статуса заказа
# ==============================

class OrderStatusUpdateWindow:
    def __init__(self, root, order_id):
        self.root = root
        self.root.title("Изменение статуса заказа")
        self.root.geometry("600x500")
        center_window(self.root, 600, 500)
        self.order_id = order_id
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Выберите новый статус:", font=("Arial", 12)).pack(pady=10)
        self.status_var = tk.StringVar(value="Принят")
        statuses = ["Ожидание принятия", "Принят", "Готовится", "Готов", "Выдан", "Отменён"]
        for status in statuses:
            tk.Radiobutton(self.root, text=status, variable=self.status_var, value=status).pack()

        # Кнопка обновления статуса
        tk.Button(self.root, text="Обновить статус", command=self.update_status).pack(pady=10)

        # Кнопка "Назад к списку заказов"
        tk.Button(self.root, text="Назад к списку заказов", command=self.back_to_list).pack(pady=5)

        # Отслеживаем смену статуса
        self.status_var.trace_add("write", self.on_status_change)

    def on_status_change(self, *args):
        selected = self.status_var.get()
        if selected == "Отменён":
            self.open_cancel_reason_dialog()
        elif selected == "Готовится":
            self.open_cooking_time_dialog()

    def open_cancel_reason_dialog(self):
        """Открывает диалоговое окно для ввода причины отмены"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Причина отмены")
        dialog.geometry("400x200")
        center_window(dialog, 400, 200)

        tk.Label(dialog, text="Введите причину отмены:", font=("Arial", 12)).pack(pady=10)
        reason_entry = tk.Entry(dialog, width=50)
        reason_entry.pack(pady=10)

        def confirm_cancel():
            reason = reason_entry.get().strip()
            if not reason:
                messagebox.showwarning("Ошибка", "Введите причину отмены заказа")
                return
            self.cancel_reason = reason
            dialog.destroy()

        tk.Button(dialog, text="Подтвердить", command=confirm_cancel).pack(pady=10)

    def open_cooking_time_dialog(self):
        """Открывает диалоговое окно для ввода времени приготовления"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Время приготовления")
        dialog.geometry("400x200")
        center_window(dialog, 400, 200)

        tk.Label(dialog, text="Введите время приготовления (мин):", font=("Arial", 12)).pack(pady=10)
        time_input = tk.Spinbox(dialog, from_=5, to=60, width=5)
        time_input.pack(pady=10)

        def confirm_cooking_time():
            cook_minutes = time_input.get().strip()
            if not cook_minutes.isdigit():
                messagebox.showerror("Ошибка", "Введите корректное время приготовления")
                return
            self.cook_minutes = int(cook_minutes)
            dialog.destroy()

        tk.Button(dialog, text="Подтвердить", command=confirm_cooking_time).pack(pady=10)

    def update_status(self):
        new_status = self.status_var.get()
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            if new_status == "Готовится":
                cooking_started = datetime.now()
                cooking_ends = cooking_started + timedelta(minutes=self.cook_minutes)

                # Получаем детали заказа
                cursor.execute("SELECT details FROM orders WHERE id=?", (self.order_id,))
                row = cursor.fetchone()
                if not row or not row[0]:
                    messagebox.showerror("Ошибка", "Не найдены детали заказа")
                    return

                order_details = json.loads(row[0])

                # Вычисляем и вычитаем ингредиенты
                for item in order_details:
                    pizza_name = item["name"]
                    quantity = item["quantity"]

                    # Получаем требуемые ингредиенты для этой пиццы
                    cursor.execute('''
                        SELECT i.id, pi.required_quantity 
                        FROM pizza_ingredients pi
                        JOIN ingredients i ON pi.ingredient_id = i.id
                        WHERE pi.pizza_name = ?
                    ''', (pizza_name,))
                    ingredients_needed = cursor.fetchall()

                    for ing_id, req_qty_per_pizza in ingredients_needed:
                        total_required = req_qty_per_pizza * quantity
                        cursor.execute("UPDATE ingredients SET quantity = quantity - ? WHERE id=?", (total_required, ing_id))

                # Обновляем статус и время
                cursor.execute(
                    "UPDATE orders SET status=?, cooking_started_at=?, cooking_ends_at=? WHERE id=?",
                    (new_status, cooking_started.strftime("%Y-%m-%d %H:%M:%S"), cooking_ends.strftime("%Y-%m-%d %H:%M:%S"), self.order_id)
                )

            elif new_status == "Отменён":
                cursor.execute(
                    "UPDATE orders SET status=?, cancel_reason=? WHERE id=?",
                    (new_status, self.cancel_reason, self.order_id)
                )
            else:
                cursor.execute(
                    "UPDATE orders SET status=? WHERE id=?",
                    (new_status, self.order_id)
                )

            conn.commit()
            messagebox.showinfo("Успех", f"Статус заказа #{self.order_id} изменён на '{new_status}'")
            self.back_to_list()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить статус: {e}")
        finally:
            if conn:
                conn.close()

    def back_to_list(self):
        self.root.destroy()
        from ui.order_window import OrdersViewWindow
        OrdersViewWindow(tk.Toplevel())

class OrdersViewWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Все заказы")
        self.root.geometry("900x500")
        center_window(self.root, 900, 500)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Список всех заказов", font=("Arial", 16)).pack(pady=10)

        # Канвас с прокруткой
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.load_orders(scrollable_frame)

        tk.Button(self.root, text="Назад к меню", command=self.back_to_staff_menu).pack(pady=10)

    def load_orders(self, frame):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.id, c.name, o.status, o.total_price, o.created_at
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            ORDER BY o.created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            order_id, client_name, status, total_price, created_at = row

            order_frame = tk.Frame(frame, relief="solid", bd=1, padx=10, pady=10)
            order_frame.pack(fill="x", pady=5)

            detail_label = tk.Label(order_frame, text=f"ID: {order_id} | Клиент: {client_name} | Статус: {status} | Время: {created_at} | Сумма: {total_price} руб", justify="left")
            detail_label.pack(anchor="w")

            btn_frame = tk.Frame(order_frame)
            btn_frame.pack(pady=5)

            tk.Button(btn_frame, text="Изменить", width=10,
                      command=lambda oid=order_id: self.open_edit_window(oid)).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Удалить", width=10,
                      command=lambda oid=order_id: self.delete_order(oid, frame)).pack(side="left", padx=5)

    def open_edit_window(self, order_id):
        self.root.withdraw()
        OrderStatusUpdateWindow(tk.Toplevel(), order_id)

    def delete_order(self, order_id, frame):
        confirm = messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить заказ #{order_id}?")
        if confirm:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
            conn.commit()
            conn.close()

            # Удаляем только этот заказ из интерфейса
            frame.destroy()

            # Перезагружаем список заказов (удаленный заказ больше не отобразится)
            self.root.withdraw()
            from ui.order_window import OrdersViewWindow
            OrdersViewWindow(tk.Toplevel())
            self.root.destroy()

    def back_to_staff_menu(self):
        self.root.destroy()
        from ui.staff_window import StaffMainWindow
        StaffMainWindow(tk.Tk())