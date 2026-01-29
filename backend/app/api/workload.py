"""
Workload Analysis API Endpoints

워크로드 분석 REST API
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from ..schemas.workload import (
    WorkloadProfileRequest,
    WorkloadAnalysisResponse,
    WorkloadPresetsResponse,
    WorkloadPresetSummary,
    WorkloadPresetDetailResponse,
    WorkloadCharacterizationResponse,
    RecommendedArchitectureResponse,
    CompetitiveBenchmarkResponse,
    MemoryTypeEnum,
)
from ..services.workload_analyzer import (
    WorkloadAnalyzer,
    WorkloadProfile,
    WorkloadType,
    ComputeRequirements,
    MemoryRequirements,
    PowerConstraints,
    DeploymentContext,
    FormFactor,
    CoolingType,
    Precision,
    MemoryType,
)
from ..services.workload_presets import (
    get_all_presets,
    get_preset,
    get_preset_profile,
    WORKLOAD_PRESETS,
)

router = APIRouter()

# 워크로드 분석기 인스턴스
workload_analyzer = WorkloadAnalyzer()


def request_to_profile(request: WorkloadProfileRequest) -> WorkloadProfile:
    """API 요청을 도메인 모델로 변환"""
    return WorkloadProfile(
        name=request.name,
        workload_type=WorkloadType(request.workload_type.value),
        compute_requirements=ComputeRequirements(
            operations_per_inference=request.compute_requirements.operations_per_inference,
            target_latency_ms=request.compute_requirements.target_latency_ms,
            batch_size=request.compute_requirements.batch_size,
            precision=Precision(request.compute_requirements.precision.value),
        ),
        memory_requirements=MemoryRequirements(
            model_size_gb=request.memory_requirements.model_size_gb,
            activation_memory_gb=request.memory_requirements.activation_memory_gb,
            kv_cache_gb=request.memory_requirements.kv_cache_gb,
            bandwidth_requirement_gbps=request.memory_requirements.bandwidth_requirement_gbps,
        ),
        power_constraints=PowerConstraints(
            max_tdp_watts=request.power_constraints.max_tdp_watts,
            target_efficiency_tops_per_watt=request.power_constraints.target_efficiency_tops_per_watt,
        ),
        deployment_context=DeploymentContext(
            form_factor=FormFactor(request.deployment_context.form_factor.value),
            cooling=CoolingType(request.deployment_context.cooling.value),
            volume_per_year=request.deployment_context.volume_per_year,
        ),
        description=request.description,
    )


def memory_type_to_enum(mt: MemoryType) -> MemoryTypeEnum:
    """도메인 MemoryType을 스키마 Enum으로 변환"""
    return MemoryTypeEnum(mt.value)


@router.post("/analyze", response_model=WorkloadAnalysisResponse)
async def analyze_workload(request: WorkloadProfileRequest):
    """
    워크로드 분석 및 아키텍처 추천

    고객 워크로드 프로파일을 분석하여 최적의 칩 아키텍처를 추천합니다.

    - **compute_requirements**: 연산 요구사항 (TOPS, 지연시간, 배치 크기, 정밀도)
    - **memory_requirements**: 메모리 요구사항 (모델 크기, 대역폭)
    - **power_constraints**: 전력 제약조건 (TDP, 효율)
    - **deployment_context**: 배포 환경 (폼팩터, 쿨링, 볼륨)
    """
    try:
        # 요청을 도메인 모델로 변환
        profile = request_to_profile(request)

        # 분석 실행
        result = workload_analyzer.analyze(profile)

        # 응답 변환
        return WorkloadAnalysisResponse(
            workload_name=result.workload_profile.name,
            workload_type=request.workload_type,
            characterization=WorkloadCharacterizationResponse(
                compute_intensity=result.characterization.compute_intensity,
                arithmetic_intensity=result.characterization.arithmetic_intensity,
                bottleneck=result.characterization.bottleneck,
                required_tops=result.characterization.required_tops,
            ),
            recommended_architectures=[
                RecommendedArchitectureResponse(
                    name=arch.name,
                    description=arch.description,
                    process_node_nm=arch.process_node_nm,
                    npu_cores=arch.npu_cores,
                    cpu_cores=arch.cpu_cores,
                    gpu_cores=arch.gpu_cores,
                    memory_type=memory_type_to_enum(arch.memory_type),
                    memory_capacity_gb=arch.memory_capacity_gb,
                    memory_bandwidth_tbps=arch.memory_bandwidth_tbps,
                    die_size_mm2=arch.die_size_mm2,
                    power_tdp_w=arch.power_tdp_w,
                    performance_tops=arch.performance_tops,
                    efficiency_tops_per_watt=arch.efficiency_tops_per_watt,
                    estimated_unit_cost=arch.estimated_unit_cost,
                    match_score=arch.match_score,
                    is_recommended=arch.is_recommended,
                    justifications=arch.justifications,
                    trade_offs=arch.trade_offs,
                )
                for arch in result.recommended_architectures
            ],
            competitive_benchmarks=[
                CompetitiveBenchmarkResponse(
                    competitor_name=bench.competitor_name,
                    performance_tops=bench.performance_tops,
                    power_tdp_w=bench.power_tdp_w,
                    memory_bandwidth_tbps=bench.memory_bandwidth_tbps,
                    estimated_price=bench.estimated_price,
                    comparison_summary=bench.comparison_summary,
                )
                for bench in result.competitive_benchmarks
            ],
            confidence_score=result.confidence_score,
            analysis_notes=result.analysis_notes,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@router.get("/presets", response_model=WorkloadPresetsResponse)
async def list_workload_presets():
    """
    프리셋 워크로드 목록

    사전 정의된 워크로드 프로파일 템플릿 목록을 반환합니다.
    """
    presets = get_all_presets()
    return WorkloadPresetsResponse(
        presets=[
            WorkloadPresetSummary(
                id=p["id"],
                name=p["name"],
                category=p["category"],
                description=p["description"],
            )
            for p in presets
        ]
    )


@router.get("/presets/{preset_id}", response_model=WorkloadPresetDetailResponse)
async def get_workload_preset(preset_id: str):
    """
    특정 프리셋 조회

    프리셋 ID로 상세 워크로드 프로파일을 조회합니다.
    """
    preset = get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"프리셋을 찾을 수 없습니다: {preset_id}")

    profile = preset["profile"]

    return WorkloadPresetDetailResponse(
        id=preset["id"],
        name=preset["name"],
        category=preset["category"],
        description=preset["description"],
        profile=WorkloadProfileRequest(
            name=profile.name,
            workload_type=profile.workload_type.value,
            compute_requirements={
                "operations_per_inference": profile.compute_requirements.operations_per_inference,
                "target_latency_ms": profile.compute_requirements.target_latency_ms,
                "batch_size": profile.compute_requirements.batch_size,
                "precision": profile.compute_requirements.precision.value,
            },
            memory_requirements={
                "model_size_gb": profile.memory_requirements.model_size_gb,
                "activation_memory_gb": profile.memory_requirements.activation_memory_gb,
                "kv_cache_gb": profile.memory_requirements.kv_cache_gb,
                "bandwidth_requirement_gbps": profile.memory_requirements.bandwidth_requirement_gbps,
            },
            power_constraints={
                "max_tdp_watts": profile.power_constraints.max_tdp_watts,
                "target_efficiency_tops_per_watt": profile.power_constraints.target_efficiency_tops_per_watt,
            },
            deployment_context={
                "form_factor": profile.deployment_context.form_factor.value,
                "cooling": profile.deployment_context.cooling.value,
                "volume_per_year": profile.deployment_context.volume_per_year,
            },
            description=profile.description,
        ),
    )


@router.post("/presets/{preset_id}/analyze", response_model=WorkloadAnalysisResponse)
async def analyze_preset_workload(preset_id: str):
    """
    프리셋 워크로드 분석

    프리셋 ID로 워크로드를 분석하고 아키텍처를 추천합니다.
    """
    profile = get_preset_profile(preset_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"프리셋을 찾을 수 없습니다: {preset_id}")

    try:
        result = workload_analyzer.analyze(profile)

        return WorkloadAnalysisResponse(
            workload_name=result.workload_profile.name,
            workload_type=result.workload_profile.workload_type.value,
            characterization=WorkloadCharacterizationResponse(
                compute_intensity=result.characterization.compute_intensity,
                arithmetic_intensity=result.characterization.arithmetic_intensity,
                bottleneck=result.characterization.bottleneck,
                required_tops=result.characterization.required_tops,
            ),
            recommended_architectures=[
                RecommendedArchitectureResponse(
                    name=arch.name,
                    description=arch.description,
                    process_node_nm=arch.process_node_nm,
                    npu_cores=arch.npu_cores,
                    cpu_cores=arch.cpu_cores,
                    gpu_cores=arch.gpu_cores,
                    memory_type=memory_type_to_enum(arch.memory_type),
                    memory_capacity_gb=arch.memory_capacity_gb,
                    memory_bandwidth_tbps=arch.memory_bandwidth_tbps,
                    die_size_mm2=arch.die_size_mm2,
                    power_tdp_w=arch.power_tdp_w,
                    performance_tops=arch.performance_tops,
                    efficiency_tops_per_watt=arch.efficiency_tops_per_watt,
                    estimated_unit_cost=arch.estimated_unit_cost,
                    match_score=arch.match_score,
                    is_recommended=arch.is_recommended,
                    justifications=arch.justifications,
                    trade_offs=arch.trade_offs,
                )
                for arch in result.recommended_architectures
            ],
            competitive_benchmarks=[
                CompetitiveBenchmarkResponse(
                    competitor_name=bench.competitor_name,
                    performance_tops=bench.performance_tops,
                    power_tdp_w=bench.power_tdp_w,
                    memory_bandwidth_tbps=bench.memory_bandwidth_tbps,
                    estimated_price=bench.estimated_price,
                    comparison_summary=bench.comparison_summary,
                )
                for bench in result.competitive_benchmarks
            ],
            confidence_score=result.confidence_score,
            analysis_notes=result.analysis_notes,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")
