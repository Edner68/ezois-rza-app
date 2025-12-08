"""Роутеры формирования отчётов и аналитики."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db import get_session
from ..models import DeviceConfig, RzaDevice, RzaPanel, SettingRevision, Substation, Switchgear
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
    """Собирает историю конфигураций устройства."""

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
