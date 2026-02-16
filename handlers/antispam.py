import time
from collections import defaultdict

# user_id → list of timestamps
user_message_times = defaultdict(list)

# user_id → block_until_timestamp
blocked_users = {}

SPAM_LIMIT = 3          # 3 messages
TIME_WINDOW = 1         # in 2 seconds
BLOCK_DURATION = 600    # 10 minutes (600 sec)


def check_spam(user_id: int) -> bool:
    """
    Returns True if user is blocked
    """

    now = time.time()

    # Check if user already blocked
    if user_id in blocked_users:
        if now < blocked_users[user_id]:
            return True
        else:
            del blocked_users[user_id]

    # Track timestamps
    user_message_times[user_id].append(now)

    # Keep only recent timestamps
    user_message_times[user_id] = [
        t for t in user_message_times[user_id]
        if now - t <= TIME_WINDOW
    ]

    # If spam detected
    if len(user_message_times[user_id]) >= SPAM_LIMIT:
        blocked_users[user_id] = now + BLOCK_DURATION
        user_message_times[user_id].clear()
        return True

    return False


def is_blocked(user_id: int) -> bool:
    now = time.time()

    if user_id in blocked_users:
        if now < blocked_users[user_id]:
            return True
        else:
            del blocked_users[user_id]

    return False
