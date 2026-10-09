from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestSizeLimitMiddleware:
    """ASGI-middleware: 413 для тел больше лимита, ЕЩЁ ДО парсинга JSON.

    Защита от "прислали 50 МБ base64-картинки" — Pydantic проверит
    поля, но зачем тратить CPU на разбор такого запроса.
    """

    def __init__(self, app: ASGIApp, *, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = Headers(scope=scope).get("content-length")
        if content_length is not None:
            try:
                body_size = int(content_length)
            except ValueError:
                body_size = None
            if body_size is not None and body_size > self.max_body_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={
                        "detail": (
                            f"Request body too large. "
                            f"Max {self.max_body_bytes} bytes."
                        )
                    },
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
