"""Single-operator access control for the local demo; not multi-tenant identity."""
import asyncio
import tempfile
import hmac
import time
from collections import deque

from starlette.responses import JSONResponse

from app.core.config import settings


class AccessControlMiddleware:
    def __init__(self, app):
        self.app = app
        self.attempts = {"failed": deque(), "read": deque(), "write": deque()}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] == "/health":
            return await self.app(scope, receive, send)
        if scope["method"] == "OPTIONS":
            return await self.app(scope, receive, send)
        token = settings.api_access_token
        if len(token) < 32 or token.lower().startswith(("change", "replace", "your_")):
            return await JSONResponse({"detail": "Access is not configured."}, 503)(scope, receive, send)
        headers = dict(scope["headers"])
        supplied = headers.get(b"authorization", b"")
        authorized = hmac.compare_digest(supplied, ("Bearer " + token).encode())
        group = "failed" if not authorized else ("read" if scope["method"] == "GET" else "write")
        bucket = self.attempts[group]
        now = time.monotonic()
        while bucket and bucket[0] <= now - 60:
            bucket.popleft()
        # Fixed buckets bound memory and do not trust spoofable forwarded IPs.
        limit = {"failed": 30, "read": 300, "write": 10}[group]
        if len(bucket) >= limit:
            return await JSONResponse({"detail": "Too many requests. Try again shortly."}, 429,
                                      headers={"Retry-After": "60"})(scope, receive, send)
        bucket.append(now)
        if not authorized:
            return await JSONResponse({"detail": "Access token required."}, 401,
                                      headers={"WWW-Authenticate": "Bearer"})(scope, receive, send)
        if scope["method"] == "POST" and scope["path"].rstrip("/") == "/api/uploads" and not settings.allow_uploads:
            return await JSONResponse({"detail": "Uploads are disabled."}, 403)(scope, receive, send)

        async def private_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + [(b"cache-control", b"no-store")]
            await send(message)
        if scope["method"] in {"POST", "PUT", "PATCH"}:
            maximum = (settings.max_upload_mb * 1024 * 1024 + 65536) if scope["path"].rstrip("/") == "/api/uploads" else 65536
            with tempfile.SpooledTemporaryFile(max_size=1024 * 1024) as body:
                size = 0
                deadline = time.monotonic() + 30
                while True:
                    try:
                        message = await asyncio.wait_for(receive(), max(.001, deadline - time.monotonic()))
                    except TimeoutError:
                        return await JSONResponse({"detail": "Request body timed out."}, 408)(scope, receive, send)
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    size += len(chunk)
                    if size > maximum:
                        return await JSONResponse({"detail": "Request body is too large."}, 413)(scope, receive, send)
                    body.write(chunk)
                    if not message.get("more_body", False):
                        break
                body.seek(0)
                async def buffered_receive():
                    chunk = body.read(65536)
                    return {"type": "http.request", "body": chunk, "more_body": body.tell() < size}
                return await self.app(scope, buffered_receive, private_send)
        await self.app(scope, receive, private_send)
