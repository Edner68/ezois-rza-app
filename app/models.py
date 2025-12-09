"""ORM-модели домена РЗА."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class TimestampMixin:
    """Общий миксин с временными метками."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Substation(Base, TimestampMixin):
    """ПС (подстанция) как базовый объект сети."""

    __tablename__ = "substations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    voltage_class: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    switchgears: Mapped[List["Switchgear"]] = relationship(
        back_populates="substation", cascade="all, delete-orphan"
    )
    documents: Mapped[List["Document"]] = relationship(
        back_populates="substation", cascade="all, delete-orphan"
    )


class Switchgear(Base, TimestampMixin):
    """РУ (распределительное устройство) внутри ПС."""

    __tablename__ = "switchgears"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    substation_id: Mapped[int] = mapped_column(ForeignKey("substations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    voltage_level: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    substation: Mapped["Substation"] = relationship(back_populates="switchgears")
    bays: Mapped[List["Bay"]] = relationship(
        back_populates="switchgear", cascade="all, delete-orphan"
    )


class Bay(Base, TimestampMixin):
    """Ячейка РУ."""

    __tablename__ = "bays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    switchgear_id: Mapped[int] = mapped_column(ForeignKey("switchgears.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    function: Mapped[str] = mapped_column(String(100), nullable=False)
    feeder: Mapped[Optional[str]] = mapped_column(String(100))

    switchgear: Mapped["Switchgear"] = relationship(back_populates="bays")
    panels: Mapped[List["RzaPanel"]] = relationship(
        back_populates="bay", cascade="all, delete-orphan"
    )


class RzaPanel(Base, TimestampMixin):
    """Шкаф РЗА."""

    __tablename__ = "rza_panels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bay_id: Mapped[int] = mapped_column(ForeignKey("bays.id"), nullable=False)
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    panel_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    bay: Mapped["Bay"] = relationship(back_populates="panels")
    devices: Mapped[List["RzaDevice"]] = relationship(
        back_populates="panel", cascade="all, delete-orphan"
    )


class RzaDevice(Base, TimestampMixin):
    """Устройство РЗА внутри шкафа."""

    __tablename__ = "rza_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    panel_id: Mapped[int] = mapped_column(ForeignKey("rza_panels.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    panel: Mapped["RzaPanel"] = relationship(back_populates="devices")
    configs: Mapped[List["DeviceConfig"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )


class DeviceConfig(Base, TimestampMixin):
    """Конфигурация устройства РЗА."""

    __tablename__ = "device_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("rza_devices.id"), nullable=False)
    version_tag: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    comment: Mapped[Optional[str]] = mapped_column(Text)

    device: Mapped["RzaDevice"] = relationship(back_populates="configs")
    revisions: Mapped[List["SettingRevision"]] = relationship(
        back_populates="config", cascade="all, delete-orphan"
    )


class SettingRevision(Base, TimestampMixin):
    """Версия уставок конфигурации."""

    __tablename__ = "setting_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    config_id: Mapped[int] = mapped_column(ForeignKey("device_configs.id"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime)

    config: Mapped["DeviceConfig"] = relationship(back_populates="revisions")


class Document(Base, TimestampMixin):
    """Документ проекта (ТЗ, схема, отчёт)."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    substation_id: Mapped[int] = mapped_column(ForeignKey("substations.id"), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    uri: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(128))

    substation: Mapped["Substation"] = relationship(back_populates="documents")


class AuditLog(Base):
    """Аудит критичных операций и изменений."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    critical: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    before_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    after_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
