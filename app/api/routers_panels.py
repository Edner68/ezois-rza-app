"""Роутеры для управления шкафами РЗА и устройствами."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..audit import log_audit
from ..db import get_session
from ..models import Bay, RzaDevice, RzaPanel
from ..schemas import (
    RzaDeviceCreate,
    RzaDeviceRead,
    RzaDeviceUpdate,
    RzaPanelCreate,
    RzaPanelRead,
    RzaPanelUpdate,
)
from .routers_objects import model_to_dict

router = APIRouter(prefix="/panels", tags=["Шкафы РЗА"])


async def get_panel_or_404(session: AsyncSession, panel_id: int) -> RzaPanel:
    stmt = select(RzaPanel).options(selectinload(RzaPanel.devices)).where(RzaPanel.id == panel_id)
    result = await session.execute(stmt)
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шкаф не найден")
    return entity


async def get_device_or_404(session: AsyncSession, device_id: int) -> RzaDevice:
    result = await session.execute(select(RzaDevice).where(RzaDevice.id == device_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Устройство не найдено")
    return entity


@router.post("", response_model=RzaPanelRead, status_code=status.HTTP_201_CREATED)
async def create_panel(
    payload: RzaPanelCreate,
    session: AsyncSession = Depends(get_session),
) -> RzaPanel:
    bay_exists = await session.get(Bay, payload.bay_id)
    if not bay_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ячейка не найдена")
    entity = RzaPanel(**payload.dict())
    session.add(entity)
    await session.flush()
    await log_audit(
        session,
        action="create",
        entity_name="RzaPanel",
        entity_id=entity.id,
        after_state=model_to_dict(entity),
    )
    await session.commit()
    await session.refresh(entity)
    return entity


@router.get("", response_model=List[RzaPanelRead])
async def list_panels(
    session: AsyncSession = Depends(get_session),
    bay_id: int | None = Query(default=None, description="Фильтр по ячейке"),
) -> List[RzaPanel]:
    stmt = select(RzaPanel).options(selectinload(RzaPanel.devices))
    if bay_id is not None:
        stmt = stmt.where(RzaPanel.bay_id == bay_id)
    result = await session.execute(stmt)
    return result.scalars().unique().all()


@router.put("/{panel_id}", response_model=RzaPanelRead)
async def update_panel(
    panel_id: int,
    payload: RzaPanelUpdate,
    session: AsyncSession = Depends(get_session),
) -> RzaPanel:
    entity = await get_panel_or_404(session, panel_id)
    before = model_to_dict(entity)
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(entity, field, value)
    await log_audit(
        session,
        action="update",
        entity_name="RzaPanel",
        entity_id=entity.id,
        before_state=before,
        after_state=model_to_dict(entity),
    )
    await session.commit()
    await session.refresh(entity)
    return entity


@router.delete("/{panel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_panel(panel_id: int, session: AsyncSession = Depends(get_session)) -> None:
    entity = await get_panel_or_404(session, panel_id)
    await log_audit(
        session,
        action="delete",
        entity_name="RzaPanel",
        entity_id=entity.id,
        before_state=model_to_dict(entity),
        after_state=None,
    )
    await session.delete(entity)
    await session.commit()


# -------------------- Устройства --------------------


@router.post("/{panel_id}/devices", response_model=RzaDeviceRead, status_code=status.HTTP_201_CREATED)
async def create_device(
    panel_id: int,
    payload: RzaDeviceCreate,
    session: AsyncSession = Depends(get_session),
) -> RzaDevice:
    panel = await get_panel_or_404(session, panel_id)
    if payload.panel_id != panel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="panel_id в теле должен совпадать с путём",
        )
    device = RzaDevice(**payload.dict(exclude={"panel_id"}), panel_id=panel.id)
    session.add(device)
    await session.flush()
    await log_audit(
        session,
        action="create",
        entity_name="RzaDevice",
        entity_id=device.id,
        after_state=model_to_dict(device),
    )
    await session.commit()
    await session.refresh(device)
    return device


@router.get("/{panel_id}/devices", response_model=List[RzaDeviceRead])
async def list_devices(panel_id: int, session: AsyncSession = Depends(get_session)) -> List[RzaDevice]:
    await get_panel_or_404(session, panel_id)
    stmt = select(RzaDevice).where(RzaDevice.panel_id == panel_id)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.put("/devices/{device_id}", response_model=RzaDeviceRead)
async def update_device(
    device_id: int,
    payload: RzaDeviceUpdate,
    session: AsyncSession = Depends(get_session),
) -> RzaDevice:
    device = await get_device_or_404(session, device_id)
    before = model_to_dict(device)
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(device, field, value)
    await log_audit(
        session,
        action="update",
        entity_name="RzaDevice",
        entity_id=device.id,
        before_state=before,
        after_state=model_to_dict(device),
    )
    await session.commit()
    await session.refresh(device)
    return device


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: int, session: AsyncSession = Depends(get_session)) -> None:
    device = await get_device_or_404(session, device_id)
    await log_audit(
        session,
        action="delete",
        entity_name="RzaDevice",
        entity_id=device.id,
        before_state=model_to_dict(device),
        after_state=None,
    )
    await session.delete(device)
    await session.commit()
