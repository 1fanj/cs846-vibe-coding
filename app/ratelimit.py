from fastapi import Request, HTTPException, Depends
from typing import Callable
import time
import threading
from app import auth

_lock = threading.Lock()
_store: dict[str, list[float]] = {}


def rate_limit(max_requests: int = 3, window_seconds: int = 60) -> Callable:
    def dependency(request: Request, current_user=Depends(auth.get_current_user)):
        # current_user will be resolved by FastAPI when this dependency is used
        if current_user is not None:
            key = f"user:{current_user.username}"
        else:
            # fallback to IP-based key
            client = request.client.host if request.client else "anon"
            key = f"ip:{client}"

        now = time.time()
        with _lock:
            times = _store.get(key, [])
            # drop old timestamps
            cutoff = now - window_seconds
            times = [t for t in times if t > cutoff]
            if len(times) >= max_requests:
                raise HTTPException(status_code=429, detail="rate limit exceeded")
            times.append(now)
            _store[key] = times

    return dependency


def _clear_store_for_tests():
    with _lock:
        _store.clear()
