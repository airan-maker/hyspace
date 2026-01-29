from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
import uuid

from ..database import get_db
from ..models import Simulation
from ..schemas import (
    ChipConfigRequest,
    PPAResponse,
    PPAAlternativesResponse,
    CostRequest,
    CostResponse,
    VolumeAnalysisResponse,
    FullSimulationRequest,
    FullSimulationResponse,
    SimulationSummary,
)
from ..schemas.ppa import PPAAlternativeItem, AreaBreakdown, PowerBreakdown
from ..schemas.cost import VolumeAnalysisRequest, VolumeEconomicsItem
from ..services import PPAEngine, CostSimulator
from ..services.ppa_engine import ChipConfig

router = APIRouter()

# Initialize engines
ppa_engine = PPAEngine()
cost_simulator = CostSimulator()


def config_request_to_chip_config(req: ChipConfigRequest) -> ChipConfig:
    """Convert API request to internal ChipConfig"""
    return ChipConfig(
        process_node_nm=req.process_node_nm,
        cpu_cores=req.cpu_cores,
        gpu_cores=req.gpu_cores,
        npu_cores=req.npu_cores,
        l2_cache_mb=req.l2_cache_mb,
        l3_cache_mb=req.l3_cache_mb,
        pcie_lanes=req.pcie_lanes,
        memory_channels=req.memory_channels,
        target_frequency_ghz=req.target_frequency_ghz,
    )


def ppa_result_to_response(result) -> PPAResponse:
    """Convert internal PPAResult to API response"""
    return PPAResponse(
        die_size_mm2=result.die_size_mm2,
        power_tdp_w=result.power_tdp_w,
        performance_ghz=result.performance_ghz,
        performance_tops=result.performance_tops,
        efficiency_tops_per_watt=result.efficiency_tops_per_watt,
        confidence_score=result.confidence_score,
        area_breakdown=AreaBreakdown(**result.area_breakdown),
        power_breakdown=PowerBreakdown(**result.power_breakdown),
    )


@router.post("/ppa", response_model=PPAResponse)
async def simulate_ppa(request: ChipConfigRequest):
    """
    PPA (Power, Performance, Area) 시뮬레이션

    칩 구성을 기반으로 다이 면적, 전력 소비, 성능을 계산합니다.
    """
    try:
        chip_config = config_request_to_chip_config(request)
        result = ppa_engine.calculate(chip_config)
        return ppa_result_to_response(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ppa/alternatives", response_model=PPAAlternativesResponse)
async def simulate_ppa_alternatives(request: ChipConfigRequest):
    """
    대안 구성 비교

    현재 구성과 함께 저전력/고성능 대안을 함께 제안합니다.
    """
    try:
        chip_config = config_request_to_chip_config(request)
        alternatives = ppa_engine.generate_alternatives(chip_config)

        items = [
            PPAAlternativeItem(
                variant=variant,
                result=ppa_result_to_response(result)
            )
            for variant, result in alternatives
        ]

        return PPAAlternativesResponse(alternatives=items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cost", response_model=CostResponse)
async def simulate_cost(request: CostRequest):
    """
    제조 비용 시뮬레이션

    다이 크기와 공정 노드를 기반으로 제조 비용을 계산합니다.
    """
    try:
        result = cost_simulator.calculate_cost(
            die_size=request.die_size_mm2,
            node_nm=request.process_node_nm,
            volume=request.volume,
            target_asp=request.target_asp,
        )
        return CostResponse(
            wafer_cost=result.wafer_cost,
            die_cost=result.die_cost,
            good_die_cost=result.good_die_cost,
            package_cost=result.package_cost,
            test_cost=result.test_cost,
            total_unit_cost=result.total_unit_cost,
            target_asp=result.target_asp,
            gross_margin=result.gross_margin,
            gross_margin_percent=result.gross_margin_percent,
            net_die_per_wafer=result.net_die_per_wafer,
            yield_rate=result.yield_rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cost/volume-analysis", response_model=VolumeAnalysisResponse)
async def analyze_volume_economics(request: VolumeAnalysisRequest):
    """
    볼륨별 경제성 분석

    다양한 생산량에 따른 단가 변화를 분석합니다.
    """
    try:
        results = cost_simulator.analyze_volume_economics(
            die_size=request.die_size_mm2,
            node_nm=request.process_node_nm,
            target_asp=request.target_asp,
            volumes=request.volumes,
        )
        return VolumeAnalysisResponse(
            analysis=[
                VolumeEconomicsItem(
                    volume=r.volume,
                    unit_cost=r.unit_cost,
                    total_cost=r.total_cost,
                    volume_discount=r.volume_discount,
                    break_even_volume=r.break_even_volume,
                )
                for r in results
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/full", response_model=FullSimulationResponse)
async def run_full_simulation(
    request: FullSimulationRequest,
    db: Session = Depends(get_db)
):
    """
    통합 시뮬레이션 (PPA + 비용)

    칩 구성을 기반으로 PPA와 비용을 동시에 계산하고 결과를 저장합니다.
    """
    try:
        # PPA 계산
        chip_config = config_request_to_chip_config(request.config)
        ppa_result = ppa_engine.calculate(chip_config)

        # 비용 계산
        cost_result = cost_simulator.calculate_cost(
            die_size=ppa_result.die_size_mm2,
            node_nm=request.config.process_node_nm,
            volume=request.volume,
            target_asp=request.target_asp,
        )

        # DB 저장
        simulation_id = uuid.uuid4()
        simulation = Simulation(
            id=simulation_id,
            name=request.name,
            config=request.config.model_dump(),
            result={
                "ppa": {
                    "die_size_mm2": ppa_result.die_size_mm2,
                    "power_tdp_w": ppa_result.power_tdp_w,
                    "performance_ghz": ppa_result.performance_ghz,
                    "performance_tops": ppa_result.performance_tops,
                    "efficiency_tops_per_watt": ppa_result.efficiency_tops_per_watt,
                    "area_breakdown": ppa_result.area_breakdown,
                    "power_breakdown": ppa_result.power_breakdown,
                },
                "cost": {
                    "wafer_cost": cost_result.wafer_cost,
                    "die_cost": cost_result.die_cost,
                    "good_die_cost": cost_result.good_die_cost,
                    "package_cost": cost_result.package_cost,
                    "test_cost": cost_result.test_cost,
                    "total_unit_cost": cost_result.total_unit_cost,
                    "target_asp": cost_result.target_asp,
                    "gross_margin": cost_result.gross_margin,
                    "gross_margin_percent": cost_result.gross_margin_percent,
                    "net_die_per_wafer": cost_result.net_die_per_wafer,
                    "yield_rate": cost_result.yield_rate,
                },
                "volume": request.volume,
            },
            confidence_score=ppa_result.confidence_score,
        )
        db.add(simulation)
        db.commit()

        return FullSimulationResponse(
            id=simulation_id,
            name=request.name,
            config=request.config,
            ppa=ppa_result_to_response(ppa_result),
            cost=CostResponse(
                wafer_cost=cost_result.wafer_cost,
                die_cost=cost_result.die_cost,
                good_die_cost=cost_result.good_die_cost,
                package_cost=cost_result.package_cost,
                test_cost=cost_result.test_cost,
                total_unit_cost=cost_result.total_unit_cost,
                target_asp=cost_result.target_asp,
                gross_margin=cost_result.gross_margin,
                gross_margin_percent=cost_result.gross_margin_percent,
                net_die_per_wafer=cost_result.net_die_per_wafer,
                yield_rate=cost_result.yield_rate,
            ),
            confidence_score=ppa_result.confidence_score,
            created_at=datetime.utcnow(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=list[SimulationSummary])
async def get_simulation_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    시뮬레이션 이력 조회

    저장된 시뮬레이션 결과 목록을 반환합니다.
    """
    simulations = (
        db.query(Simulation)
        .order_by(Simulation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        SimulationSummary(
            id=sim.id,
            name=sim.name,
            process_node_nm=sim.config.get("process_node_nm", 0),
            die_size_mm2=sim.result.get("ppa", {}).get("die_size_mm2", 0),
            power_tdp_w=sim.result.get("ppa", {}).get("power_tdp_w", 0),
            total_unit_cost=sim.result.get("cost", {}).get("total_unit_cost", 0),
            gross_margin_percent=sim.result.get("cost", {}).get("gross_margin_percent", 0),
            confidence_score=sim.confidence_score or 0,
            created_at=sim.created_at,
        )
        for sim in simulations
    ]


@router.get("/{simulation_id}", response_model=FullSimulationResponse)
async def get_simulation(
    simulation_id: UUID,
    db: Session = Depends(get_db)
):
    """
    시뮬레이션 결과 조회

    저장된 시뮬레이션 결과를 ID로 조회합니다.
    """
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()

    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    ppa_data = simulation.result.get("ppa", {})
    cost_data = simulation.result.get("cost", {})

    return FullSimulationResponse(
        id=simulation.id,
        name=simulation.name,
        config=ChipConfigRequest(**simulation.config),
        ppa=PPAResponse(
            die_size_mm2=ppa_data.get("die_size_mm2", 0),
            power_tdp_w=ppa_data.get("power_tdp_w", 0),
            performance_ghz=ppa_data.get("performance_ghz", 0),
            performance_tops=ppa_data.get("performance_tops", 0),
            efficiency_tops_per_watt=ppa_data.get("efficiency_tops_per_watt", 0),
            confidence_score=simulation.confidence_score or 0,
            area_breakdown=AreaBreakdown(**ppa_data.get("area_breakdown", {})),
            power_breakdown=PowerBreakdown(**ppa_data.get("power_breakdown", {})),
        ),
        cost=CostResponse(**cost_data),
        confidence_score=simulation.confidence_score or 0,
        created_at=simulation.created_at,
    )
