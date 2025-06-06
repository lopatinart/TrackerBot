import aiosqlite
import datetime
from collections import defaultdict
from typing import Dict, List, Literal

Period = Literal["день", "неделя", "месяц"]

DB_PATH = "expenses.db"
db = aiosqlite.connect(DB_PATH)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                amount INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
        ''')
        await db.commit()

async def add_expense(user_id: int, category: str, amount: int, description: str):
    """Добавление траты базу данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO expenses (user_id, category, amount, description) VALUES (?, ?, ?, ?)",
            (user_id, category, amount, description)
        )
        await db.commit()


async def get_expenses_by_period(user_id: int, period: str):
    """Получение истории расходов за период"""
    now = datetime.datetime.now()
    today = now.date()

    # Определяем количество дней для периода
    days_count = {
        "День": 1,
        "Неделя": 7,
        "Месяц": 31
    }.get(period, 1)

    # Собираем список дат, по которым будем группировать
    date_range = [today - datetime.timedelta(days=i) for i in range(days_count)]
    min_date = min(date_range)
    min_datetime = datetime.datetime.combine(min_date, datetime.time.min)

    # Получаем все траты за нужный диапазон
    async with aiosqlite.connect("expenses.db") as db:
        async with db.execute(
            '''
            SELECT category, amount, description, created_at
            FROM expenses
            WHERE user_id = ?
              AND created_at >= ?
            ''',
            (user_id, min_datetime),
        ) as cursor:
            rows = await cursor.fetchall()

    # Готовим результат
    grouped = defaultdict(list)

    for category, amount, description, created_at in rows:
        created_at = datetime.datetime.fromisoformat(created_at)
        date_str = created_at.date().isoformat()
        if created_at.date() not in date_range:
            continue

        time_str = created_at.strftime("%H:%M")
        grouped[date_str].append([time_str, [category, amount, description or ""]])

    return dict(grouped)


async def get_stats_by_period(user_id: int, period: str) -> Dict[str, int]:
    """Получение статистики расходов по категориям за период"""
    now = datetime.datetime.now()
    today = now.date()

    days_count = {
        "День": 1,
        "Неделя": 7,
        "Месяц": 31,
        "Год": 365,
        "Все время": 365*10
    }.get(period, 1)

    min_date = today - datetime.timedelta(days=days_count)
    min_datetime = datetime.datetime.combine(min_date, datetime.time.min)

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            '''
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id = ?
              AND created_at >= ?
            GROUP BY category
            ORDER BY total DESC
            ''',
            (user_id, min_datetime if period != "Все время" else 0),
        ) as cursor:
            rows = await cursor.fetchall()

    return {category: total for category, total in rows}