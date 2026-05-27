"""FastAPI application lifespan helpers."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import AsyncIterator, Callable

from config.settings import init_app_config
from fastapi import FastAPI
from loguru import logger


def build_app_lifespan(
    nested_lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
):
    """Build the application lifespan and optionally nest a sub-application lifespan."""

    @asynccontextmanager
    async def lifespan(app_instance: FastAPI) -> AsyncIterator[None]:
        app_instance.state.startup_error = None
        app_instance.state.startup_config = None

        try:
            logger.info("Application startup started.")
            startup_cfg = init_app_config()
            app_instance.state.startup_config = startup_cfg
            logger.info("Application startup finished.")
        except Exception as exc:
            logger.exception("Application startup failed.")
            app_instance.state.startup_error = str(exc)
            raise

        try:
            if nested_lifespan is None:
                yield
            else:
                async with nested_lifespan(app_instance):
                    yield
        finally:
            logger.info("Application shutdown finished.")

    return lifespan
