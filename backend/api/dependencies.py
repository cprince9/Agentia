import uuid
from typing import AsyncGenerator, Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from redis.asyncio import Redis, from_url as redis_from_url
from jose import jwt, JWTError

from ..config.settings import Settings, get_settings
from ..services.event_bus import EventBus

# Global engine and session factory caches
_async_engine = None
_async_session_factory = None
_redis_client: Optional[Redis] = None


def get_engine():
    global _async_engine, _async_session_factory
    if _async_engine is None:
        settings = get_settings()
        _async_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        _async_session_factory = async_sessionmaker(
            _async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_engine


def get_session_factory():
    if _async_session_factory is None:
        get_engine()
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session per request."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[Redis, None]:
    """Dependency for async Redis connection pool."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis_from_url(settings.REDIS_URL, decode_responses=False)
    yield _redis_client


async def get_event_bus(redis: Redis = Depends(get_redis)) -> EventBus:
    """Dependency injecting EventBus instance."""
    return EventBus(redis=redis)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings),
) -> Optional[dict]:
    """
    Validate optional JWT Bearer token.
    Returns user payload dictionary or None if unauthenticated.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
