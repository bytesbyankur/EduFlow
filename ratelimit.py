import time
from functools import wraps
from flask import request, jsonify

# In-memory store: { (ip, endpoint): [timestamps] }
REQUEST_LOG = {}

def rate_limit(max_requests, window_seconds):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = (request.remote_addr, request.endpoint)
            now = time.time()

            timestamps = REQUEST_LOG.get(key, [])
            timestamps = [t for t in timestamps if now - t < window_seconds]

            if len(timestamps) >= max_requests:
                return jsonify({
                    "error": "Too many requests, try again later"
                }), 429

            timestamps.append(now)
            REQUEST_LOG[key] = timestamps
            return f(*args, **kwargs)
        return wrapper
    return decorator
