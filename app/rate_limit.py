import threading
import time
from collections import deque
from fastapi import HTTPException


class InMemoryRateLimiter:
    """
    Rate limiter de ventana deslizante en memoria.
    Thread-safe y con límite de buckets para evitar memory leaks
    cuando hay muchos user_ids distintos.
    """

    def __init__(self, max_requests: int, window_seconds: int, max_buckets: int = 2000) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_buckets = max_buckets
        self._buckets: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            # Evitar crecimiento ilimitado del diccionario de buckets
            if key not in self._buckets:
                if len(self._buckets) >= self.max_buckets:
                    # Eliminar la entrada más antigua
                    oldest_key = next(iter(self._buckets))
                    del self._buckets[oldest_key]
                self._buckets[key] = deque()

            bucket = self._buckets[key]

            # Descartar timestamps fuera de la ventana
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
