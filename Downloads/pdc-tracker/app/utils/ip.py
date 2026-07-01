from flask import request


def get_client_ip() -> str:
    """
    Extract real client IP. Checks X-Forwarded-For first (reverse proxy),
    takes the leftmost (client) IP from the chain.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"
