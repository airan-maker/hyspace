"""
AI/ML Industry Ontology

AI 가속기 칩, 모델 아키텍처, 워크로드 특성에 대한 도메인 지식

Sources:
- Published specs (NVIDIA, AMD, Intel, Google, etc.)
- MLPerf Benchmarks
- Academic papers & whitepapers
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ============================================================
# AI Accelerator Specifications
# ============================================================

class AcceleratorVendor(str, Enum):
    NVIDIA = "NVIDIA"
    AMD = "AMD"
    INTEL = "Intel"
    GOOGLE = "Google"
    AWS = "AWS"
    MICROSOFT = "Microsoft"
    META = "Meta"
    BROADCOM = "Broadcom"


class AcceleratorCategory(str, Enum):
    TRAINING = "Training"
    INFERENCE = "Inference"
    GENERAL = "Training + Inference"


@dataclass
class MemorySpec:
    """메모리 사양"""
    type: str               # HBM3, HBM3E, HBM4, GDDR6X, LPDDR5
    capacity_gb: int
    bandwidth_tbps: float
    stack_count: Optional[int] = None
    bus_width_bits: Optional[int] = None


@dataclass
class ComputeSpec:
    """연산 사양"""
    fp64_tflops: Optional[float] = None
    fp32_tflops: Optional[float] = None
    tf32_tflops: Optional[float] = None
    bf16_tflops: Optional[float] = None
    fp16_tflops: Optional[float] = None
    fp8_tflops: Optional[float] = None
    int8_tops: Optional[float] = None
    int4_tops: Optional[float] = None
    sparsity_support: bool = False
    # Sparse일 때 2x
    sparse_bf16_tflops: Optional[float] = None
    sparse_int8_tops: Optional[float] = None


@dataclass
class AIAcceleratorSpec:
    """AI 가속기 사양 - 공개 데이터 기반"""
    name: str
    codename: str
    vendor: AcceleratorVendor
    category: AcceleratorCategory

    # Architecture
    process_node: str           # e.g., "TSMC N4P"
    transistor_count_billion: float
    die_size_mm2: float
    num_dies: int               # 멀티다이 구성 시
    packaging: str              # CoWoS, EMIB, etc.

    # Compute
    compute: ComputeSpec

    # Memory
    memory: MemorySpec

    # Power
    tdp_watts: int
    typical_power_watts: Optional[int] = None

    # Interconnect
    interconnect: str = ""          # NVLink, xGMI, etc.
    interconnect_bandwidth_gbps: Optional[float] = None
    pcie_gen: str = "PCIe 5.0"
    pcie_lanes: int = 16

    # Market
    msrp_usd: Optional[int] = None
    launch_year: int = 2024
    availability: str = ""

    # MLPerf benchmark (if available)
    mlperf_training_score: Optional[float] = None
    mlperf_inference_score: Optional[float] = None

    description: str = ""


AI_ACCELERATORS: dict[str, AIAcceleratorSpec] = {
    "H100_SXM": AIAcceleratorSpec(
        name="NVIDIA H100 SXM",
        codename="Hopper GH100",
        vendor=AcceleratorVendor.NVIDIA,
        category=AcceleratorCategory.GENERAL,
        process_node="TSMC N4P",
        transistor_count_billion=80,
        die_size_mm2=814,
        num_dies=1,
        packaging="CoWoS-S",
        compute=ComputeSpec(
            fp64_tflops=33.5,
            fp32_tflops=67,
            tf32_tflops=495,
            bf16_tflops=990,
            fp16_tflops=990,
            fp8_tflops=1979,
            int8_tops=3958,
            sparsity_support=True,
            sparse_bf16_tflops=1979,
            sparse_int8_tops=7916
        ),
        memory=MemorySpec(
            type="HBM3",
            capacity_gb=80,
            bandwidth_tbps=3.35,
            stack_count=5,
            bus_width_bits=5120
        ),
        tdp_watts=700,
        typical_power_watts=580,
        interconnect="NVLink 4.0",
        interconnect_bandwidth_gbps=900,
        pcie_gen="PCIe 5.0",
        msrp_usd=30000,
        launch_year=2022,
        description="현재 AI 학습 시장 표준, LLM 학습/추론 모두 지원"
    ),

    "H200_SXM": AIAcceleratorSpec(
        name="NVIDIA H200 SXM",
        codename="Hopper GH200",
        vendor=AcceleratorVendor.NVIDIA,
        category=AcceleratorCategory.GENERAL,
        process_node="TSMC N4P",
        transistor_count_billion=80,
        die_size_mm2=814,
        num_dies=1,
        packaging="CoWoS-S",
        compute=ComputeSpec(
            fp64_tflops=33.5,
            fp32_tflops=67,
            tf32_tflops=495,
            bf16_tflops=990,
            fp16_tflops=990,
            fp8_tflops=1979,
            int8_tops=3958,
            sparsity_support=True,
        ),
        memory=MemorySpec(
            type="HBM3E",
            capacity_gb=141,
            bandwidth_tbps=4.8,
            stack_count=6,
            bus_width_bits=6144
        ),
        tdp_watts=700,
        interconnect="NVLink 4.0",
        interconnect_bandwidth_gbps=900,
        msrp_usd=35000,
        launch_year=2024,
        description="H100 대비 메모리 76% 증가, 대형 LLM 추론 최적화"
    ),

    "B200": AIAcceleratorSpec(
        name="NVIDIA B200",
        codename="Blackwell GB200",
        vendor=AcceleratorVendor.NVIDIA,
        category=AcceleratorCategory.GENERAL,
        process_node="TSMC N4P",
        transistor_count_billion=208,
        die_size_mm2=1650,  # 2-die
        num_dies=2,
        packaging="CoWoS-L",
        compute=ComputeSpec(
            fp64_tflops=40,
            fp32_tflops=80,
            tf32_tflops=1125,
            bf16_tflops=2250,
            fp16_tflops=2250,
            fp8_tflops=4500,
            int8_tops=9000,
            sparsity_support=True,
            sparse_bf16_tflops=4500,
            sparse_int8_tops=18000
        ),
        memory=MemorySpec(
            type="HBM3E",
            capacity_gb=192,
            bandwidth_tbps=8.0,
            stack_count=8,
            bus_width_bits=8192
        ),
        tdp_watts=1000,
        interconnect="NVLink 5.0",
        interconnect_bandwidth_gbps=1800,
        msrp_usd=40000,
        launch_year=2024,
        description="2-die 구성, H100 대비 학습 4x, 추론 30x 향상"
    ),

    "MI300X": AIAcceleratorSpec(
        name="AMD Instinct MI300X",
        codename="Aldebaran",
        vendor=AcceleratorVendor.AMD,
        category=AcceleratorCategory.GENERAL,
        process_node="TSMC N5 + N6",
        transistor_count_billion=153,
        die_size_mm2=750,
        num_dies=8,  # 4 XCD + 4 IOD chiplets
        packaging="CoWoS-equivalent",
        compute=ComputeSpec(
            fp64_tflops=81.7,
            fp32_tflops=163.4,
            bf16_tflops=1307.4,
            fp16_tflops=1307.4,
            fp8_tflops=2614.9,
            int8_tops=2614,
        ),
        memory=MemorySpec(
            type="HBM3",
            capacity_gb=192,
            bandwidth_tbps=5.3,
            stack_count=8,
            bus_width_bits=8192
        ),
        tdp_watts=750,
        interconnect="Infinity Fabric",
        interconnect_bandwidth_gbps=896,
        msrp_usd=15000,
        launch_year=2023,
        description="메모리 용량 192GB로 대형 LLM에 유리, 가격 경쟁력"
    ),

    "MI325X": AIAcceleratorSpec(
        name="AMD Instinct MI325X",
        codename="",
        vendor=AcceleratorVendor.AMD,
        category=AcceleratorCategory.GENERAL,
        process_node="TSMC N5 + N6",
        transistor_count_billion=153,
        die_size_mm2=750,
        num_dies=8,
        packaging="CoWoS-equivalent",
        compute=ComputeSpec(
            fp64_tflops=81.7,
            fp32_tflops=163.4,
            bf16_tflops=1307.4,
            fp16_tflops=1307.4,
            fp8_tflops=2614.9,
            int8_tops=2614,
        ),
        memory=MemorySpec(
            type="HBM3E",
            capacity_gb=256,
            bandwidth_tbps=6.0,
            stack_count=8,
        ),
        tdp_watts=750,
        interconnect="Infinity Fabric",
        interconnect_bandwidth_gbps=896,
        launch_year=2024,
        description="MI300X 메모리 업그레이드, HBM3E 256GB"
    ),

    "Gaudi3": AIAcceleratorSpec(
        name="Intel Gaudi 3",
        codename="",
        vendor=AcceleratorVendor.INTEL,
        category=AcceleratorCategory.GENERAL,
        process_node="TSMC N5",
        transistor_count_billion=80,
        die_size_mm2=500,
        num_dies=2,
        packaging="EMIB",
        compute=ComputeSpec(
            bf16_tflops=1835,
            fp8_tflops=1835,
            int8_tops=1835,
        ),
        memory=MemorySpec(
            type="HBM2E",
            capacity_gb=128,
            bandwidth_tbps=3.7,
            stack_count=8,
        ),
        tdp_watts=600,
        interconnect="Ethernet (RoCE)",
        interconnect_bandwidth_gbps=600,
        msrp_usd=12000,
        launch_year=2024,
        description="네트워크 기반 스케일아웃, TCO 경쟁력 강조"
    ),

    "TPUv5e": AIAcceleratorSpec(
        name="Google TPU v5e",
        codename="",
        vendor=AcceleratorVendor.GOOGLE,
        category=AcceleratorCategory.INFERENCE,
        process_node="TSMC N7 (추정)",
        transistor_count_billion=30,
        die_size_mm2=300,
        num_dies=1,
        packaging="Standard",
        compute=ComputeSpec(
            bf16_tflops=197,
            int8_tops=394,
        ),
        memory=MemorySpec(
            type="HBM2E",
            capacity_gb=16,
            bandwidth_tbps=1.6,
        ),
        tdp_watts=250,
        interconnect="ICI (Inter-Chip Interconnect)",
        launch_year=2023,
        description="클라우드 추론 최적화, 비용 효율적인 스케일아웃"
    ),
}


# ============================================================
# HBM (High Bandwidth Memory) Specifications
# ============================================================

@dataclass
class HBMSpec:
    """HBM 사양 - JEDEC 및 공개 데이터"""
    generation: str
    jedec_standard: str
    bandwidth_per_stack_gbps: int
    max_capacity_per_stack_gb: int
    pin_speed_gbps: float
    io_width_bits: int
    stack_height: str       # "8-Hi", "12-Hi", "16-Hi"
    vendors: list[str]
    process_node: str
    tsv_pitch_um: float     # Through-Silicon Via 간격
    power_per_stack_w: float
    volume_production_year: int
    description: str


HBM_GENERATIONS: dict[str, HBMSpec] = {
    "HBM2E": HBMSpec(
        generation="HBM2E",
        jedec_standard="JESD235C",
        bandwidth_per_stack_gbps=460,
        max_capacity_per_stack_gb=16,
        pin_speed_gbps=3.6,
        io_width_bits=1024,
        stack_height="8-Hi",
        vendors=["SK Hynix", "Samsung", "Micron"],
        process_node="1Y nm DRAM",
        tsv_pitch_um=40,
        power_per_stack_w=8,
        volume_production_year=2021,
        description="현재 주류 HBM, A100/MI250 탑재"
    ),
    "HBM3": HBMSpec(
        generation="HBM3",
        jedec_standard="JESD238",
        bandwidth_per_stack_gbps=665,
        max_capacity_per_stack_gb=24,
        pin_speed_gbps=6.4,
        io_width_bits=1024,
        stack_height="8-Hi / 12-Hi",
        vendors=["SK Hynix", "Samsung", "Micron"],
        process_node="1a nm DRAM",
        tsv_pitch_um=36,
        power_per_stack_w=10,
        volume_production_year=2023,
        description="H100 탑재, 대역폭 44% 향상"
    ),
    "HBM3E": HBMSpec(
        generation="HBM3E",
        jedec_standard="JESD238A",
        bandwidth_per_stack_gbps=1180,
        max_capacity_per_stack_gb=36,
        pin_speed_gbps=9.2,
        io_width_bits=1024,
        stack_height="12-Hi",
        vendors=["SK Hynix", "Samsung", "Micron"],
        process_node="1b nm DRAM",
        tsv_pitch_um=32,
        power_per_stack_w=12,
        volume_production_year=2024,
        description="H200/B200 탑재, 12-Hi 스택으로 용량·대역폭 동시 향상"
    ),
    "HBM4": HBMSpec(
        generation="HBM4",
        jedec_standard="JESD238B (예정)",
        bandwidth_per_stack_gbps=1640,
        max_capacity_per_stack_gb=48,
        pin_speed_gbps=6.4,
        io_width_bits=2048,
        stack_height="16-Hi",
        vendors=["SK Hynix", "Samsung", "Micron"],
        process_node="1c nm DRAM",
        tsv_pitch_um=28,
        power_per_stack_w=14,
        volume_production_year=2026,
        description="IO 2048-bit으로 2배 확장, 2026 양산 예정"
    ),
}


# ============================================================
# AI Model Architecture Reference
# ============================================================

@dataclass
class AIModelSpec:
    """주요 AI 모델 사양"""
    name: str
    family: str
    vendor: str
    parameter_count_billion: float
    architecture: str
    context_length: int
    training_compute_pflop_days: Optional[float]
    training_tokens_trillion: Optional[float]
    inference_memory_fp16_gb: float
    inference_memory_int8_gb: float
    inference_memory_int4_gb: float
    typical_latency_ms: Optional[float]    # per token @ INT8
    typical_throughput_tps: Optional[float] # tokens/sec @ INT8
    release_year: int
    license_type: str
    description: str


AI_MODELS: dict[str, AIModelSpec] = {
    "llama3_70b": AIModelSpec(
        name="Llama 3 70B",
        family="Llama 3",
        vendor="Meta",
        parameter_count_billion=70,
        architecture="Decoder-only Transformer, GQA",
        context_length=8192,
        training_compute_pflop_days=6400,
        training_tokens_trillion=15,
        inference_memory_fp16_gb=140,
        inference_memory_int8_gb=70,
        inference_memory_int4_gb=35,
        typical_latency_ms=25,
        typical_throughput_tps=80,
        release_year=2024,
        license_type="Llama 3 Community License",
        description="오픈소스 LLM 최강급, GPT-3.5 Turbo 수준"
    ),
    "llama3_8b": AIModelSpec(
        name="Llama 3 8B",
        family="Llama 3",
        vendor="Meta",
        parameter_count_billion=8,
        architecture="Decoder-only Transformer, GQA",
        context_length=8192,
        training_compute_pflop_days=750,
        training_tokens_trillion=15,
        inference_memory_fp16_gb=16,
        inference_memory_int8_gb=8,
        inference_memory_int4_gb=4,
        typical_latency_ms=8,
        typical_throughput_tps=250,
        release_year=2024,
        license_type="Llama 3 Community License",
        description="엣지/모바일 배포용 경량 모델"
    ),
    "gpt4": AIModelSpec(
        name="GPT-4",
        family="GPT",
        vendor="OpenAI",
        parameter_count_billion=1800,
        architecture="MoE Transformer (추정, 8×220B)",
        context_length=128000,
        training_compute_pflop_days=None,
        training_tokens_trillion=13,
        inference_memory_fp16_gb=3600,
        inference_memory_int8_gb=1800,
        inference_memory_int4_gb=900,
        typical_latency_ms=None,
        typical_throughput_tps=None,
        release_year=2023,
        license_type="Proprietary (API only)",
        description="최대 상용 LLM, MoE 아키텍처 추정"
    ),
    "mixtral_8x7b": AIModelSpec(
        name="Mixtral 8x7B",
        family="Mixtral",
        vendor="Mistral AI",
        parameter_count_billion=47,
        architecture="Sparse MoE (8 experts × 7B, top-2 routing)",
        context_length=32768,
        training_compute_pflop_days=None,
        training_tokens_trillion=None,
        inference_memory_fp16_gb=94,
        inference_memory_int8_gb=47,
        inference_memory_int4_gb=24,
        typical_latency_ms=15,
        typical_throughput_tps=120,
        release_year=2024,
        license_type="Apache 2.0",
        description="MoE로 추론 시 12.9B 활성, 70B급 성능"
    ),
    "stable_diffusion_xl": AIModelSpec(
        name="Stable Diffusion XL",
        family="Stable Diffusion",
        vendor="Stability AI",
        parameter_count_billion=6.6,
        architecture="Latent Diffusion (UNet + VAE + CLIP)",
        context_length=0,
        training_compute_pflop_days=None,
        training_tokens_trillion=None,
        inference_memory_fp16_gb=13,
        inference_memory_int8_gb=7,
        inference_memory_int4_gb=4,
        typical_latency_ms=3000,
        typical_throughput_tps=None,
        release_year=2023,
        license_type="Open (CreativeML)",
        description="이미지 생성 표준 모델, 1024×1024"
    ),
}


# ============================================================
# Compute Intensity Reference
# ============================================================

@dataclass
class WorkloadProfile:
    """워크로드 특성 프로파일"""
    name: str
    category: str  # LLM_TRAINING, LLM_INFERENCE, IMAGE_GEN, RECOMMENDATION, SCIENTIFIC
    arithmetic_intensity_flop_per_byte: float
    bottleneck: str  # "MEMORY_BOUND", "COMPUTE_BOUND", "IO_BOUND"
    typical_batch_size: tuple[int, int]
    precision: str
    memory_footprint_scaling: str
    description: str


WORKLOAD_PROFILES: dict[str, WorkloadProfile] = {
    "llm_training": WorkloadProfile(
        name="LLM Training",
        category="LLM_TRAINING",
        arithmetic_intensity_flop_per_byte=150,
        bottleneck="COMPUTE_BOUND",
        typical_batch_size=(256, 4096),
        precision="BF16 / FP32 (mixed precision)",
        memory_footprint_scaling="16B × params (Adam: weights + gradients + 2 optimizer states)",
        description="대규모 병렬 학습, AllReduce 통신 바운드"
    ),
    "llm_prefill": WorkloadProfile(
        name="LLM Inference - Prefill",
        category="LLM_INFERENCE",
        arithmetic_intensity_flop_per_byte=50,
        bottleneck="COMPUTE_BOUND",
        typical_batch_size=(1, 64),
        precision="INT8 / FP8",
        memory_footprint_scaling="2B × params (INT8) + KV cache",
        description="프롬프트 처리 단계, 큰 행렬 연산 지배적"
    ),
    "llm_decode": WorkloadProfile(
        name="LLM Inference - Decode",
        category="LLM_INFERENCE",
        arithmetic_intensity_flop_per_byte=1,
        bottleneck="MEMORY_BOUND",
        typical_batch_size=(1, 256),
        precision="INT8 / INT4",
        memory_footprint_scaling="KV cache = 2 × layers × heads × head_dim × seq_len × batch",
        description="토큰 생성 단계, 메모리 대역폭 바운드 (작은 행렬-벡터 곱)"
    ),
    "image_generation": WorkloadProfile(
        name="Image Generation (Diffusion)",
        category="IMAGE_GEN",
        arithmetic_intensity_flop_per_byte=80,
        bottleneck="COMPUTE_BOUND",
        typical_batch_size=(1, 8),
        precision="FP16",
        memory_footprint_scaling="UNet + VAE + Scheduler states",
        description="반복적 denoising, 20-50 step 연산"
    ),
    "recommendation": WorkloadProfile(
        name="Recommendation (DLRM)",
        category="RECOMMENDATION",
        arithmetic_intensity_flop_per_byte=0.5,
        bottleneck="MEMORY_BOUND",
        typical_batch_size=(1024, 65536),
        precision="FP32 (embeddings) + INT8 (MLP)",
        memory_footprint_scaling="임베딩 테이블 지배적 (수백 GB)",
        description="대형 임베딩 룩업, 메모리 용량/대역폭 바운드"
    ),
}


# ============================================================
# Lookup Interface
# ============================================================

class AIIndustryOntology:
    """AI 산업 도메인 온톨로지 통합 인터페이스"""

    @staticmethod
    def get_all_accelerators() -> dict[str, AIAcceleratorSpec]:
        return AI_ACCELERATORS

    @staticmethod
    def get_accelerator(name: str) -> Optional[AIAcceleratorSpec]:
        return AI_ACCELERATORS.get(name)

    @staticmethod
    def get_accelerators_by_vendor(vendor: AcceleratorVendor) -> list[AIAcceleratorSpec]:
        return [a for a in AI_ACCELERATORS.values() if a.vendor == vendor]

    @staticmethod
    def get_all_hbm() -> dict[str, HBMSpec]:
        return HBM_GENERATIONS

    @staticmethod
    def get_hbm(generation: str) -> Optional[HBMSpec]:
        return HBM_GENERATIONS.get(generation)

    @staticmethod
    def get_all_models() -> dict[str, AIModelSpec]:
        return AI_MODELS

    @staticmethod
    def get_model(name: str) -> Optional[AIModelSpec]:
        return AI_MODELS.get(name)

    @staticmethod
    def get_workload_profiles() -> dict[str, WorkloadProfile]:
        return WORKLOAD_PROFILES

    @staticmethod
    def estimate_inference_hardware(
        model_params_billion: float,
        precision: str = "INT8",
        target_throughput_tps: Optional[float] = None
    ) -> dict:
        """
        모델 추론에 필요한 하드웨어 추정

        Rule of thumb:
        - FP16: 2 bytes/param → memory = 2 × params
        - INT8: 1 byte/param → memory = params
        - INT4: 0.5 bytes/param → memory = 0.5 × params
        - KV cache: ~10-30% of model memory (sequence length dependent)
        """
        bytes_per_param = {"FP32": 4, "FP16": 2, "BF16": 2, "INT8": 1, "INT4": 0.5, "FP8": 1}
        bpp = bytes_per_param.get(precision, 1)

        model_memory_gb = model_params_billion * bpp
        kv_cache_gb = model_memory_gb * 0.2  # 20% 추정
        total_memory_gb = model_memory_gb + kv_cache_gb

        # 적합한 가속기 추천
        suitable = []
        for name, acc in AI_ACCELERATORS.items():
            if acc.memory.capacity_gb >= total_memory_gb:
                suitable.append({
                    "accelerator": name,
                    "gpus_needed": 1,
                    "memory_utilization_pct": round(total_memory_gb / acc.memory.capacity_gb * 100, 1),
                })
            elif acc.memory.capacity_gb >= total_memory_gb / 2:
                suitable.append({
                    "accelerator": name,
                    "gpus_needed": 2,
                    "memory_utilization_pct": round(total_memory_gb / (acc.memory.capacity_gb * 2) * 100, 1),
                })
            elif acc.memory.capacity_gb >= total_memory_gb / 4:
                suitable.append({
                    "accelerator": name,
                    "gpus_needed": 4,
                    "memory_utilization_pct": round(total_memory_gb / (acc.memory.capacity_gb * 4) * 100, 1),
                })
            elif acc.memory.capacity_gb >= total_memory_gb / 8:
                suitable.append({
                    "accelerator": name,
                    "gpus_needed": 8,
                    "memory_utilization_pct": round(total_memory_gb / (acc.memory.capacity_gb * 8) * 100, 1),
                })

        return {
            "model_params_billion": model_params_billion,
            "precision": precision,
            "model_memory_gb": round(model_memory_gb, 1),
            "kv_cache_estimate_gb": round(kv_cache_gb, 1),
            "total_memory_gb": round(total_memory_gb, 1),
            "suitable_hardware": sorted(suitable, key=lambda x: x["gpus_needed"]),
        }
