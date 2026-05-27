"""
Модуль для работы с базой данных SQLite
"""
import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "bot_data.db")


async def init_db():
    """Инициализация базы данных и создание таблиц"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                phone TEXT NOT NULL,
                country TEXT NOT NULL,
                status TEXT DEFAULT 'не активен',
                work_type TEXT DEFAULT 'WhatsApp',
                warmup_type TEXT DEFAULT 'Старый',
                login_type TEXT DEFAULT 'Код',
                duration_hours INTEGER DEFAULT 6,
                load_stories INTEGER DEFAULT 0,
                change_name INTEGER DEFAULT 0,
                add_avatar INTEGER DEFAULT 0,
                change_bio INTEGER DEFAULT 0,
                send_photos INTEGER DEFAULT 0,
                chat_type TEXT DEFAULT 'Личные сообщения',
                finish_at TIMESTAMP DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Добавить колонку finish_at если её нет (миграция)
        try:
            await db.execute("ALTER TABLE accounts ADD COLUMN finish_at TIMESTAMP DEFAULT NULL")
            await db.commit()
        except Exception:
            pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_hours (
                user_id INTEGER PRIMARY KEY,
                hours INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def add_account(user_id: int, username: str, phone: str, country: str) -> int:
    """Добавить аккаунт в БД, вернуть его id"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO accounts (user_id, username, phone, country) VALUES (?, ?, ?, ?)",
            (user_id, username, phone, country)
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_accounts(user_id: int) -> list:
    """Получить все аккаунты пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM accounts WHERE user_id = ? ORDER BY id DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_account(account_id: int):
    """Получить аккаунт по id"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def delete_account(account_id: int):
    """Удалить аккаунт"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        await db.commit()


async def update_account_field(account_id: int, field: str, value):
    """Обновить поле аккаунта"""
    allowed_fields = {
        "status", "work_type", "warmup_type", "login_type",
        "duration_hours", "load_stories", "change_name",
        "add_avatar", "change_bio", "send_photos", "chat_type", "finish_at"
    }
    if field not in allowed_fields:
        raise ValueError("Недопустимое поле: " + field)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE accounts SET " + field + " = ? WHERE id = ?", (value, account_id))
        await db.commit()


async def update_account_status(account_id: int, status: str):
    await update_account_field(account_id, "status", status)


async def get_accounts_finishing_soon() -> list:
    """Получить аккаунты у которых время закончилось (finish_at <= now)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM accounts WHERE status = 'работает' AND finish_at IS NOT NULL AND finish_at <= datetime('now')"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_user_hours(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT hours FROM user_hours WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0


async def set_user_hours(user_id: int, hours: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO user_hours (user_id, hours) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET hours = ?",
            (user_id, hours, hours)
        )
        await db.commit()


async def deduct_user_hours(user_id: int, hours: int) -> bool:
    """Списать часы у пользователя. Возвращает True если успешно."""
    current = await get_user_hours(user_id)
    if current < hours:
        return False
    await set_user_hours(user_id, current - hours)
    return True


async def get_all_users() -> list:
    """Получить всех уникальных пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT DISTINCT user_id FROM accounts")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
