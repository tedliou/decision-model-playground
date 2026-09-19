from fastapi import APIRouter, Request

from playground.schemas import (
    ErrorResponse,
    Metadata,
    RecommendationRequest,
    RecommendationResponse,
)

router = APIRouter(prefix="/api/v1")


@router.get("/metadata", response_model=Metadata)
def metadata(request: Request):
    return request.app.state.service.metadata()


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    responses={status: {"model": ErrorResponse} for status in (409, 422, 500, 502, 503, 504)},
)
def recommend(body: RecommendationRequest, request: Request):
    return request.app.state.service.recommend(body)
