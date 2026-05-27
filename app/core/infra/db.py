"""Async MySQL database helpers."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Optional, ParamSpec, TypeVar
from urllib.parse import quote_plus

from config.settings import AppConfig, get_app_config
from core.http.exceptions import AppHTTPException
from loguru import logger
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

P = ParamSpec("P")
T = TypeVar("T")

_GLOBAL_DB: SessionManager | None = None


def db_retry(
    max_retries: int = 3,
    delay: float = 1.0,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Retry transient database connection failures."""

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: Exception | None = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (OperationalError, InterfaceError) as exc:
                    last_error = exc
                    logger.warning(
                        "Database operation failed; retry {}/{}: {}",
                        attempt + 1,
                        max_retries,
                        exc,
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)

            raise AppHTTPException(
                detail="Database operation failed",
                error_detail=str(last_error),
            )

        return wrapper

    return decorator


class SessionManager:
    """Async MySQL session manager."""

    def __init__(self, cfg: AppConfig | None = None) -> None:
        self.cfg = cfg or get_app_config()
        self._lock = asyncio.Lock()
        self._engine: AsyncEngine | None = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

        self.mysql_config = {
            "host": self.cfg.mysql_host,
            "port": int(self.cfg.mysql_port),
            "user": self.cfg.mysql_user,
            "password": self.cfg.mysql_password,
            "database": self.cfg.mysql_database,
            "charset": self.cfg.mysql_charset,
        }
        logger.info(
            "Using MySQL database: {}:{} / {}",
            self.mysql_config["host"],
            self.mysql_config["port"],
            self.mysql_config["database"],
        )

    def _build_mysql_url(self) -> str:
        host = str(self.mysql_config.get("host") or "").strip()
        port = int(self.mysql_config.get("port") or 3306)
        user = str(self.mysql_config.get("user") or "").strip()
        password = str(self.mysql_config.get("password") or "")
        database = str(self.mysql_config.get("database") or "").strip()
        charset = str(self.mysql_config.get("charset") or "utf8mb4").strip() or "utf8mb4"

        if not host or not user or not database:
            raise AppHTTPException(
                detail="Database configuration is incomplete",
                error_detail="mysql host/user/database are required",
            )

        return (
            "mysql+aiomysql://"
            f"{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/"
            f"{quote_plus(database)}?charset={quote_plus(charset)}"
        )

    async def init_conn(self) -> None:
        """Initialize the async engine and session factory."""

        if self._engine is not None:
            return

        async with self._lock:
            if self._engine is not None:
                return

            self._engine = create_async_engine(
                self._build_mysql_url(),
                pool_pre_ping=True,
                pool_recycle=3600,
                future=True,
            )
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                autoflush=False,
            )
            logger.info("Database engine initialized.")

    async def initialize_schema(self, metadata: Any | None = None) -> None:
        """Create tables for explicit SQLAlchemy metadata.

        Business model discovery is intentionally not performed here.
        """

        if metadata is None:
            logger.info("No metadata provided; skip database schema initialization.")
            return

        if self._engine is None:
            await self.init_conn()
        assert self._engine is not None

        async with self._engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    @asynccontextmanager
    async def get_session(
        self,
        *,
        autocommit: bool = True,
    ) -> AsyncIterator[AsyncSession]:
        """Yield a managed async session."""

        if self._session_factory is None:
            await self.init_conn()
        assert self._session_factory is not None

        async with self._session_factory() as session:
            try:
                yield session
                if autocommit:
                    await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        """Dispose the async engine."""

        if self._engine is None:
            return
        await self._engine.dispose()
        self._engine = None
        self._session_factory = None
        logger.info("Database engine closed.")


DatabaseManager = SessionManager


async def init_db_client(cfg: AppConfig | None = None) -> SessionManager:
    """Initialize and cache the process-wide database manager."""

    global _GLOBAL_DB

    _GLOBAL_DB = SessionManager(cfg)
    await _GLOBAL_DB.init_conn()
    return _GLOBAL_DB


async def get_global_db() -> SessionManager:
    """Return the cached database manager, initializing it on first use."""

    global _GLOBAL_DB

    if _GLOBAL_DB is None:
        _GLOBAL_DB = SessionManager()
        await _GLOBAL_DB.init_conn()
    return _GLOBAL_DB


async def close_db_client() -> None:
    """Close the cached database manager."""

    global _GLOBAL_DB

    if _GLOBAL_DB is None:
        return
    await _GLOBAL_DB.close()
    _GLOBAL_DB = None


@asynccontextmanager
async def session_scope(
    *,
    autocommit: bool = True,
) -> AsyncIterator[AsyncSession]:
    """Yield a managed async database session."""

    db = await get_global_db()
    async with db.get_session(autocommit=autocommit) as session:
        yield session


@asynccontextmanager
async def transaction_scope() -> AsyncIterator[AsyncSession]:
    """Yield a managed async database session that commits on success."""

    async with session_scope(autocommit=True) as session:
        yield session


__all__ = [
    "DatabaseManager",
    "SessionManager",
    "close_db_client",
    "db_retry",
    "get_global_db",
    "init_db_client",
    "session_scope",
    "transaction_scope",
]
