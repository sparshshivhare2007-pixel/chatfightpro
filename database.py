from pymongo import MongoClient, ASCENDING
from config import Config
import datetime

# =========================
# Mongo Connection
# =========================

client = MongoClient(Config.MONGO_URI)
db = client["chatfight"]
messages_col = db["messages"]

# =========================
# Indexes (Performance Boost)
# =========================

messages_col.create_index(
    [("user_id", ASCENDING), ("group_id", ASCENDING), ("date", ASCENDING)],
    unique=True
)

messages_col.create_index("user_id")
messages_col.create_index("group_id")
messages_col.create_index("date")

# =========================
# Increment Message
# =========================

def increment_message(user_id: int, group_id: int):
    today = datetime.date.today().isoformat()

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
# Group Leaderboard
# =========================

def get_leaderboard(group_id: int, mode="overall"):
    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    match_stage = {"group_id": group_id}

    if mode == "today":
        match_stage["date"] = today
    elif mode == "week":
        match_stage["date"] = {"$gte": week_ago}

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
# Global Leaderboard
# =========================

def get_global_leaderboard(mode="overall"):
    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    match_stage = {}

    if mode == "today":
        match_stage["date"] = today
    elif mode == "week":
        match_stage["date"] = {"$gte": week_ago}

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

    total_messages = sum(r["total"] for r in results)

    return [(r["_id"], r["total"]) for r in results], total_messages

# =========================
# User Stats
# =========================

def get_user_overall_stats(user_id: int):
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": None,
                "messages": {"$sum": "$count"},
                "groups": {"$addToSet": "$group_id"}
            }
        }
    ]

    result = list(messages_col.aggregate(pipeline))
    if not result:
        return 0, 0

    return result[0]["messages"], len(result[0]["groups"])


def get_user_today_stats(user_id: int):
    today = datetime.date.today().isoformat()

    pipeline = [
        {"$match": {"user_id": user_id, "date": today}},
        {
            "$group": {
                "_id": None,
                "messages": {"$sum": "$count"},
                "groups": {"$addToSet": "$group_id"}
            }
        }
    ]

    result = list(messages_col.aggregate(pipeline))
    if not result:
        return 0, 0

    return result[0]["messages"], len(result[0]["groups"])


def get_user_week_stats(user_id: int):
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    pipeline = [
        {"$match": {"user_id": user_id, "date": {"$gte": week_ago}}},
        {
            "$group": {
                "_id": None,
                "messages": {"$sum": "$count"},
                "groups": {"$addToSet": "$group_id"}
            }
        }
    ]

    result = list(messages_col.aggregate(pipeline))
    if not result:
        return 0, 0

    return result[0]["messages"], len(result[0]["groups"])

# =========================
# Global Stats
# =========================

def get_global_user_count():
    return len(messages_col.distinct("user_id"))

def get_user_global_rank(user_id: int):
    pipeline = [
        {
            "$group": {
                "_id": "$user_id",
                "total": {"$sum": "$count"}
            }
        },
        {"$sort": {"total": -1}}
    ]

    results = list(messages_col.aggregate(pipeline))

    for index, user in enumerate(results, start=1):
        if user["_id"] == user_id:
            return index

    return None

def get_total_global_messages():
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$count"}
            }
        }
    ]

    result = list(messages_col.aggregate(pipeline))
    return result[0]["total"] if result else 0
