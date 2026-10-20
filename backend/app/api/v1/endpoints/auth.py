from datetime import timedelta
import logging
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import DUMMY_PASSWORD_HASH, create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutResponse, TokenResponse
from app.schemas.user import UserCreate, UserRead

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    email = str(payload.email).casefold()
    try:
        if db.scalar(select(User.id).where(User.email == email)) is not None:
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from None
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database failure during account registration")
        raise HTTPException(status_code=500, detail="Unable to create account.") from None


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.strip().casefold()
    try:
        user = db.scalar(select(User).where(User.email == email))
    except SQLAlchemyError:
        logger.exception("Database failure during login")
        raise HTTPException(status_code=500, detail="Unable to authenticate at this time.") from None
    password_valid = verify_password(payload.password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    if user is None or not user.is_active or not password_valid:
        raise HTTPException(status_code=401, detail="Invalid email or password.", headers={"WWW-Authenticate": "Bearer"})
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    try:
        token = create_access_token(user.id, expires_delta=timedelta(seconds=expires_in))
    except (RuntimeError, ValueError, jwt.PyJWTError):
        logger.exception("Unable to create access token")
        raise HTTPException(status_code=500, detail="Unable to authenticate at this time.") from None
    return TokenResponse(access_token=token, expires_in=expires_in, user=user)


@router.get("/me", response_model=UserRead)
def current_user(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout", response_model=LogoutResponse)
def logout(_: User = Depends(get_current_user)) -> LogoutResponse:
    # Access tokens are stateless; clients must discard them. They remain valid until expiry.
    return LogoutResponse(message="Signed out on this device. The access token remains valid until it expires.")