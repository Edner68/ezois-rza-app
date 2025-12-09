"""Роутеры для конфигураций устройств и уставок."""

from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..audit import log_audit
from ..db import get_session
from ..models import DeviceConfig, RzaDevice, SettingRevision
from ..schemas import (
    DeviceConfigCreate,
    DeviceConfigRead,
    DeviceConfigUpdate,
    SettingRevisionCreate,
    SettingRevisionRead,
    SettingRevisionUpdate,
)
from .routers_objects import model_to_dict

router = APIRouter(prefix="/configs", tags=["Конфигурации и уставки"])


async def get_device_or_404(session: AsyncSession, device_id: int) -> RzaDevice:
    device = await session.get(RzaDevice, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Устройство не найдено")
    return device


async def get_config_or_404(session: AsyncSession, config_id: int) -> DeviceConfig:
    stmt = select(DeviceConfig).options(selectinload(DeviceConfig.revisions)).where(
        DeviceConfig.id == config_id
    )
    result = await session.execute(stmt)
    config = result.scalar_one_or_none()
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Конфигурация не найдена")
    return config


async def get_revision_or_404(session: AsyncSession, revision_id: int) -> SettingRevision:
    revision = await session.get(SettingRevision, revision_id)
    if not revision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ревизия не найдена")
    return revision


@router.post("", response_model=DeviceConfigRead, status_code=status.HTTP_201_CREATED)
async def create_device_config(
    payload: DeviceConfigCreate,
    session: AsyncSession = Depends(get_session),
) -> DeviceConfig:
    await get_device_or_404(session, payload.device_id)
    config = DeviceConfig(**payload.dict())
    session.add(config)
    await session.flush()
    await log_audit(
        session,
        action="create",
        entity_name="DeviceConfig",
        entity_id=config.id,
        after_state=model_to_dict(config),
    )
    await session.commit()
    await session.refresh(config)
    return config


@router.get("", response_model=List[DeviceConfigRead])
async def list_configs(
    session: AsyncSession = Depends(get_session), device_id: int | None = None
) -> List[DeviceConfig]:
    stmt = select(DeviceConfig).options(selectinload(DeviceConfig.revisions))
    if device_id is not None:
        stmt = stmt.where(DeviceConfig.device_id == device_id)
    result = await session.execute(stmt)
    return result.scalars().unique().all()


@router.put("/{config_id}", response_model=DeviceConfigRead)
async def update_config(
    config_id: int,
    payload: DeviceConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> DeviceConfig:
    config = await get_config_or_404(session, config_id)
    before = model_to_dict(config)
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(config, field, value)
    await log_audit(
        session,
        action="update",
        entity_name="DeviceConfig",
        entity_id=config.id,
        before_state=before,
        after_state=model_to_dict(config),
    )
    await session.commit()
    await session.refresh(config)
    return config


# -------------------- Ревизии уставок --------------------


@router.post("/{config_id}/revisions", response_model=SettingRevisionRead, status_code=status.HTTP_201_CREATED)
async def create_revision(
    config_id: int,
    payload: SettingRevisionCreate,
    session: AsyncSession = Depends(get_session),
) -> SettingRevision:
    config = await get_config_or_404(session, config_id)
    if payload.config_id != config_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="config_id в теле должен совпадать с путём",
        )
    revision = SettingRevision(**payload.dict(exclude={"config_id"}), config_id=config.id)
    session.add(revision)
    await session.flush()

    if revision.is_active:
        await _set_active_revision(session, config, revision)

    await log_audit(
        session,
        action="create_revision",
        entity_name="SettingRevision",
        entity_id=revision.id,
        after_state=model_to_dict(revision),
    )
    await session.commit()
    await session.refresh(revision)
    return revision


@router.put("/revisions/{revision_id}", response_model=SettingRevisionRead)
async def update_revision(
    revision_id: int,
    payload: SettingRevisionUpdate,
    session: AsyncSession = Depends(get_session),
) -> SettingRevision:
    revision = await get_revision_or_404(session, revision_id)
    await session.refresh(revision, attribute_names=["config"])
    before = model_to_dict(revision)
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(revision, field, value)
    if payload.is_active is True:
        await _set_active_revision(session, revision.config, revision)
    elif payload.is_active is False:
        revision.is_active = False
    await log_audit(
        session,
        action="update_revision",
        entity_name="SettingRevision",
        entity_id=revision.id,
        before_state=before,
        after_state=model_to_dict(revision),
    )
    await session.commit()
    await session.refresh(revision)
    return revision


@router.post("/revisions/{revision_id}/activate", response_model=SettingRevisionRead)
async def activate_revision(
    revision_id: int, session: AsyncSession = Depends(get_session)
) -> SettingRevision:
    revision = await get_revision_or_404(session, revision_id)
    await session.refresh(revision, attribute_names=["config"])
    await _set_active_revision(session, revision.config, revision)
    revision.effective_from = revision.effective_from or datetime.utcnow()
    await log_audit(
        session,
        action="activate_revision",
        entity_name="SettingRevision",
        entity_id=revision.id,
        after_state=model_to_dict(revision),
    )
    await session.commit()
    await session.refresh(revision)
    return revision


async def _set_active_revision(
    session: AsyncSession, config: DeviceConfig, revision: SettingRevision
) -> None:
    """Обеспечивает единственную активную ревизию."""

    result = await session.execute(
        select(SettingRevision).where(SettingRevision.config_id == config.id)
    )
    for item in result.scalars().all():
        if item.id == revision.id:
            item.is_active = True
            if item.effective_from is None:
                item.effective_from = datetime.utcnow()
            item.effective_to = None
        else:
            if item.is_active and item.effective_to is None:
                item.effective_to = datetime.utcnow()
            item.is_active = False
    revision.is_active = True
