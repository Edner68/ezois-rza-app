"""Роутеры управления объектами ПС и РУ."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..audit import log_audit
from ..db import get_session
from ..models import Bay, Substation, Switchgear
from ..schemas import (
    BayCreate,
    BayRead,
    BayUpdate,
    SubstationCreate,
    SubstationRead,
    SubstationUpdate,
    SwitchgearCreate,
    SwitchgearRead,
    SwitchgearUpdate,
)

router = APIRouter(prefix="/objects", tags=["Объекты РЗА"])


def model_to_dict(instance: Any) -> Dict[str, Any]:
    """Сериализует ORM-модель в словарь."""

    data: Dict[str, Any] = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        if isinstance(value, datetime):
            data[column.name] = value.isoformat()
        else:
            data[column.name] = value
    return data


async def get_substation_or_404(session: AsyncSession, substation_id: int) -> Substation:
    result = await session.execute(
        select(Substation)
        .options(
            selectinload(Substation.switchgears).selectinload(Switchgear.bays),
            selectinload(Substation.documents),
        )
        .where(Substation.id == substation_id)
    )
    substation = result.scalar_one_or_none()
    if not substation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ПС не найдена")
    return substation


async def get_switchgear_or_404(session: AsyncSession, switchgear_id: int) -> Switchgear:
    result = await session.execute(
        select(Switchgear).where(Switchgear.id == switchgear_id)
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="РУ не найдено")
    return entity


@router.post("/substations", response_model=SubstationRead, status_code=status.HTTP_201_CREATED)
async def create_substation(
    payload: SubstationCreate,
    session: AsyncSession = Depends(get_session),
) -> Substation:
    """Создаёт новую ПС."""

    substation = Substation(**payload.dict())
    session.add(substation)
    await session.flush()
    await log_audit(
        session,
        action="create",
        entity_name="Substation",
        entity_id=substation.id,
        after_state=model_to_dict(substation),
    )
    await session.commit()
    await session.refresh(substation)
    return substation


@router.get("/substations", response_model=List[SubstationRead])
async def list_substations(session: AsyncSession = Depends(get_session)) -> List[Substation]:
    """Возвращает список всех ПС."""

    stmt = select(Substation).options(
        selectinload(Substation.switchgears).selectinload(Switchgear.bays),
        selectinload(Substation.documents),
    )
    result = await session.execute(stmt)
    return result.scalars().unique().all()


@router.get("/substations/{substation_id}", response_model=SubstationRead)
async def get_substation(
    substation_id: int, session: AsyncSession = Depends(get_session)
) -> Substation:
    return await get_substation_or_404(session, substation_id)


@router.put("/substations/{substation_id}", response_model=SubstationRead)
async def update_substation(
    substation_id: int,
    payload: SubstationUpdate,
    session: AsyncSession = Depends(get_session),
) -> Substation:
    substation = await get_substation_or_404(session, substation_id)
    before = model_to_dict(substation)
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(substation, field, value)
    await log_audit(
        session,
        action="update",
        entity_name="Substation",
        entity_id=substation.id,
        before_state=before,
        after_state=model_to_dict(substation),
    )
    await session.commit()
    await session.refresh(substation)
    return substation


@router.delete("/substations/{substation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_substation(
    substation_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    substation = await get_substation_or_404(session, substation_id)
    await log_audit(
        session,
        action="delete",
        entity_name="Substation",
        entity_id=substation.id,
        before_state=model_to_dict(substation),
        after_state=None,
    )
    await session.delete(substation)
    await session.commit()


# -------------------- РУ --------------------


@router.post("/switchgears", response_model=SwitchgearRead, status_code=status.HTTP_201_CREATED)
async def create_switchgear(
    payload: SwitchgearCreate,
    session: AsyncSession = Depends(get_session),
) -> Switchgear:
    await get_substation_or_404(session, payload.substation_id)
    entity = Switchgear(**payload.dict())
    session.add(entity)
    await session.flush()
    await log_audit(
        session,
        action="create",
        entity_name="Switchgear",
        entity_id=entity.id,
        after_state=model_to_dict(entity),
    )
    await session.commit()
    await session.refresh(entity)
    return entity


@router.get("/switchgears", response_model=List[SwitchgearRead])
async def list_switchgears(session: AsyncSession = Depends(get_session)) -> List[Switchgear]:
    stmt = select(Switchgear).options(selectinload(Switchgear.bays))
    result = await session.execute(stmt)
    return result.scalars().unique().all()


@router.put("/switchgears/{switchgear_id}", response_model=SwitchgearRead)
async def update_switchgear(
    switchgear_id: int,
    payload: SwitchgearUpdate,
    session: AsyncSession = Depends(get_session),
) -> Switchgear:
    entity = await get_switchgear_or_404(session, switchgear_id)
    before = model_to_dict(entity)
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(entity, field, value)
    await log_audit(
        session,
        action="update",
        entity_name="Switchgear",
        entity_id=entity.id,
        before_state=before,
        after_state=model_to_dict(entity),
    )
    await session.commit()
    await session.refresh(entity)
    return entity


@router.delete("/switchgears/{switchgear_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_switchgear(
    switchgear_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    entity = await get_switchgear_or_404(session, switchgear_id)
    await log_audit(
        session,
        action="delete",
        entity_name="Switchgear",
        entity_id=entity.id,
        before_state=model_to_dict(entity),
        after_state=None,
    )
    await session.delete(entity)
    await session.commit()


# -------------------- Ячейки --------------------


async def get_bay_or_404(session: AsyncSession, bay_id: int) -> Bay:
    result = await session.execute(select(Bay).where(Bay.id == bay_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ячейка не найдена")
    return entity


@router.post("/bays", response_model=BayRead, status_code=status.HTTP_201_CREATED)
async def create_bay(
    payload: BayCreate,
    session: AsyncSession = Depends(get_session),
) -> Bay:
    await get_switchgear_or_404(session, payload.switchgear_id)
    entity = Bay(**payload.dict())
    session.add(entity)
    await session.flush()
    await log_audit(
        session,
        action="create",
        entity_name="Bay",
        entity_id=entity.id,
        after_state=model_to_dict(entity),
    )
    await session.commit()
    await session.refresh(entity)
    return entity


@router.put("/bays/{bay_id}", response_model=BayRead)
async def update_bay(
    bay_id: int,
    payload: BayUpdate,
    session: AsyncSession = Depends(get_session),
) -> Bay:
    entity = await get_bay_or_404(session, bay_id)
    before = model_to_dict(entity)
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(entity, field, value)
    await log_audit(
        session,
        action="update",
        entity_name="Bay",
        entity_id=entity.id,
        before_state=before,
        after_state=model_to_dict(entity),
    )
    await session.commit()
    await session.refresh(entity)
    return entity


@router.delete("/bays/{bay_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bay(bay_id: int, session: AsyncSession = Depends(get_session)) -> None:
    entity = await get_bay_or_404(session, bay_id)
    await log_audit(
        session,
        action="delete",
        entity_name="Bay",
        entity_id=entity.id,
        before_state=model_to_dict(entity),
        after_state=None,
    )
    await session.delete(entity)
    await session.commit()
