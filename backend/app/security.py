from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256${_b64url(salt)}${_b64url(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt_b64, digest_b64 = password_hash.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = _b64url_decode(salt_b64)
        expected = _b64url_decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_token(payload: dict[str, Any], secret: str, ttl_seconds: int = 86_400) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    body = dict(payload)
    body["exp"] = int(time.time()) + ttl_seconds
    head = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    data = _b64url(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), f"{head}.{data}".encode("ascii"), hashlib.sha256).digest()
    return f"{head}.{data}.{_b64url(signature)}"


def decode_token(token: str, secret: str) -> dict[str, Any]:
    head, data, signature = token.split(".", 2)
    expected = hmac.new(secret.encode("utf-8"), f"{head}.{data}".encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_decode(signature), expected):
        raise ValueError("invalid token signature")
    payload = json.loads(_b64url_decode(data))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("token expired")
    return payload


def mask_secret(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) <= 6:
        return "***"
    return f"{value[:2]}***{value[-2:]}"
