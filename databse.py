import sqlite3
import datetime
from config import Config

conn = sqlite3.connect(Config.DATABASE_URL, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id INTEGER,
    group_id INTEGER,
    date TEXT,
    count INTEGER DEFAULT 1,
    PRIMARY KEY (user_id, group_id, date)
)
""")

conn.commit()


def increment_message(user_id, group_id):
    today = datetime.date.today().isoformat()

    cursor.execute("""
    INSERT INTO messages (user_id, group_id, date, count)
    VALUES (?, ?, ?, 1)
    ON CONFLICT(user_id, group_id, date)
    DO UPDATE SET count = count + 1
    """, (user_id, group_id, today))

    conn.commit()


def get_leaderboard(group_id, mode="overall"):
    if mode == "today":
        today = datetime.date.today().isoformat()
        cursor.execute("""
        SELECT user_id, SUM(count) as total
        FROM messages
        WHERE group_id=? AND date=?
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT 10
        """, (group_id, today))

    elif mode == "week":
        week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        cursor.execute("""
        SELECT user_id, SUM(count) as total
        FROM messages
        WHERE group_id=? AND date>=?
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT 10
        """, (group_id, week_ago))

    else:  # overall
        cursor.execute("""
        SELECT user_id, SUM(count) as total
        FROM messages
        WHERE group_id=?
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT 10
        """, (group_id,))

    return cursor.fetchall()
