import joblib
import os
from threading import Lock

DEFAULT_BATCH_RATE_LIMIT = int(os.environ.get("BATCH_RATE_LIMIT", 100))
DEFAULT_BATCH_RATE_LIMIT_SECONDS = int(os.environ.get("BATCH_RATE_LIMIT_SECONDS", 60))

class RateLimiter:
    def __init__(self, rate_limit, time_window):
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.timestamps = []
        self.lock = Lock()

    def acquire(self):
        # Removed rate limiting logic
        pass


def pmap(func, dictionary, n_jobs=8, verbose=True, rate_limit=None, rate_limit_seconds=None):
    # Rate limiter is initialized but does nothing
    # rate_limiter = RateLimiter(1, 1)

    def safe_func(**kwargs):
        try:
            # rate_limiter.acquire()
            return func(**kwargs)
        except Exception as e:
            print(f"Error processing {kwargs}: {e}")
            return None

    results = joblib.Parallel(n_jobs=n_jobs, verbose=verbose, prefer="processes")(
        joblib.delayed(safe_func)(**elt) for elt in dictionary
    )
    
    return results