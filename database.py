from pymongo import MongoClient, ASCENDING
from config import Config
import datetime

# =========================
# Mongo Connection
# =========================

client = MongoClient(Config.MONGO_URI)
db = client["chatfight"]

messages_col = db["messages"]
events_col = db["events"]  # ✅ NEW COLLECTION


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
# Date Filter Builder
# =========================

def _build_date_filter(mode):
    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    if mode == "today":
        return {"date": today}
    elif mode == "week":
        return {"date": {"$gte": week_ago}}
    return {}


# =========================
# Increment Normal Message
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
# Add Event Points
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


# =========================
# Event Leaderboard (Group)
# =========================

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
# Get User Event Points
# =========================

def get_user_event_points(user_id: int, group_id: int):
    result = events_col.find_one({
        "user_id": user_id,
        "group_id": group_id
    })

    if not result:
        return 0

    return result.get("points", 0)


# =========================
# Group Leaderboard
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
# Global Leaderboard
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
# Top Groups
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
# Total Group Messages
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
# Global Stats
# =========================

def get_global_user_count():
    return len(messages_col.distinct("user_id"))


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
