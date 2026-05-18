import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.settings import CompanySettings
from app.schemas.settings import CompanySettingsOut, CompanySettingsUpdate

router = APIRouter()

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


async def _get_or_create(db: AsyncSession) -> CompanySettings:
    result = await db.execute(select(CompanySettings).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = CompanySettings()
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


@router.get("", response_model=CompanySettingsOut)
async def get_settings(db: AsyncSession = Depends(get_db)):
    return await _get_or_create(db)


@router.patch("", response_model=CompanySettingsOut)
async def update_settings(body: CompanySettingsUpdate, db: AsyncSession = Depends(get_db)):
    settings = await _get_or_create(db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await db.commit()
    await db.refresh(settings)
    return settings


@router.post("/letterhead", response_model=CompanySettingsOut)
async def upload_letterhead(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PNG, JPG, or WebP images are accepted.")

    ext = os.path.splitext(file.filename or "letterhead.png")[1] or ".png"
    filename = f"letterhead_{uuid.uuid4().hex[:8]}{ext}"
    dest = os.path.join(UPLOADS_DIR, filename)

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    settings = await _get_or_create(db)
    # Delete old letterhead if it exists
    if settings.letterhead_path:
        old = os.path.join(UPLOADS_DIR, settings.letterhead_path)
        if os.path.exists(old):
            os.remove(old)

    settings.letterhead_path = filename
    await db.commit()
    await db.refresh(settings)
    return settings


@router.delete("/letterhead", response_model=CompanySettingsOut)
async def delete_letterhead(db: AsyncSession = Depends(get_db)):
    settings = await _get_or_create(db)
    if settings.letterhead_path:
        _remove_file(settings.letterhead_path)
        settings.letterhead_path = None
        await db.commit()
        await db.refresh(settings)
    return settings


@router.get("/letterhead/file")
async def get_letterhead_file(db: AsyncSession = Depends(get_db)):
    settings = await _get_or_create(db)
    if not settings.letterhead_path:
        raise HTTPException(status_code=404, detail="No letterhead uploaded")
    return _serve_file(settings.letterhead_path)


# ── Signature ─────────────────────────────────────────────────────────────────

@router.post("/signature", response_model=CompanySettingsOut)
async def upload_signature(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    return await _upload_asset(file, db, "signature")


@router.delete("/signature", response_model=CompanySettingsOut)
async def delete_signature(db: AsyncSession = Depends(get_db)):
    settings = await _get_or_create(db)
    if settings.signature_path:
        _remove_file(settings.signature_path)
        settings.signature_path = None
        await db.commit()
        await db.refresh(settings)
    return settings


@router.get("/signature/file")
async def get_signature_file(db: AsyncSession = Depends(get_db)):
    settings = await _get_or_create(db)
    if not settings.signature_path:
        raise HTTPException(status_code=404, detail="No signature uploaded")
    return _serve_file(settings.signature_path)


# ── Stamp ─────────────────────────────────────────────────────────────────────

@router.post("/stamp", response_model=CompanySettingsOut)
async def upload_stamp(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    return await _upload_asset(file, db, "stamp")


@router.delete("/stamp", response_model=CompanySettingsOut)
async def delete_stamp(db: AsyncSession = Depends(get_db)):
    settings = await _get_or_create(db)
    if settings.stamp_path:
        _remove_file(settings.stamp_path)
        settings.stamp_path = None
        await db.commit()
        await db.refresh(settings)
    return settings


@router.get("/stamp/file")
async def get_stamp_file(db: AsyncSession = Depends(get_db)):
    settings = await _get_or_create(db)
    if not settings.stamp_path:
        raise HTTPException(status_code=404, detail="No stamp uploaded")
    return _serve_file(settings.stamp_path)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _remove_file(filename: str) -> None:
    path = os.path.join(UPLOADS_DIR, filename)
    if os.path.exists(path):
        os.remove(path)


def _serve_file(filename: str) -> FileResponse:
    path = os.path.join(UPLOADS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


async def _upload_asset(
    file: UploadFile,
    db: AsyncSession,
    asset_type: str,   # "signature" | "stamp"
) -> "CompanySettings":
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PNG, JPG, or WebP images are accepted.")

    ext = os.path.splitext(file.filename or f"{asset_type}.png")[1] or ".png"
    filename = f"{asset_type}_{uuid.uuid4().hex[:8]}{ext}"
    dest = os.path.join(UPLOADS_DIR, filename)

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    settings = await _get_or_create(db)
    old = getattr(settings, f"{asset_type}_path", None)
    if old:
        _remove_file(old)

    setattr(settings, f"{asset_type}_path", filename)
    await db.commit()
    await db.refresh(settings)
    return settings
