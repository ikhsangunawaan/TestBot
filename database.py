import sqlite3

DB_NAME = "schedule.db"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS schedule (day_of_week TEXT, time TEXT, subject TEXT)"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, user_id INTEGER, remind_at INTEGER, message TEXT)"""
        )
        conn.commit()


def add_schedule(day, time, subject):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO schedule (day_of_week, time, subject) VALUES (?, ?, ?)",
            (day, time, subject),
        )
        conn.commit()


def get_schedule_for_day(day):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT time, subject FROM schedule WHERE day_of_week = ? ORDER BY time",
            (day.lower(),),
        )
        return c.fetchall()


def remove_schedule(day, time):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "DELETE FROM schedule WHERE day_of_week = ? AND time = ?",
            (day.lower(), time),
        )
        conn.commit()
        return c.rowcount


def clear_schedule(day):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM schedule WHERE day_of_week = ?", (day.lower(),))
        conn.commit()
        return c.rowcount


def add_reminder(user_id, remind_at, message):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO reminders (user_id, remind_at, message) VALUES (?, ?, ?)",
            (user_id, remind_at, message),
        )
        conn.commit()


def get_due_reminders():
    import time

    now = int(time.time())
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, user_id, message FROM reminders WHERE remind_at <= ?", (now,)
        )
        return c.fetchall()


def delete_reminder(reminder_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()


def get_user_reminders(user_id, limit=5):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, remind_at, message FROM reminders WHERE user_id = ? ORDER BY remind_at LIMIT ?",
            (user_id, limit),
        )
        return c.fetchall()


def get_all_schedules():
    """Get all schedules grouped by day"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT day_of_week, time, subject FROM schedule ORDER BY day_of_week, time"
        )
        return c.fetchall()


def search_schedule_by_subject(subject_keyword):
    """Search schedules by subject name (case-insensitive)"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT day_of_week, time, subject FROM schedule WHERE LOWER(subject) LIKE ? ORDER BY day_of_week, time",
            (f"%{subject_keyword.lower()}%",),
        )
        return c.fetchall()


def delete_schedule_by_subject(subject_keyword):
    """Delete all schedules matching subject keyword"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "DELETE FROM schedule WHERE LOWER(subject) LIKE ?",
            (f"%{subject_keyword.lower()}%",),
        )
        conn.commit()
        return c.rowcount


def delete_all_user_reminders(user_id):
    """Delete all reminders for a specific user"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
        conn.commit()
        return c.rowcount
