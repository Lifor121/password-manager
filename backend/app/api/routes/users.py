from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select, update

from app.api.deps import CurrentSession, DbSession
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.models.session import Session as UserSession
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest

settings = get_settings()
router = APIRouter(prefix="/users", tags=["users"])

@router.put("/me/password", status_code=status.HTTP_200_OK)
@limiter.limit(settings.rate_limit_default)
async def change_password(
    request: Request,
    response: Response,
    data: ChangePasswordRequest,
    current_session: CurrentSession,
    db: DbSession,
) -> dict[str, str]:
    stmt = select(User).where(User.id == current_session.user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user or not user.check_password_hash(data.old_password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password hash",
        )

    user.update_password(
        new_auth_hash=data.new_password_hash,
        new_encrypted_vault_key=data.new_encrypted_vault_key,
    )

    revoke_stmt = (
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.id != current_session.id,
            UserSession.is_revoked.is_(False),
        )
        .values(is_revoked=True)
    )
    await db.execute(revoke_stmt)
    await db.commit()
    return {"status": "password_updated"}

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
@limiter.limit(settings.rate_limit_default)
async def delete_account(
    request: Request,
    response: Response,
    current_session: CurrentSession,
    db: DbSession,
) -> Response:
    stmt = select(User).where(User.id == current_session.user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user:
        await db.delete(user)
        await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
