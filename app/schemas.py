"""Pydantic-схемы для API."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ORMModel(BaseModel):
    """Базовый класс с поддержкой ORM."""

    class Config:
        orm_mode = True


# -------------------- ПС / РУ / Ячейки --------------------


class SubstationBase(BaseModel):
    name: str = Field(..., description="Название ПС")
    code: str = Field(..., description="Кодовой идентификатор")
    voltage_class: str = Field(..., description="Класс напряжения")
    location: Optional[str] = Field(None, description="Расположение")
    description: Optional[str] = Field(None, description="Описание")


class SubstationCreate(SubstationBase):
    pass


class SubstationUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    voltage_class: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


class SwitchgearBase(BaseModel):
    substation_id: int = Field(..., description="ID ПС")
    name: str
    kind: str
    voltage_level: str
    description: Optional[str] = None


class SwitchgearCreate(SwitchgearBase):
    pass


class SwitchgearUpdate(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    voltage_level: Optional[str] = None
    description: Optional[str] = None


class BayBase(BaseModel):
    switchgear_id: int
    name: str
    function: str
    feeder: Optional[str] = None


class BayCreate(BayBase):
    pass


class BayUpdate(BaseModel):
    name: Optional[str] = None
    function: Optional[str] = None
    feeder: Optional[str] = None


class BayRead(ORMModel, BayBase):
    id: int
    created_at: datetime
    updated_at: datetime


class SwitchgearRead(ORMModel, SwitchgearBase):
    id: int
    created_at: datetime
    updated_at: datetime
    bays: List[BayRead] = Field(default_factory=list)


class SubstationRead(ORMModel, SubstationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    switchgears: List[SwitchgearRead] = Field(default_factory=list)


# -------------------- Шкафы и устройства --------------------


class RzaPanelBase(BaseModel):
    bay_id: int
    designation: str
    panel_type: str
    status: str = Field(default="draft")
    notes: Optional[str] = None


class RzaPanelCreate(RzaPanelBase):
    pass


class RzaPanelUpdate(BaseModel):
    designation: Optional[str] = None
    panel_type: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class RzaDeviceBase(BaseModel):
    panel_id: int
    name: str
    vendor: str
    model: str
    firmware_version: Optional[str] = None
    is_primary: bool = True


class RzaDeviceCreate(RzaDeviceBase):
    pass


class RzaDeviceUpdate(BaseModel):
    name: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    is_primary: Optional[bool] = None


class RzaDeviceRead(ORMModel, RzaDeviceBase):
    id: int
    created_at: datetime
    updated_at: datetime


class RzaPanelRead(ORMModel, RzaPanelBase):
    id: int
    created_at: datetime
    updated_at: datetime
    devices: List[RzaDeviceRead] = Field(default_factory=list)


# -------------------- Конфигурации и уставки --------------------


class DeviceConfigBase(BaseModel):
    device_id: int
    version_tag: str
    status: str = Field(default="draft")
    payload: dict = Field(default_factory=dict)
    comment: Optional[str] = None


class DeviceConfigCreate(DeviceConfigBase):
    pass


class DeviceConfigUpdate(BaseModel):
    version_tag: Optional[str] = None
    status: Optional[str] = None
    payload: Optional[dict] = None
    comment: Optional[str] = None


class SettingRevisionBase(BaseModel):
    config_id: int
    revision: int
    settings: dict = Field(default_factory=dict)
    is_active: bool = False
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class SettingRevisionCreate(SettingRevisionBase):
    pass


class SettingRevisionUpdate(BaseModel):
    revision: Optional[int] = None
    settings: Optional[dict] = None
    is_active: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class SettingRevisionRead(ORMModel, SettingRevisionBase):
    id: int
    created_at: datetime
    updated_at: datetime


class DeviceConfigRead(ORMModel, DeviceConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime
    revisions: List[SettingRevisionRead] = Field(default_factory=list)


# -------------------- Документы и аудит --------------------


class DocumentBase(BaseModel):
    substation_id: int
    doc_type: str
    name: str
    uri: str
    checksum: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(ORMModel, DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime


class AuditLogRead(ORMModel):
    id: int
    action: str
    entity_name: str
    entity_id: Optional[int]
    actor: str
    critical: bool
    before_state: Optional[dict]
    after_state: Optional[dict]
    created_at: datetime
