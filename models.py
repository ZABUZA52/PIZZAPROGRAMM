# models.py
import json
import sqlite3
from database import get_connection

class Client:
    def __init__(self, client_id, name, phone):
        self.id = client_id
        self.name = name
        self.phone = phone

    @staticmethod
    def get_by_phone(phone):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE phone=?", (phone,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Client(*row)
        return None

    @staticmethod
    def create(name, phone):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO clients (name, phone) VALUES (?, ?)", (name, phone))
        conn.commit()
        conn.close()

    def has_active_order(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM orders 
            WHERE client_id = ? AND status NOT IN ('Выдан', 'Отменён')
        ''', (self.id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

class Order:
    @staticmethod
    def create(client_id, total_price, details):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (client_id, total_price, details, status)
            VALUES (?, ?, ?, ?)
        ''', (client_id, total_price, json.dumps(details), "Ожидание принятия"))
        conn.commit()
        conn.close()

    @staticmethod
    def check_pizza_availability(pizza_name, quantity):
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
                return False, f"Недостаточно {ing_name}: требуется: {total_needed}, доступно: {current_qty}"

        conn.close()
        return True, "Достаточно ингредиентов"

    @staticmethod
    def get_all_orders():
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
        orders = []
        for row in rows:
            order_id, client_name, status, total_price, created_at = row
            orders.append({
                "id": order_id,
                "client_name": client_name,
                "status": status,
                "total_price": total_price,
                "created_at": created_at,
                "items": []
            })
        return orders

    @staticmethod
    def update_status(order_id, new_status, reason=None):
        conn = get_connection()
        cursor = conn.cursor()
        if reason:
            cursor.execute("UPDATE orders SET status=?, cancel_reason=? WHERE id=?", (new_status, reason, order_id))
        else:
            cursor.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(order_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
        conn.commit()
        conn.close()

class Staff:
    @staticmethod
    def authenticate(username, password):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM staff WHERE username=? AND password=?", (username, password))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    @staticmethod
    def create(username, password):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO staff (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
        return True

class Ingredient:
    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, quantity FROM ingredients")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": row[0], "name": row[1], "quantity": row[2]} for row in rows]

    @staticmethod
    def update_quantity(name, new_quantity):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE ingredients SET quantity=? WHERE name=?", (new_quantity, name))
        conn.commit()
        conn.close()