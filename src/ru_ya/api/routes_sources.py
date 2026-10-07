from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, File, Form, UploadFile

from ru_ya.ingest.user_upload import AuthorityPreference, process_user_text

router = APIRouter(prefix="/user-sources", tags=["user-sources"])

# In-memory registry for the skeleton (replace with DB + object store)
_USER_SOURCES: dict[str, dict[str, Any]] = {}


@router.post("")
async def upload_user_source(
    file: UploadFile = File(...),
    owner_user_id: str = Form("anonymous"),
    authority_preference: str = Form("informational"),
):
    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="ignore")

    pref = AuthorityPreference(authority_preference)
    object_key = f"user/{owner_user_id}/{uuid4()}-{file.filename}"
    draft = process_user_text(
        owner_user_id=owner_user_id,
        filename=file.filename or "upload.txt",
        object_key=object_key,
        text=text,
        page_count=max(1, text.count("\f") + 1),
        authority_preference=pref,
    )
    record = {
        "id": str(uuid4()),
        "owner_user_id": draft.owner_user_id,
        "filename": draft.filename,
        "object_key": draft.object_key,
        "status": draft.status.value,
        "authority_preference": draft.authority_preference.value,
        "page_count": draft.page_count,
        "chunk_count": len(draft.chunks),
        "error_message": draft.error_message,
    }
    _USER_SOURCES[record["id"]] = record
    return record


@router.get("")
def list_user_sources(owner_user_id: str = "anonymous"):
    return [
        s for s in _USER_SOURCES.values() if s["owner_user_id"] == owner_user_id
    ]
