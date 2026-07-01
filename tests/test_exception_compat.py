"""
This module tests the exception handling and backwards compatibility of the exceptions module, introduced in
issue https://github.com/vibber-ai/fastapi-azure-auth/issues/229.
TODO: Remove this test module in v6.0.0
"""
import pytest
from fastapi import HTTPException, WebSocketException, status

from fastapi_azure_auth.exceptions import (
    InvalidAuth,
    InvalidAuthHttp,
    InvalidAuthWebSocket,
    UnauthorizedHttp,
    UnauthorizedWebSocket,
)


def test_invalid_auth_backwards_compatibility():
    """Test that InvalidAuth maps to correct exceptions and maintains format"""
    # Mock HTTP request scope
    http_conn = type('HTTPConnection', (), {'scope': {'type': 'http'}})()

    # Mock WebSocket scope
    ws_conn = type('HTTPConnection', (), {'scope': {'type': 'websocket'}})()

    # Test HTTP path
    http_exc = InvalidAuth("test message", http_conn)
    assert isinstance(http_exc, UnauthorizedHttp)
    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == status.HTTP_401_UNAUTHORIZED
    assert http_exc.detail == {"error": "invalid_token", "message": "test message"}

    # Test WebSocket path
    ws_exc = InvalidAuth("test message", ws_conn)
    assert isinstance(ws_exc, UnauthorizedWebSocket)
    assert isinstance(ws_exc, WebSocketException)
    assert ws_exc.code == status.WS_1008_POLICY_VIOLATION
    assert ws_exc.reason == str({"error": "invalid_token", "message": "test message"})


def test_legacy_exception_catching():
    """Test that old exception catching patterns still work"""
    # Test HTTP exceptions
    http_conn = type('HTTPConnection', (), {'scope': {'type': 'http'}})()

    with pytest.raises((InvalidAuthHttp, UnauthorizedHttp)) as exc_info:
        raise InvalidAuth("test message", http_conn)

    assert isinstance(exc_info.value, UnauthorizedHttp)
    assert exc_info.value.detail == {"error": "invalid_token", "message": "test message"}

    # Test WebSocket exceptions
    ws_conn = type('HTTPConnection', (), {'scope': {'type': 'websocket'}})()

    with pytest.raises((InvalidAuthWebSocket, UnauthorizedWebSocket)) as exc_info:
        raise InvalidAuth("test message", ws_conn)

    assert isinstance(exc_info.value, UnauthorizedWebSocket)
    assert exc_info.value.reason == str({"error": "invalid_token", "message": "test message"})


def test_new_exceptions_can_be_caught_as_legacy():
    """Test that new exceptions can be caught with legacy catch blocks"""
    with pytest.raises((InvalidAuthHttp, UnauthorizedHttp)) as exc_info:
        raise UnauthorizedHttp("test message")

    assert exc_info.value.detail == {"error": "invalid_token", "message": "test message"}

    with pytest.raises((InvalidAuthWebSocket, UnauthorizedWebSocket)) as exc_info:
        raise UnauthorizedWebSocket("test message")

    assert exc_info.value.reason == str({"error": "invalid_token", "message": "test message"})
