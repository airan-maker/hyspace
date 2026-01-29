from fastapi import APIRouter
from .simulation import router as simulation_router
from .reference_data import router as reference_router
from .workload import router as workload_router

api_router = APIRouter()
api_router.include_router(simulation_router, prefix="/simulate", tags=["Simulation"])
api_router.include_router(reference_router, prefix="/reference", tags=["Reference Data"])
api_router.include_router(workload_router, prefix="/workload", tags=["Workload Analysis"])
