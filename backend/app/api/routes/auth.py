import base64
import hashlib
import hmac
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import EmailStr
from sqlalchemy import select

from app.api.deps import CurrentSession, DbSession
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.models.session import Session as UserSession
from app.models.user import User
from app.schemas.auth import (
    AuthParamsResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
)

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_auth)
async def register(
    request: Request,
    response: Response,
    data: RegisterRequest,
    db: DbSession,
) -> dict[str, str]:
    stmt = select(User).where(User.email == data.email)
    existing_user = (await db.execute(stmt)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user = User(
        email=data.email,
        auth_hash=data.master_password_hash,
        crypto_salt=data.crypto_salt,
        encrypted_vault_key=data.encrypted_vault_key,
    )
    db.add(user)
    await db.commit()
    return {"status": "created"}

@router.get("/params", response_model=AuthParamsResponse)
@limiter.limit(settings.rate_limit_auth)
async def get_auth_params(
    request: Request,
    response: Response,
    email: Annotated[EmailStr, Query(max_length=254)],
    db: DbSession,
) -> AuthParamsResponse:
    normalized_email = str(email).strip().lower()
    stmt = select(User.crypto_salt).where(User.email == normalized_email)
    salt = (await db.execute(stmt)).scalar_one_or_none()

    if not salt:
        fake_bytes = hmac.new(
            settings.app_name.encode("utf-8"),
            normalized_email.encode("utf-8"),
            hashlib.sha256,
        ).digest()[:16]
        salt = base64.b64encode(fake_bytes).decode("ascii")

    return AuthParamsResponse(crypto_salt=salt)

@router.post("/login", response_model=LoginResponse)
@limiter.limit(settings.rate_limit_auth)
async def login(
    request: Request,
    response: Response,
    data: LoginRequest,
    db: DbSession,
) -> LoginResponse:
    stmt = select(User).where(User.email == data.email)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user or not user.check_password_hash(data.master_password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_agent = request.headers.get("user-agent")
    new_session = UserSession.create_session(
        user_id=user.id,
        device_info=user_agent,
        ttl_hours=12,
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return LoginResponse(
        access_token=str(new_session.id),
        encrypted_vault_key=user.encrypted_vault_key,
        crypto_salt=user.crypto_salt,
    )

@router.post("/logout", status_code=status.HTTP_200_OK)
@limiter.limit(settings.rate_limit_default)
async def logout(
    request: Request,
    response: Response,
    current_session: CurrentSession,
    db: DbSession,
) -> dict[str, str]:
    current_session.revoke()
    await db.commit()
    return {"status": "logged_out"}
