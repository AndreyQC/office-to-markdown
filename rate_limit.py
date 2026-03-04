import time
from collections import defaultdict
from fastapi import HTTPException, status

RATE_LIMIT = 10
RATE_WINDOW = 60

user_requests = defaultdict(list)


def check_rate_limit(username: str):
    current_time = time.time()
    requests = user_requests[username]

    requests[:] = [t for t in requests if current_time - t < RATE_WINDOW]

    if len(requests) >= RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Maximum {RATE_LIMIT} requests per minute",
                    "details": None,
                }
            },
        )

    requests.append(current_time)
