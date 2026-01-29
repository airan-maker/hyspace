"""
Workload Presets

사전 정의된 워크로드 프로파일 템플릿
"""

from .workload_analyzer import (
    WorkloadProfile,
    WorkloadType,
    ComputeRequirements,
    MemoryRequirements,
    PowerConstraints,
    DeploymentContext,
    FormFactor,
    CoolingType,
    Precision,
)

WORKLOAD_PRESETS = {
    "llm_inference_70b": {
        "id": "llm_inference_70b",
        "name": "LLM Inference - Llama-3 70B",
        "category": "AI Inference",
        "description": "70B 파라미터 대규모 언어 모델 추론 워크로드. 데이터센터 배포 최적화.",
        "profile": WorkloadProfile(
            name="LLM Inference - Llama-3 70B",
            workload_type=WorkloadType.AI_INFERENCE,
            compute_requirements=ComputeRequirements(
                operations_per_inference=140.0,  # 140 TOPS per inference
                target_latency_ms=100.0,
                batch_size=8,
                precision=Precision.INT8,
            ),
            memory_requirements=MemoryRequirements(
                model_size_gb=70.0,
                activation_memory_gb=16.0,
                kv_cache_gb=32.0,
                bandwidth_requirement_gbps=800.0,
            ),
            power_constraints=PowerConstraints(
                max_tdp_watts=300.0,
                target_efficiency_tops_per_watt=2.5,
            ),
            deployment_context=DeploymentContext(
                form_factor=FormFactor.DATA_CENTER,
                cooling=CoolingType.AIR,
                volume_per_year=50000,
            ),
            description="대규모 언어 모델 추론을 위한 고대역폭 메모리 요구",
        ),
    },

    "llm_inference_7b": {
        "id": "llm_inference_7b",
        "name": "LLM Inference - Llama-3 7B",
        "category": "AI Inference",
        "description": "7B 파라미터 언어 모델 추론. 엣지 서버 배포 최적화.",
        "profile": WorkloadProfile(
            name="LLM Inference - Llama-3 7B",
            workload_type=WorkloadType.EDGE_INFERENCE,
            compute_requirements=ComputeRequirements(
                operations_per_inference=14.0,
                target_latency_ms=50.0,
                batch_size=4,
                precision=Precision.INT8,
            ),
            memory_requirements=MemoryRequirements(
                model_size_gb=7.0,
                activation_memory_gb=2.0,
                kv_cache_gb=4.0,
                bandwidth_requirement_gbps=200.0,
            ),
            power_constraints=PowerConstraints(
                max_tdp_watts=75.0,
                target_efficiency_tops_per_watt=5.0,
            ),
            deployment_context=DeploymentContext(
                form_factor=FormFactor.EDGE_SERVER,
                cooling=CoolingType.AIR,
                volume_per_year=200000,
            ),
            description="엣지 환경 LLM 추론, 저전력 고효율 설계",
        ),
    },

    "image_classification": {
        "id": "image_classification",
        "name": "Image Classification - ResNet-50",
        "category": "Image Processing",
        "description": "실시간 이미지 분류를 위한 임베디드 워크로드.",
        "profile": WorkloadProfile(
            name="Image Classification - ResNet-50",
            workload_type=WorkloadType.IMAGE_PROCESSING,
            compute_requirements=ComputeRequirements(
                operations_per_inference=8.0,
                target_latency_ms=5.0,
                batch_size=1,
                precision=Precision.INT8,
            ),
            memory_requirements=MemoryRequirements(
                model_size_gb=0.1,
                activation_memory_gb=0.5,
                kv_cache_gb=0.0,
                bandwidth_requirement_gbps=50.0,
            ),
            power_constraints=PowerConstraints(
                max_tdp_watts=15.0,
                target_efficiency_tops_per_watt=10.0,
            ),
            deployment_context=DeploymentContext(
                form_factor=FormFactor.EMBEDDED,
                cooling=CoolingType.PASSIVE,
                volume_per_year=500000,
            ),
            description="엣지 디바이스용 실시간 이미지 분류",
        ),
    },

    "video_encoding_4k": {
        "id": "video_encoding_4k",
        "name": "Video Encoding - 4K H.265",
        "category": "Video Processing",
        "description": "4K 해상도 H.265 실시간 인코딩.",
        "profile": WorkloadProfile(
            name="Video Encoding - 4K H.265",
            workload_type=WorkloadType.VIDEO_ENCODING,
            compute_requirements=ComputeRequirements(
                operations_per_inference=50.0,
                target_latency_ms=33.0,  # 30fps
                batch_size=1,
                precision=Precision.INT8,
            ),
            memory_requirements=MemoryRequirements(
                model_size_gb=0.0,
                activation_memory_gb=8.0,
                kv_cache_gb=0.0,
                bandwidth_requirement_gbps=400.0,
            ),
            power_constraints=PowerConstraints(
                max_tdp_watts=150.0,
                target_efficiency_tops_per_watt=3.0,
            ),
            deployment_context=DeploymentContext(
                form_factor=FormFactor.DATA_CENTER,
                cooling=CoolingType.AIR,
                volume_per_year=100000,
            ),
            description="스트리밍 서비스용 실시간 4K 비디오 인코딩",
        ),
    },

    "scientific_hpc": {
        "id": "scientific_hpc",
        "name": "Scientific HPC - Matrix Compute",
        "category": "High Performance Computing",
        "description": "과학 계산을 위한 대규모 행렬 연산 워크로드.",
        "profile": WorkloadProfile(
            name="Scientific HPC - Matrix Compute",
            workload_type=WorkloadType.SCIENTIFIC_COMPUTE,
            compute_requirements=ComputeRequirements(
                operations_per_inference=500.0,
                target_latency_ms=1000.0,
                batch_size=1,
                precision=Precision.FP32,
            ),
            memory_requirements=MemoryRequirements(
                model_size_gb=0.0,
                activation_memory_gb=64.0,
                kv_cache_gb=0.0,
                bandwidth_requirement_gbps=1000.0,
            ),
            power_constraints=PowerConstraints(
                max_tdp_watts=400.0,
                target_efficiency_tops_per_watt=1.0,
            ),
            deployment_context=DeploymentContext(
                form_factor=FormFactor.DATA_CENTER,
                cooling=CoolingType.LIQUID,
                volume_per_year=10000,
            ),
            description="FP32 정밀도 필요 과학 계산, 수치 시뮬레이션",
        ),
    },
}


def get_preset(preset_id: str) -> dict:
    """프리셋 조회"""
    return WORKLOAD_PRESETS.get(preset_id)


def get_all_presets() -> list[dict]:
    """모든 프리셋 목록"""
    return [
        {
            "id": preset["id"],
            "name": preset["name"],
            "category": preset["category"],
            "description": preset["description"],
        }
        for preset in WORKLOAD_PRESETS.values()
    ]


def get_preset_profile(preset_id: str) -> WorkloadProfile:
    """프리셋의 WorkloadProfile 반환"""
    preset = WORKLOAD_PRESETS.get(preset_id)
    if preset:
        return preset["profile"]
    return None
