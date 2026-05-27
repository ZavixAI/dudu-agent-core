#!/usr/bin/env python3
"""Application entrypoint."""

from __future__ import annotations

# ruff: noqa: E402
from typing import Optional

from dotenv import load_dotenv

# 指定加载的 .env 文件（保持不动）
load_dotenv(".env")

from api.mcp import mcp_http
from config.settings import get_app_config, init_app_config
from core.http.exceptions import register_exception_handlers
from core.http.middleware import register_middlewares
from core.metrics import metrics
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from lifecycle import build_app_lifespan
from utils.logging import init_logging

init_logging(log_name="app")


def create_app() -> FastAPI:
    """Create the FastAPI application instance."""

    cfg = get_app_config()
    app = FastAPI(
        title=cfg.app_name,
        lifespan=build_app_lifespan(mcp_http.lifespan), # type: ignore
        routes=[*mcp_http.routes],
    )

    register_exception_handlers(app)
    register_middlewares(app)

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
    async def prometheus_metrics() -> str:
        return metrics.render_prometheus()

    return app


app = create_app()


def main(argv: Optional[list[str]] = None) -> None:
    """Run the application with uvicorn."""

    _ = argv

    import uvicorn

    cfg = init_app_config()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=cfg.port,
        reload=False,
        access_log=False,
    )


if __name__ == "__main__":
    main()
