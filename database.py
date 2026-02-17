from pymongo import MongoClient, ASCENDING
from config import Config
import datetime

# =========================
# Mongo Connection
# =========================

client = MongoClient(Config.MONGO_URI)
db = client["chatfight"]

messages_col = db["messages"]
events_col = db["events"]

# =========================
# Indexes
# =========================

messages_col.create_index(
    [("user_id", ASCENDING), ("group_id", ASCENDING), ("date", ASCENDING)],
    unique=True
)

messages_col.create_index("user_id")
messages_col.create_index("group_id")
messages_col.create_index("date")

events_col.create_index(
    [("user_id", ASCENDING), ("group_id", ASCENDING)],
    unique=True
)

# =========================
# 5 AM RESET LOGIC (IST)
# =========================

def _get_today_5am_reset():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)

    if now.hour < 5:
        now -= datetime.timedelta(days=1)

    return now.date().isoformat()

# =========================
# Date Filter Builder
# =========================

def _build_date_filter(mode):
    today = _get_today_5am_reset()

    today_date = datetime.datetime.strptime(today, "%Y-%m-%d").date()
    week_ago = (today_date - datetime.timedelta(days=7)).isoformat()

    if mode == "today":
        return {"date": today}
    elif mode == "week":
        return {"date": {"$gte": week_ago}}
    return {}

# =========================
# Increment Message
# =========================

def increment_message(user_id: int, group_id: int):
    today = _get_today_5am_reset()

    messages_col.update_one(
        {
            "user_id": user_id,
            "group_id": group_id,
            "date": today
        },
        {"$inc": {"count": 1}},
        upsert=True
    )

# =========================
# EVENT SYSTEM
# =========================

def add_event_points(user_id: int, group_id: int, points: int):
    events_col.update_one(
        {
            "user_id": user_id,
            "group_id": group_id
        },
        {"$inc": {"points": points}},
        upsert=True
    )

def get_event_leaderboard(group_id: int):
    pipeline = [
        {"$match": {"group_id": group_id}},
        {
            "$group": {
                "_id": "$user_id",
                "total": {"$sum": "$points"}
            }
        },
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ]

    results = list(events_col.aggregate(pipeline))
    return [(r["_id"], r["total"]) for r in results]

# =========================
# GROUP LEADERBOARD
# =========================

def get_leaderboard(group_id: int, mode="overall"):
    match_stage = {"group_id": group_id}
    match_stage.update(_build_date_filter(mode))

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$user_id",
                "total": {"$sum": "$count"}
            }
        },
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ]

    results = list(messages_col.aggregate(pipeline))
    return [(r["_id"], r["total"]) for r in results]

# =========================
# MY TOP GROUPS
# =========================

def get_user_groups_stats(user_id: int, mode="overall"):
    match_stage = {"user_id": user_id}
    match_stage.update(_build_date_filter(mode))

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$group_id",
                "total": {"$sum": "$count"}
            }
        },
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ]

    results = list(messages_col.aggregate(pipeline))
    return [(r["_id"], r["total"]) for r in results]

# =========================
# TOP GROUPS (GLOBAL)
# =========================

def get_top_groups(mode="overall"):
    match_stage = _build_date_filter(mode)

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$group_id",
                "total": {"$sum": "$count"}
            }
        },
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ]

    results = list(messages_col.aggregate(pipeline))
    return [(r["_id"], r["total"]) for r in results]

# =========================
# GLOBAL LEADERBOARD
# =========================

def get_global_leaderboard(mode="overall"):
    match_stage = _build_date_filter(mode)

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$user_id",
                "total": {"$sum": "$count"}
            }
        },
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ]

    results = list(messages_col.aggregate(pipeline))
    return [(r["_id"], r["total"]) for r in results]

# =========================
# TOTAL GROUP MESSAGES
# =========================

def get_total_group_messages(group_id: int, mode="overall"):
    match_stage = {"group_id": group_id}
    match_stage.update(_build_date_filter(mode))

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$count"}
            }
        }
    ]

    result = list(messages_col.aggregate(pipeline))
    return result[0]["total"] if result else 0

# =========================
# GLOBAL TOTAL MESSAGES (MODE BASED)
# =========================

def get_total_global_messages(mode="overall"):
    match_stage = _build_date_filter(mode)

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$count"}
            }
        }
    ]

    result = list(messages_col.aggregate(pipeline))
    return result[0]["total"] if result else 0

# =========================
# GLOBAL USER COUNT
# =========================

def get_global_user_count():
    return len(messages_col.distinct("user_id"))
