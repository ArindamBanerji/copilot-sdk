"""DataOps natural-language query endpoint."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from copilot_sdk.di import NLQueryRouter


GraphStoreFactory = Callable[[], Any]


class QueryRequest(BaseModel):
    question: str | None = None


def create_query_router(graph_store_factory: GraphStoreFactory) -> APIRouter:
    router = APIRouter(prefix="/api/dataops", tags=["dataops-query"])
    query_router = NLQueryRouter()

    @router.post("/query")
    def query(payload: QueryRequest) -> dict[str, Any]:
        question = str(payload.question or "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="question is required")
        return query_router.query(question, graph_store_factory())

    return router
