def get_user_groups_stats(user_id: int, mode="overall"):
    import datetime

    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    match_stage = {"user_id": user_id}

    if mode == "today":
        match_stage["date"] = today
    elif mode == "week":
        match_stage["date"] = {"$gte": week_ago}

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$group_id",
                "total": {"$sum": "$count"}
            }
        },
        {"$sort": {"total": -1}}
    ]

    results = list(messages_col.aggregate(pipeline))
    return [(r["_id"], r["total"]) for r in results]
