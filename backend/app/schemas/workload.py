"""
Workload Analysis Pydantic Schemas

워크로드 분석 API 요청/응답 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# Enums
class WorkloadTypeEnum(str, Enum):
    AI_INFERENCE = "AI_INFERENCE"
    AI_TRAINING = "AI_TRAINING"
    IMAGE_PROCESSING = "IMAGE_PROCESSING"
    VIDEO_ENCODING = "VIDEO_ENCODING"
    SCIENTIFIC_COMPUTE = "SCIENTIFIC_COMPUTE"
    GENERAL_PURPOSE = "GENERAL_PURPOSE"
    EDGE_INFERENCE = "EDGE_INFERENCE"


class FormFactorEnum(str, Enum):
    DATA_CENTER = "DATA_CENTER"
    EDGE_SERVER = "EDGE_SERVER"
    EMBEDDED = "EMBEDDED"
    MOBILE = "MOBILE"


class CoolingTypeEnum(str, Enum):
    AIR = "AIR"
    LIQUID = "LIQUID"
    PASSIVE = "PASSIVE"


class PrecisionEnum(str, Enum):
    FP32 = "FP32"
    FP16 = "FP16"
    BF16 = "BF16"
    INT8 = "INT8"
    INT4 = "INT4"


class MemoryTypeEnum(str, Enum):
    HBM3 = "HBM3"
    HBM3E = "HBM3E"
    HBM4 = "HBM4"
    GDDR6 = "GDDR6"
    LPDDR5 = "LPDDR5"


# Request Schemas
class ComputeRequirementsRequest(BaseModel):
    """연산 요구사항"""
    operations_per_inference: float = Field(
        ..., gt=0, le=10000,
        description="추론당 필요 연산량 (TOPS)"
    )
    target_latency_ms: float = Field(
        ..., gt=0, le=10000,
        description="목표 지연시간 (ms)"
    )
    batch_size: int = Field(
        default=1, ge=1, le=512,
        description="배치 크기"
    )
    precision: PrecisionEnum = Field(
        default=PrecisionEnum.INT8,
        description="연산 정밀도"
    )


class MemoryRequirementsRequest(BaseModel):
    """메모리 요구사항"""
    model_size_gb: float = Field(
        ..., ge=0, le=1000,
        description="모델 크기 (GB)"
    )
    activation_memory_gb: float = Field(
        default=0.0, ge=0, le=500,
        description="활성화 메모리 (GB)"
    )
    kv_cache_gb: float = Field(
        default=0.0, ge=0, le=500,
        description="KV 캐시 크기 (GB) - LLM용"
    )
    bandwidth_requirement_gbps: float = Field(
        ..., gt=0, le=10000,
        description="메모리 대역폭 요구량 (GB/s)"
    )


class PowerConstraintsRequest(BaseModel):
    """전력 제약조건"""
    max_tdp_watts: float = Field(
        ..., gt=0, le=1000,
        description="최대 TDP (Watts)"
    )
    target_efficiency_tops_per_watt: float = Field(
        default=1.0, gt=0, le=100,
        description="목표 효율 (TOPS/W)"
    )


class DeploymentContextRequest(BaseModel):
    """배포 환경"""
    form_factor: FormFactorEnum = Field(
        default=FormFactorEnum.DATA_CENTER,
        description="폼팩터"
    )
    cooling: CoolingTypeEnum = Field(
        default=CoolingTypeEnum.AIR,
        description="쿨링 방식"
    )
    volume_per_year: int = Field(
        default=10000, ge=100, le=10000000,
        description="연간 생산량"
    )


class WorkloadProfileRequest(BaseModel):
    """워크로드 프로파일 요청"""
    name: str = Field(
        ..., min_length=1, max_length=200,
        description="워크로드 이름"
    )
    workload_type: WorkloadTypeEnum = Field(
        ..., description="워크로드 유형"
    )
    compute_requirements: ComputeRequirementsRequest
    memory_requirements: MemoryRequirementsRequest
    power_constraints: PowerConstraintsRequest
    deployment_context: DeploymentContextRequest = Field(
        default_factory=DeploymentContextRequest
    )
    description: Optional[str] = Field(
        default=None, max_length=1000,
        description="워크로드 설명"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "LLM Inference - Llama-3 70B",
                "workload_type": "AI_INFERENCE",
                "compute_requirements": {
                    "operations_per_inference": 140,
                    "target_latency_ms": 100,
                    "batch_size": 8,
                    "precision": "INT8"
                },
                "memory_requirements": {
                    "model_size_gb": 70,
                    "activation_memory_gb": 16,
                    "kv_cache_gb": 32,
                    "bandwidth_requirement_gbps": 800
                },
                "power_constraints": {
                    "max_tdp_watts": 300,
                    "target_efficiency_tops_per_watt": 2.5
                },
                "deployment_context": {
                    "form_factor": "DATA_CENTER",
                    "cooling": "AIR",
                    "volume_per_year": 50000
                }
            }
        }


# Response Schemas
class WorkloadCharacterizationResponse(BaseModel):
    """워크로드 특성 분석 결과"""
    compute_intensity: str = Field(..., description="연산 집약도 (Memory-Bound/Compute-Bound/Balanced)")
    arithmetic_intensity: float = Field(..., description="Arithmetic Intensity (OPs/Byte)")
    bottleneck: str = Field(..., description="병목 지점")
    required_tops: float = Field(..., description="필요 TOPS")


class RecommendedArchitectureResponse(BaseModel):
    """추천 아키텍처"""
    name: str
    description: str
    process_node_nm: int
    npu_cores: int
    cpu_cores: int
    gpu_cores: int
    memory_type: MemoryTypeEnum
    memory_capacity_gb: int
    memory_bandwidth_tbps: float
    die_size_mm2: float
    power_tdp_w: float
    performance_tops: float
    efficiency_tops_per_watt: float
    estimated_unit_cost: float
    match_score: float = Field(..., ge=0, le=100)
    is_recommended: bool
    justifications: list[str]
    trade_offs: list[str]


class CompetitiveBenchmarkResponse(BaseModel):
    """경쟁사 벤치마크"""
    competitor_name: str
    performance_tops: float
    power_tdp_w: float
    memory_bandwidth_tbps: float
    estimated_price: float
    comparison_summary: str


class WorkloadAnalysisResponse(BaseModel):
    """워크로드 분석 결과"""
    workload_name: str
    workload_type: WorkloadTypeEnum
    characterization: WorkloadCharacterizationResponse
    recommended_architectures: list[RecommendedArchitectureResponse]
    competitive_benchmarks: list[CompetitiveBenchmarkResponse]
    confidence_score: float = Field(..., ge=0, le=100)
    analysis_notes: list[str]


# Preset Schemas
class WorkloadPresetSummary(BaseModel):
    """프리셋 요약"""
    id: str
    name: str
    category: str
    description: str


class WorkloadPresetsResponse(BaseModel):
    """프리셋 목록 응답"""
    presets: list[WorkloadPresetSummary]


class WorkloadPresetDetailResponse(BaseModel):
    """프리셋 상세 응답"""
    id: str
    name: str
    category: str
    description: str
    profile: WorkloadProfileRequest
