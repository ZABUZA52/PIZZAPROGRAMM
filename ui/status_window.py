import json
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime, timedelta
from tkinter import ttk
from database import get_connection
from utils import center_window

class StatusWindow:
    def __init__(self, root, order_id):
        self.root = root
        self.root.title("Статус заказа")
        self.root.geometry("600x450")
        center_window(self.root, 600, 450)
        self.order_id = order_id
        self.client_id = None  # Будет заполнено при загрузке заказа
        self.status = "Загрузка..."
        self.cancel_reason = None
        self.created_time = None
        self.cooking_ends = None
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

        # Кнопка отмены заказа (для клиента)
        self.cancel_button = tk.Button(self.root, text="Отменить заказ", fg="red", command=self.start_fight_game)
        self.cancel_button.pack(pady=10)

        # Кнопка "Назад" — она будет удалять заказ, если он отменён
        self.back_button = ttk.Button(self.root, text="Назад в меню", command=self.back_to_menu)
        self.back_button.pack(pady=10)

        # Виджет для причины отмены (используется один раз)
        self.cancellation_label = None

    def load_order_info(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT client_id, status, created_at, details, cancel_reason FROM orders WHERE id=?", (self.order_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            self.client_id, self.status, self.created_at, self.details_json, self.cancel_reason = row
            self.created_time = datetime.strptime(self.created_at, "%Y-%m-%d %H:%M:%S")
            self.cooking_ends = self.created_time + timedelta(minutes=15)
        else:
            messagebox.showinfo("Ошибка", "Заказ не найден")
            self.root.destroy()
            from ui.main_window import MainWindow
            MainWindow(tk.Tk(), client_id=self.client_id)
            return

        # Показываем состав заказа
        if self.details_json:
            try:
                self.order_details = json.loads(self.details_json)
                tk.Label(self.root, text="Ваш заказ:", font=("Arial", 14)).pack(pady=5)
                detail_text = "\n".join(
                    [f"{item['name']} x{item['quantity']}" for item in self.order_details]
                )
                tk.Label(self.root, text=detail_text, justify="left").pack(padx=20, pady=5)
                total = sum(item["price"] * item["quantity"] for item in self.order_details)
                tk.Label(self.root, text=f"Общая сумма: {total:.2f} руб", fg="blue", font=("Arial", 12)).pack(pady=5)
            except Exception as e:
                print("Ошибка при загрузке деталей заказа:", e)

    def show_cancellation_reason(self):
        """Показывает причину отмены"""
        if self.cancellation_label:
            self.cancellation_label.destroy()  # Удаляем предыдущую надпись
        reason_text = self.cancel_reason or "Без указания причины"
        self.cancellation_label = tk.Label(
            self.root,
            text=f"❌ Заказ был отменён\nПричина: {reason_text}",
            fg="red",
            font=("Arial", 12),
            justify="center"
        )
        self.cancellation_label.pack(pady=20)

    def delete_order_from_db(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id=?", (self.order_id,))
        conn.commit()
        conn.close()

    def start_auto_update(self):
        self.update_status()
        self.root.after(3000, self.start_auto_update)

    def update_status(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status, cancel_reason, cooking_started_at, cooking_ends_at FROM orders WHERE id=?", (self.order_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            new_status, self.cancel_reason, cooking_started, cooking_ends = row
            self.status = new_status
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
            if self.status == "Готовится" and cooking_started:
                cooking_started_dt = datetime.strptime(cooking_started, "%Y-%m-%d %H:%M:%S")
                cooking_ends_dt = datetime.strptime(cooking_ends, "%Y-%m-%d %H:%M:%S")
                remaining = cooking_ends_dt - now
                minutes, seconds = divmod(remaining.seconds, 60)
                self.time_label.config(text=f"Время до готовности: {minutes} мин {seconds} сек")
            elif self.status == "Готов":
                self.time_label.config(text="Время до готовности: Готов!")
            elif self.status == "Отменён":
                self.time_label.config(text="")
                self._set_steps(["❌ Заказ отменён", "", "", "", ""])
                self.show_cancellation_reason()  # Показываем причину отмены
            else:
                self.time_label.config(text="---")

            # Обновляем этапы
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
        # Удаляем заказ, если он выдан или отменён
        if self.status in ["Отменён", "Выдан"]:
            self.delete_order_from_db()

        self.root.destroy()
        from ui.main_window import MainWindow
        MainWindow(tk.Tk(), client_id=self.client_id)

    def start_fight_game(self):
        """Запускает мини-игру 'Драка' перед отменой заказа."""
        self.cancel_button.config(state=tk.DISABLED)  # Отключаем кнопку отмены
        self.fight_window = tk.Toplevel(self.root)
        self.fight_window.title("Мини-игра: Драка")
        self.fight_window.geometry("400x300")
        center_window(self.fight_window, 400, 300)

        # Переменная для хранения ID after-таймера
        self.staff_timer_id = None

        # Надписи с процентами
        self.user_percent_label = tk.Label(self.fight_window, text="Ваш прогресс: 0%", font=("Arial", 12))
        self.user_percent_label.pack(pady=5)
        self.staff_percent_label = tk.Label(self.fight_window, text="Прогресс сотрудника: 0%", font=("Arial", 12))
        self.staff_percent_label.pack(pady=5)

        # Создаём полоски прогресса
        self.user_progress = ttk.Progressbar(self.fight_window, length=300, mode='determinate', value=0)
        self.user_progress.pack(pady=10)
        self.staff_progress = ttk.Progressbar(self.fight_window, length=300, mode='determinate', value=0)
        self.staff_progress.pack(pady=10)

        # Начальные значения прогресса
        self.user_progress_value = 0
        self.staff_progress_value = 0

        # Максимальное значение прогресса
        self.max_progress = 100

        # Скорость автопрогресса сотрудника (увеличена в 5 раз)
        self.staff_speed = 30  # Проценты в секунду

        # Кнопка для увеличения прогресса пользователя
        self.attack_button = tk.Button(self.fight_window, text="Атаковать", command=self.increase_user_progress)
        self.attack_button.pack(pady=10)

        # Сообщение о победе/поражении
        self.result_label = tk.Label(self.fight_window, text="", font=("Arial", 14))
        self.result_label.pack(pady=20)

        # Запускаем автопрогресс сотрудника
        self.staff_timer_id = self.fight_window.after(1000, self.auto_increase_staff_progress)

        # Обработчик закрытия окна
        self.fight_window.protocol("WM_DELETE_WINDOW", self.on_close_fight_window)

    def increase_user_progress(self):
        """Увеличивает прогресс пользователя при нажатии кнопки."""
        if self.user_progress_value < self.max_progress:
            self.user_progress_value += 5  # Каждый клик увеличивает на 5%
            self.user_progress["value"] = self.user_progress_value
            self.update_user_percent_label()
            self.check_game_over()

    def auto_increase_staff_progress(self):
        """Автоматически увеличивает прогресс сотрудника."""
        if self.staff_progress_value < self.max_progress:
            self.staff_progress_value += self.staff_speed  # Автоувеличение на 15% в секунду
            self.staff_progress["value"] = self.staff_progress_value
            self.update_staff_percent_label()
            self.check_game_over()
            self.staff_timer_id = self.fight_window.after(1000, self.auto_increase_staff_progress)
        else:
            self.check_game_over()

    def update_user_percent_label(self):
        """Обновляет текст метки с процентом пользователя"""
        self.user_percent_label.config(text=f"Ваш прогресс: {int(self.user_progress_value)}%")

    def update_staff_percent_label(self):
        """Обновляет текст метки с процентом сотрудника"""
        self.staff_percent_label.config(text=f"Прогресс сотрудника: {int(self.staff_progress_value)}%")

    def check_game_over(self):
        """Проверяет, закончилась ли игра."""
        if self.user_progress_value >= self.max_progress:
            self.result_label.config(text="🎉 Вы победили! Заказ отменён.", fg="green")
            self.end_game(cancel_order=True)
        elif self.staff_progress_value >= self.max_progress:
            self.result_label.config(text="❌ Вы проиграли. Заказ не отменён.", fg="red")
            self.end_game(cancel_order=False)

    def end_game(self, cancel_order):
        """Завершает игру и выполняет действия."""
        self.attack_button.config(state=tk.DISABLED)
        if self.staff_timer_id:
            self.fight_window.after_cancel(self.staff_timer_id)
            self.staff_timer_id = None
        self.fight_window.after(2000, self.fight_window.destroy)  # Закрываем через 2 секунды
        if cancel_order:
            self.cancel_order()  # Отменяем заказ
        else:
            self.root.quit()  # Завершаем приложение

    def on_close_fight_window(self):
        """Обработчик закрытия окна игры."""
        if self.staff_timer_id:
            self.fight_window.after_cancel(self.staff_timer_id)
            self.staff_timer_id = None
        self.root.quit()  # Если пользователь закроет окно, завершаем приложение

    def cancel_order(self):
        """Отменяет заказ после успешной игры."""
        reason = "Клиент отменил заказ"
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status='Отменён', cancel_reason=? WHERE id=?", (reason, self.order_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("Заказ отменён", "Ваш заказ был успешно отменён.")
        self.root.destroy()
        from ui.main_window import MainWindow
        MainWindow(tk.Tk(), client_id=self.client_id)