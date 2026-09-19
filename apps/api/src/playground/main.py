import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from playground.catalog import load_catalog
from playground.config import Settings, configure_runtime
from playground.providers.base import ProviderError
from playground.providers.jev import JevProvider
from playground.providers.laya import LayaProvider
from playground.routes import router
from playground.service import RecommendationService

logger = logging.getLogger(__name__)


def create_app(service: RecommendationService | None = None) -> FastAPI:
    configure_runtime()
    app = FastAPI(title="VerveCode Model Playground", version="0.1.0")
    if service is None:
        settings = Settings()
        service = RecommendationService(
            load_catalog(), {"laya": LayaProvider(settings), "jev": JevProvider(settings)}
        )
    app.state.service = service
    app.include_router(router)

    @app.exception_handler(ProviderError)
    async def provider_error(_request: Request, exc: ProviderError):
        return JSONResponse(
            status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, _exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_request",
                    "message": "請輸入 1–500 字的問題並選擇有效模型",
                }
            },
        )

    @app.exception_handler(Exception)
    async def unexpected_error(_request: Request, exc: Exception):
        logger.exception("Recommendation failed", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "模型執行失敗，請查看後端終端機記錄",
                }
            },
        )

    return app


app = create_app()
