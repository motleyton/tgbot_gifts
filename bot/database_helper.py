import sqlite3
from datetime import datetime
from sqlite3 import Connection

class Database:
    """Class for managing the birthday database."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Connection = self.connect_db()

    # def connect_db(self) -> Connection:
    #     """Connects to the SQLite database."""
    #     conn = sqlite3.connect(self.db_path)
    #     conn.execute('''CREATE TABLE IF NOT EXISTS birthdays
    #                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
    #                   user_id INTEGER,
    #                   name TEXT,
    #                   birthday DATE,
    #                   UNIQUE(user_id, name))''')
    #     conn.commit()
    #     return conn

    def connect_db(self) -> Connection:
        """Connects to the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''CREATE TABLE IF NOT EXISTS birthdays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        birthday DATE,
        reminders_sent INTEGER DEFAULT 0,
        reminder_active BOOLEAN DEFAULT TRUE,
        UNIQUE(user_id, name)
    );''')

        conn.commit()
        return conn


    # def add_friend(self, user_id: int, name: str, birthday: str) -> None:
    #     """Adds a birthday to the database."""
    #     try:
    #         self.conn.execute("INSERT INTO birthdays (user_id, name, birthday) VALUES (?, ?, ?)",
    #                           (user_id, name, birthday))
    #         self.conn.commit()
    #     except sqlite3.IntegrityError as e:
    #         print(f"Error adding birthday: {e}")
    #
    def add_friend(self, user_id: int, name: str, birthday: str):
        self.conn.execute("""
            INSERT INTO birthdays (user_id, name, birthday, reminders_sent, reminder_active)
            VALUES (?, ?, ?, 0, TRUE)
        """, (user_id, name, birthday))
        self.conn.commit()
        self.reset_reminders_for_all_friends()

    # def get_birthdays_today(self) -> list:
    #     """Возвращает список пользователей и их друзей, у которых сегодня день рождения."""
    #     cursor = self.conn.cursor()
    #     today = datetime.now().strftime("%m-%d")
    #     cursor.execute("SELECT user_id, name, id FROM birthdays WHERE strftime('%m-%d', birthday) = ?", (today,))
    #     return cursor.fetchall()

    def get_active_birthdays_today(self):
        """Извлекает активные записи о днях рождения на сегодня."""
        cursor = self.conn.cursor()
        today = datetime.now().strftime("%m-%d")

        cursor.execute("""
            SELECT user_id, name, id FROM birthdays
            WHERE strftime('%m-%d', birthday) = ? AND reminder_active = TRUE
        """, (today,))

        return cursor.fetchall()


    def get_birthday_info_by_id(self, id: int):
        """Извлекает информацию о дне рождения по уникальному идентификатору."""
        cursor = self.conn.cursor()
        # Выполните SQL-запрос для получения записи по id
        cursor.execute("SELECT name, birthday FROM birthdays WHERE id = ?", (id,))
        result = cursor.fetchone()

        if result:
            # Если запись найдена, возвращаем словарь с информацией
            return {'name': result[0], 'birthday': result[1]}
        else:
            # Если запись не найдена, возвращаем None
            return None


    def update_reminder_status(self, id):
        # Увеличиваем количество отправленных напоминаний
        self.conn.execute("""
            UPDATE birthdays
            SET reminders_sent = reminders_sent + 1
            WHERE id = ?
        """, (id,))

        # Деактивируем напоминание, если было отправлено 3 напоминания
        self.conn.execute("""
            UPDATE birthdays
            SET reminder_active = FALSE
            WHERE id = ? AND reminders_sent >= 3
        """, (id,))
        self.conn.commit()
    def reset_reminders_for_all_friends(self):
        """Сбрасывает счетчик напоминаний для всех друзей."""
        self.conn.execute("""
            UPDATE birthdays
            SET reminders_sent = 0, reminder_active = TRUE
        """)
        self.conn.commit()