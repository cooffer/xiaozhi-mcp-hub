from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ...domain import User
from ...schemas import BootstrapStatus, LoginRequest, LoginResponse, RegisterRequest, public_dict
from ...security import verify_password
from ..deps import current_user, login_response, store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/bootstrap-status", response_model=BootstrapStatus)
async def bootstrap_status() -> BootstrapStatus:
    return BootstrapStatus(registration_open=not await store.has_admin_user())


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    user = await store.get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return login_response(user)


@router.post("/register", response_model=LoginResponse)
async def register(payload: RegisterRequest) -> LoginResponse:
    try:
        user = await store.create_first_admin(payload.email, payload.password)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="registration is closed") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="email already exists") from exc
    return login_response(user)


@router.get("/me")
async def me(user: Annotated[User, Depends(current_user)]):
    data = public_dict(user)
    data.pop("password_hash", None)
    return data


@router.post("/logout")
async def logout(_: Annotated[User, Depends(current_user)]):
    return {"ok": True}

