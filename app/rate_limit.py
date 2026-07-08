import time
from collections import defaultdict, deque
from fastapi import HTTPException


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.time()
        bucket = self._buckets[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Demasiadas solicitudes. Intenta nuevamente en unos minutos.",
            )
        bucket.append(now)


chat_rate_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60)
write_rate_limiter = InMemoryRateLimiter(max_requests=40, window_seconds=60)
