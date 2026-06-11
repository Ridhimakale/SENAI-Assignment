from fastapi import APIRouter

from app.api.v1.agent import router as agent_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.classification import router as classification_router
from app.api.v1.health import router as health_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.operations import router as operations_router
from app.api.v1.simulation import router as simulation_router
from app.api.v1.rag import router as rag_router
from app.api.v1.web_intelligence import router as web_intelligence_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(ingest_router)
api_router.include_router(rag_router)
api_router.include_router(classification_router)
api_router.include_router(agent_router)
api_router.include_router(web_intelligence_router)
api_router.include_router(analytics_router)
api_router.include_router(operations_router)
api_router.include_router(simulation_router)
