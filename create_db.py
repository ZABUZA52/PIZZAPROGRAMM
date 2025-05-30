# create_db.py
from database import init_db, get_connection

print("Создаём базу данных и таблицы...")
init_db()

conn = get_connection()
cursor = conn.cursor()

# Добавляем начальные данные об ингредиентах
ingredients = [
    ("Тесто", 50),
    ("Помидоры", 100),
    ("Мozzarella", 80),
    ("Базилик", 50),
    ("Грибы", 60),
    ("Оливки", 70),
    ("Перец", 90),
    ("Сыр Чеддер", 40),
    ("Сыр Гауда", 30),
    ("Сыр Пармезан", 20)
]
for name, quantity in ingredients:
    cursor.execute("INSERT OR IGNORE INTO ingredients (name, quantity) VALUES (?, ?)", (name, quantity))

# Связываем пиццы с ингредиентами
pizza_ingredients = [
    ("Пепперони", "Тесто", 1),
    ("Пепперони", "Помидоры", 5),
    ("Пепперони", "Мozzarella", 10),
    ("Пепперони", "Базилик", 2),
    ("Маргарита", "Тесто", 1),
    ("Маргарита", "Помидоры", 5),
    ("Маргарита", "Моззарелла", 10),
    ("Маргарита", "Базилик", 3),
    ("Гавайская", "Тесто", 1),
    ("Гавайская", "Помидоры", 5),
    ("Гавайская", "Моззарелла", 10),
    ("Гавайская", "Грибы", 5),
    ("Четыре сыра", "Тесто", 1),
    ("Четыре сыра", "Моззарелла", 10),
    ("Четыре сыра", "Сыр Чеддер", 5),
    ("Четыре сыра", "Сыр Гауда", 5),
    ("Четыре сыра", "Сыр Пармезан", 5)
]
for pizza_name, ingredient_name, req_qty in pizza_ingredients:
    cursor.execute("SELECT id FROM ingredients WHERE name=?", (ingredient_name,))
    result = cursor.fetchone()
    if result:
        ingredient_id = result[0]
        cursor.execute(
            "INSERT INTO pizza_ingredients (pizza_name, ingredient_id, required_quantity) VALUES (?, ?, ?)",
            (pizza_name, ingredient_id, req_qty)
        )

conn.commit()
conn.close()

print("База данных успешно создана!")