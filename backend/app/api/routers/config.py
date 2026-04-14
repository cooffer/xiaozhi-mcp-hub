from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ...config_import import import_config, load_payload
from ...domain import User
from ...schemas import public_dict
from ..deps import bridge_manager, connectors, current_user, require_admin, store

router = APIRouter(prefix="/config", tags=["config"])


@router.post("/import")
async def config_import(
    user: Annotated[User, Depends(require_admin)],
    file: UploadFile | None = File(default=None),
    raw: str | None = Form(default=None),
):
    text = (await file.read()).decode("utf-8") if file is not None else raw or ""
    payload = load_payload(text)
    result = await import_config(payload, store, connectors, created_by=user.id)
    await bridge_manager.sync()
    return result


@router.get("/export")
async def config_export(_: Annotated[User, Depends(current_user)]):
    return await store.export_config()


@router.get("/versions")
async def config_versions(_: Annotated[User, Depends(current_user)]):
    return [public_dict(item) for item in await store.list_config_versions()]

