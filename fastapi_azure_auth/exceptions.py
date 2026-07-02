from __future__ import annotations

from fastapi import HTTPException, WebSocketException, status
from starlette.requests import HTTPConnection


class InvalidRequestHttp(HTTPException):
    """HTTP exception for malformed/invalid requests"""

    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST, detail={'error': 'invalid_request', 'message': detail}
        )


class InvalidRequestWebSocket(WebSocketException):
    """WebSocket exception for malformed/invalid requests"""

    def __init__(self, detail: str) -> None:
        super().__init__(
            code=status.WS_1008_POLICY_VIOLATION, reason=str({'error': 'invalid_request', 'message': detail})
        )


class UnauthorizedHttp(HTTPException):
    """HTTP exception for authentication failures"""

    def __init__(self, detail: str, authorization_url: str | None = None, client_id: str | None = None) -> None:
        header_value = 'Bearer'
        if authorization_url:
            header_value += f', authorization_uri="{authorization_url}"'
        if client_id:
            header_value += f', client_id="{client_id}"'
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'error': 'invalid_token', 'message': detail},
            headers={'WWW-Authenticate': header_value},
        )


class UnauthorizedWebSocket(WebSocketException):
    """WebSocket exception for authentication failures"""

    def __init__(self, detail: str) -> None:
        super().__init__(
            code=status.WS_1008_POLICY_VIOLATION, reason=str({'error': 'invalid_token', 'message': detail})
        )


class ForbiddenHttp(HTTPException):
    """HTTP exception for insufficient permissions"""

    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'error': 'insufficient_scope', 'message': detail},
            headers={'WWW-Authenticate': 'Bearer'},
        )


class ForbiddenWebSocket(WebSocketException):
    """WebSocket exception for insufficient permissions"""

    def __init__(self, detail: str) -> None:
        super().__init__(
            code=status.WS_1008_POLICY_VIOLATION, reason=str({'error': 'insufficient_scope', 'message': detail})
        )


#  --- start backwards-compatible code ---
def InvalidAuth(detail: str, request: HTTPConnection) -> UnauthorizedHttp | UnauthorizedWebSocket:
    """
    Legacy factory function that maps to Unauthorized for backwards compatibility.
    Returns the correct exception based on the connection type.
    TODO: Remove in v6.0.0
    """
    if request.scope['type'] == 'http':
        # Convert the legacy format to new format
        return UnauthorizedHttp(detail)
    return UnauthorizedWebSocket(detail)


class InvalidAuthHttp(UnauthorizedHttp):
    """Legacy HTTP exception class that maps to UnauthorizedHttp
    TODO: Remove in v6.0.0
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)  # pragma: no cover


class InvalidAuthWebSocket(UnauthorizedWebSocket):
    """Legacy WebSocket exception class that maps to UnauthorizedWebSocket
    TODO: Remove in v6.0.0
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)  # pragma: no cover


#  --- end backwards-compatible code ---


def InvalidRequest(detail: str, request: HTTPConnection) -> InvalidRequestHttp | InvalidRequestWebSocket:
    """Factory function for invalid request exceptions (HTTP only, as request validation happens pre-connection)"""
    if request.scope['type'] == 'http':
        return InvalidRequestHttp(detail)
    return InvalidRequestWebSocket(detail)


def Unauthorized(
    detail: str, request: HTTPConnection, authorization_url: str | None = None, client_id: str | None = None
) -> UnauthorizedHttp | UnauthorizedWebSocket:
    """Factory function for unauthorized exceptions"""
    if request.scope['type'] == 'http':
        return UnauthorizedHttp(detail, authorization_url, client_id)
    return UnauthorizedWebSocket(detail)


def Forbidden(detail: str, request: HTTPConnection) -> ForbiddenHttp | ForbiddenWebSocket:
    """Factory function for forbidden exceptions"""
    if request.scope['type'] == 'http':
        return ForbiddenHttp(detail)
    return ForbiddenWebSocket(detail)
