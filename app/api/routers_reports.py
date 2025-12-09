"""Роутеры формирования отчётов и аналитики."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db import get_session
from ..models import (
    Bay,
    DeviceConfig,
    RzaDevice,
    RzaPanel,
    SettingRevision,
    Substation,
    Switchgear,
)
from ..schemas import SubstationRead
from .routers_objects import get_substation_or_404

router = APIRouter(prefix="/reports", tags=["Отчётность"])


@router.get("/summary")
async def report_summary(session: AsyncSession = Depends(get_session)) -> Dict[str, int]:
    """Возвращает агрегированные показатели системы."""

    counts = {}
    counts["substations"] = await _count(session, Substation)
    counts["switchgears"] = await _count(session, Switchgear)
    counts["panels"] = await _count(session, RzaPanel)
    counts["devices"] = await _count(session, RzaDevice)
    counts["active_revisions"] = await _count(
        session, SettingRevision, SettingRevision.is_active.is_(True)
    )
    return counts


async def _count(session: AsyncSession, model: Any, where_clause: Any | None = None) -> int:
    stmt = select(func.count()).select_from(model)
    if where_clause is not None:
        stmt = stmt.where(where_clause)
    result = await session.execute(stmt)
    return result.scalar_one()


@router.get("/substations/{substation_id}/structure", response_model=SubstationRead)
async def report_substation_structure(
    substation_id: int, session: AsyncSession = Depends(get_session)
) -> Substation:
    """Возвращает дерево объектов по выбранной ПС."""

    substation = await get_substation_or_404(session, substation_id)
    # ensure relationships loaded
    await session.refresh(substation)
    return substation


@router.get("/devices/{device_id}/history")
async def report_device_history(
    device_id: int, session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Собирает историю конфигураций устройства (ТЗ 4.2.4)."""

    stmt = (
        select(RzaDevice)
        .options(selectinload(RzaDevice.configs).selectinload(DeviceConfig.revisions))
        .where(RzaDevice.id == device_id)
    )
    result = await session.execute(stmt)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    configs = []
    for config in device.configs:
        configs.append(
            {
                "id": config.id,
                "version": config.version_tag,
                "status": config.status,
                "revisions": [
                    {
                        "id": rev.id,
                        "revision": rev.revision,
                        "is_active": rev.is_active,
                        "effective_from": rev.effective_from,
                        "effective_to": rev.effective_to,
                    }
                    for rev in config.revisions
                ],
            }
        )
    return {"device": device.name, "configs": configs}


@router.get("/rza-devices")
async def report_rza_devices(
    session: AsyncSession = Depends(get_session),
    vendor: str | None = Query(None, description="Фильтр по производителю"),
    model: str | None = Query(None, description="Фильтр по модели"),
    substation_id: int | None = Query(None, description="Фильтр по ПС"),
    switchgear_id: int | None = Query(None, description="Фильтр по РУ"),
    bay_id: int | None = Query(None, description="Фильтр по ячейке"),
    panel_id: int | None = Query(None, description="Фильтр по шкафу"),
    is_primary: bool | None = Query(None, description="Фильтр по признаку основного"),
) -> List[Dict[str, Any]]:
    """Возвращает перечень устройств РЗА с расширенной топологией (ТЗ 4.2.4)."""

    stmt = (
        select(
            RzaDevice,
            RzaPanel.designation.label("panel_designation"),
            Bay.name.label("bay_name"),
            Switchgear.name.label("switchgear_name"),
            Substation.name.label("substation_name"),
        )
        .join(RzaPanel, RzaPanel.id == RzaDevice.panel_id)
        .join(Bay, Bay.id == RzaPanel.bay_id)
        .join(Switchgear, Switchgear.id == Bay.switchgear_id)
        .join(Substation, Substation.id == Switchgear.substation_id)
    )
    if vendor:
        stmt = stmt.where(RzaDevice.vendor.ilike(f"%{vendor}%"))
    if model:
        stmt = stmt.where(RzaDevice.model.ilike(f"%{model}%"))
    if substation_id:
        stmt = stmt.where(Substation.id == substation_id)
    if switchgear_id:
        stmt = stmt.where(Switchgear.id == switchgear_id)
    if bay_id:
        stmt = stmt.where(Bay.id == bay_id)
    if panel_id:
        stmt = stmt.where(RzaPanel.id == panel_id)
    if is_primary is not None:
        stmt = stmt.where(RzaDevice.is_primary.is_(is_primary))
    result = await session.execute(stmt)
    devices: List[Dict[str, Any]] = []
    for row in result.fetchall():
        device: RzaDevice = row[0]
        devices.append(
            {
                "id": device.id,
                "name": device.name,
                "vendor": device.vendor,
                "model": device.model,
                "firmware_version": device.firmware_version,
                "is_primary": device.is_primary,
                "panel_id": device.panel_id,
                "panel_designation": row.panel_designation,
                "bay_name": row.bay_name,
                "switchgear_name": row.switchgear_name,
                "substation_name": row.substation_name,
            }
        )
    return devices


@router.get("/settings-history")
async def report_settings_history(
    session: AsyncSession = Depends(get_session),
    device_id: int | None = Query(None, description="Фильтр по устройству"),
    config_id: int | None = Query(None, description="Фильтр по конфигурации"),
    substation_id: int | None = Query(None, description="Фильтр по подстанции"),
    limit: int = Query(50, ge=1, le=500, description="Максимум записей"),
) -> List[Dict[str, Any]]:
    """Возвращает историю уставок с привязкой к объектам (ТЗ 4.1.2, 4.2.4)."""

    stmt = (
        select(
            SettingRevision,
            DeviceConfig.version_tag.label("version_tag"),
            RzaDevice.name.label("device_name"),
            RzaPanel.designation.label("panel_designation"),
            Bay.name.label("bay_name"),
            Switchgear.name.label("switchgear_name"),
            Substation.name.label("substation_name"),
        )
        .join(DeviceConfig, DeviceConfig.id == SettingRevision.config_id)
        .join(RzaDevice, RzaDevice.id == DeviceConfig.device_id)
        .join(RzaPanel, RzaPanel.id == RzaDevice.panel_id)
        .join(Bay, Bay.id == RzaPanel.bay_id)
        .join(Switchgear, Switchgear.id == Bay.switchgear_id)
        .join(Substation, Substation.id == Switchgear.substation_id)
        .order_by(SettingRevision.created_at.desc())
        .limit(limit)
    )
    if device_id:
        stmt = stmt.where(RzaDevice.id == device_id)
    if config_id:
        stmt = stmt.where(DeviceConfig.id == config_id)
    if substation_id:
        stmt = stmt.where(Substation.id == substation_id)

    result = await session.execute(stmt)
    history: List[Dict[str, Any]] = []
    for row in result.fetchall():
        revision: SettingRevision = row[0]
        history.append(
            {
                "revision_id": revision.id,
                "config_id": revision.config_id,
                "revision": revision.revision,
                "is_active": revision.is_active,
                "effective_from": revision.effective_from,
                "effective_to": revision.effective_to,
                "created_at": revision.created_at,
                "version_tag": row.version_tag,
                "device_name": row.device_name,
                "panel_designation": row.panel_designation,
                "bay_name": row.bay_name,
                "switchgear_name": row.switchgear_name,
                "substation_name": row.substation_name,
            }
        )
    return history
