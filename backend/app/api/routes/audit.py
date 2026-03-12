from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogOut

router = APIRouter()


@router.get('', response_model=list[AuditLogOut])
async def list_audit_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> list[AuditLogOut]:
    from app.models.enums import UserRole

    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 500))
    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(AuditLog.actor_id == current_user.id)
    rows = await db.execute(stmt)
    return [AuditLogOut.model_validate(item) for item in rows.scalars().all()]
