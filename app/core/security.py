import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

import bcrypt
import jwt
from pydantic import BaseModel

from app.core import messages
from app.core.config import get_settings

TokenType = Literal["access", "refresh"]


class TokenPayload(BaseModel):
    sub: str
    type: TokenType
    jti: str
    exp: datetime

    @property
    def user_id(self) -> uuid.UUID:
        return uuid.UUID(self.sub)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(
    user_id: uuid.UUID, token_type: TokenType, expires_delta: timedelta
) -> tuple[str, TokenPayload]:
    settings = get_settings()
    payload = TokenPayload(
        sub=str(user_id),
        type=token_type,
        jti=str(uuid.uuid4()),
        exp=datetime.now(UTC) + expires_delta,
    )
    token = jwt.encode(payload.model_dump(), settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, payload


def create_access_token(user_id: uuid.UUID) -> tuple[str, TokenPayload]:
    minutes = get_settings().access_token_expire_minutes
    return create_token(user_id, "access", timedelta(minutes=minutes))


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, TokenPayload]:
    days = get_settings().refresh_token_expire_days
    return create_token(user_id, "refresh", timedelta(days=days))


def decode_token(token: str, expected_type: TokenType) -> TokenPayload:
    settings = get_settings()
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise ValueError(messages.TOKEN_EXPIRED) from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError(messages.TOKEN_INVALID) from exc
    payload = TokenPayload.model_validate(data)
    if payload.type != expected_type:
        raise ValueError(
            messages.TOKEN_WRONG_TYPE.format(expected=expected_type, actual=payload.type)
        )
    return payload
