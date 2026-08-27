"""DataOps natural-language query endpoint."""

from __future__ import annotations

from typing import Any, Callable, cast

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from copilot_sdk.di import NLQueryRouter
from copilot_sdk.di.query_service import DIQueryService, InvalidQueryError


GraphStoreFactory = Callable[[], Any]


class QueryRequest(BaseModel):
    question: str | None = None


def create_query_router(
    graph_store_factory: GraphStoreFactory,
    *,
    query_service: DIQueryService | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/dataops", tags=["dataops-query"])
    query_router = NLQueryRouter()

    @router.post("/query")
    def query(payload: QueryRequest) -> dict[str, Any]:
        question = str(payload.question or "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="question is required")
        if query_service is not None:
            try:
                response: dict[str, Any] = cast(dict[str, Any], query_service.execute(
                    {"question": question, "context": {"domain": "dataops"}}
                ).model_dump())
                # Preserve the legacy compatibility field while sharing the
                # same DIQueryService execution path as the canonical route.
                response["intent"] = response["query"]["intent"]
                return response
            except InvalidQueryError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        return cast(dict[str, Any], query_router.query(question, graph_store_factory()))

    return router
