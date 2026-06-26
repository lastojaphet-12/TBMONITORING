import secrets
from datetime import timedelta, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from sqlalchemy import select

from backend.config import settings
from backend.database.postgres import SessionLocal
from backend.main_dependencies import get_current_user_payload, require_role
from backend.models.user import User, Role, PasswordResetToken

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_exp_minutes)
    to_encode = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=6, max_length=255)
    role: Role


class MeResponse(BaseModel):
    id: int
    username: str
    role: Role
    status: str
    created_at: datetime


class PasswordResetRequest(BaseModel):
    username: str


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=255)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    stmt = select(User).where(User.username == form_data.username)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db=Depends(get_db)):
    existing = db.execute(select(User).where(User.username == req.username)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "username": user.username, "role": user.role}


@router.get("/me", response_model=MeResponse)
def me(payload=Depends(get_current_user_payload), db=Depends(get_db)):
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return MeResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
    )


@router.get("/users", dependencies=[Depends(require_role("provider"))])
def list_users(role: str | None = None, db=Depends(get_db)):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    users = db.execute(stmt).scalars().all()
    return {
        "users": [
            {"id": u.id, "username": u.username, "role": u.role.value}
            for u in users
        ]
    }

@router.post("/password-reset/request")
def request_password_reset(req: PasswordResetRequest, db=Depends(get_db)):
    user = db.execute(select(User).where(User.username == req.username)).scalar_one_or_none()
    # Avoid user enumeration
    if not user:
        return {"status": "ok"}

    token_value = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=30)

    prt = PasswordResetToken(
        token=token_value,
        user_id=user.id,
        expires_at=expires_at,
        used=False,
    )
    db.add(prt)
    db.commit()

    # For this reference implementation we return the token directly.
    # In production, it should be emailed.
    return {"status": "ok", "token": token_value}


@router.post("/password-reset/confirm")
def confirm_password_reset(req: PasswordResetConfirmRequest, db=Depends(get_db)):
    prt = db.execute(select(PasswordResetToken).where(PasswordResetToken.token == req.token)).scalar_one_or_none()
    if not prt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    if prt.used or prt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = db.execute(select(User).where(User.id == prt.user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user.password_hash = hash_password(req.new_password)
    prt.used = True

    db.add(user)
    db.add(prt)
    db.commit()

    return {"status": "ok"}


