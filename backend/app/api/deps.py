from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.session import Session as UserSession

security = HTTPBearer(auto_error=False)

# Готовый тип для инжекции сессии БД (без предупреждений Ruff B008)
DbSession = Annotated[AsyncSession, Depends(get_async_session)]

async def get_current_session(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: DbSession,
) -> UserSession:
    """Проверка Bearer-сессии и скользящее продление TTL (12 ч)."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    try:
        session_uuid = UUID(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    stmt = select(UserSession).where(UserSession.id == str(session_uuid))
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session or not session.is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    session.renew(ttl_hours=12)
    await db.commit()
    return session

# Готовый тип для инжекции авторизованной сессии пользователя
CurrentSession = Annotated[UserSession, Depends(get_current_session)]
