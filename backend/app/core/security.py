import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from app.core.config import settings

# Enforce explicit password length bounds
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Configure Argon2id Password Hasher
# time_cost: iterations, memory_cost: kibibytes (64MB), parallelism: threads
password_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)

# Equalize the expensive password-verification path for unknown accounts.
DUMMY_PASSWORD_HASH = password_hasher.hash(secrets.token_urlsafe(32))


class PasswordValidationError(ValueError):
    """Raised when a password violates length or format constraints."""
    pass


def validate_password_length(password: str) -> None:
    """
    Validates password length to ensure sufficient complexity and prevent
    resource-exhaustion (DoS) attacks on the hashing algorithm.
    Does not silently truncate passwords.
    """
    if not password:
        raise PasswordValidationError("Password cannot be empty.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordValidationError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise PasswordValidationError(
            f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters."
        )


def hash_password(password: str) -> str:
    """
    Hashes a password using Argon2id.
    Never stores or logs the plain-text password.
    """
    validate_password_length(password)
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against an Argon2id hash.
    Returns False on any mismatch or invalid hash without raising exceptions.
    """
    if not password or not hashed_password:
        return False
    try:
        return password_hasher.verify(hashed_password, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def get_jwt_secret_key() -> str:
    """
    Retrieves the JWT secret key from application settings.
    Ensures minimum cryptographic strength of 256 bits (32 bytes).
    """
    return settings.effective_jwt_secret_key


def create_access_token(
    subject: Union[str, uuid.UUID],
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generates a cryptographically signed JWT access token.
    Claims:
      - sub: user UUID string
      - jti: unique JWT token ID (used for revocation)
      - iat: issued-at timestamp
      - exp: expiration timestamp
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "jti": jti or secrets.token_urlsafe(32),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }

    if extra_claims:
        payload.update(extra_claims)

    encoded_jwt = jwt.encode(
        payload,
        get_jwt_secret_key(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a signed JWT access token.
    Enforces expiration check and strictly verifies against the configured algorithm.
    Raises jwt.PyJWTError on invalid, malformed, or expired token.
    """
    payload = jwt.decode(
        token,
        get_jwt_secret_key(),
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "exp", "iat", "jti"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")
    return payload
