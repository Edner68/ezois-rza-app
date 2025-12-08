"""Инструменты аудита критичных операций."""

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .models import AuditLog


async def log_audit(
    session: AsyncSession,
    action: str,
    entity_name: str,
    *,
    entity_id: Optional[int] = None,
    actor: Optional[str] = None,
    before_state: Optional[dict[str, Any]] = None,
    after_state: Optional[dict[str, Any]] = None,
    critical: bool = True,
) -> None:
    """Фиксирует запись в журнале аудита."""

    if not settings.audit_enabled:
        return

    entry = AuditLog(
        action=action,
        entity_name=entity_name,
        entity_id=entity_id,
        actor=actor or settings.default_actor,
        critical=critical,
        before_state=before_state,
        after_state=after_state,
    )
    session.add(entry)
    await session.flush()
