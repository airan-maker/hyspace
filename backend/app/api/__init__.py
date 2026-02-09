from fastapi import APIRouter
from .simulation import router as simulation_router
from .reference_data import router as reference_router
from .workload import router as workload_router
from .yield_api import router as yield_router
from .security import router as security_router
from .fab import router as fab_router
from .supply import router as supply_router
from .notifications import router as notifications_router
from .reports import router as reports_router
from .predictions import router as predictions_router
from .websocket import router as websocket_router
from .ontology import router as ontology_router
from .seed import router as seed_router
from .graph import router as graph_router
from .ai_insights import router as ai_insights_router
from .whatif import router as whatif_router
from .yield_graph import router as yield_graph_router

api_router = APIRouter()
api_router.include_router(simulation_router, prefix="/simulate", tags=["Simulation"])
api_router.include_router(reference_router, prefix="/reference", tags=["Reference Data"])
api_router.include_router(workload_router, prefix="/workload", tags=["Workload Analysis"])
api_router.include_router(yield_router, tags=["Yield Management"])
api_router.include_router(security_router, tags=["Security & Governance"])
api_router.include_router(fab_router, tags=["Virtual Fab"])
api_router.include_router(supply_router, tags=["Supply Chain"])
api_router.include_router(notifications_router, tags=["Notifications"])
api_router.include_router(reports_router, tags=["Reports"])
api_router.include_router(predictions_router, tags=["Predictive Analytics"])
api_router.include_router(websocket_router, tags=["Real-time WebSocket"])
api_router.include_router(ontology_router, tags=["Domain Ontology"])
api_router.include_router(seed_router, tags=["Seed Data Agent"])
api_router.include_router(graph_router, tags=["Graph Database"])
api_router.include_router(ai_insights_router, tags=["AI Insights"])
api_router.include_router(whatif_router, tags=["What-If Simulation"])
api_router.include_router(yield_graph_router, tags=["Yield-Graph Bridge"])
