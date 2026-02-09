"""
LLM-based Structured Data Extractor v2

웹에서 수집한 원시 텍스트를 LLM(Claude API)을 사용하여
그래프 DB 노드/관계 형태의 구조화된 데이터로 변환.

v2 개선사항:
- 토픽별 맞춤 프롬프트 템플릿
- 소스 신뢰도 기반 우선순위 컨텍스트 윈도잉
- 멀티패스 추출 (노드 → 관계)
- 강화된 JSON 파싱 + 구조 검증

지원 LLM:
- Anthropic Claude (기본)
- 폴백: 내장 도메인 지식 기반 추출 (API 키 없을 때)
"""

import json
import os
import re
from typing import Optional

try:
    import anthropic
except ImportError:
    anthropic = None


# ─────────────────────────────────────────────────────
# Topic-Specific Prompt Templates — 토픽별 맞춤 프롬프트
# ─────────────────────────────────────────────────────

TOPIC_PROMPT_TEMPLATES = {
    "foundry_fabsite": {
        "domain_context": """You are extracting data about semiconductor foundries and their fabrication facilities.
Key entities: Foundry companies (TSMC, Samsung, Intel, GlobalFoundries, SMIC, UMC) and individual fab sites.
For Foundry: extract revenue, market share, HQ, country, wafer capacity (KWPM), employee count, fab count.
For FabSite: extract location, wafer capacity (WSPM), process nodes supported, construction status, investment amount (B USD), opening year.
Use exact process node names: N5, N4P, N3E, N3P, N2, A16, SF3, SF2, Intel_18A, Intel_20A.""",
        "extraction_hints": [
            "Look for specific fab numbers (Fab 18, Fab 21, etc.) and their locations",
            "Capacity is in 'wafers per month' (WPM/WSPM) or 'K WPM'",
            "Track CHIPS Act / EU Chips Act funding tied to specific fabs",
            "Status: ACTIVE, UNDER_CONSTRUCTION, PLANNED",
        ],
    },
    "process_generation": {
        "domain_context": """You are extracting semiconductor transistor architecture generations.
Key transitions: Planar -> FinFET -> GAA (Nanosheet/RibbonFET/MBCFET) -> CFET.
Also track BSPDN (Backside Power Delivery) adoption.
For ProcessGeneration: extract transistor type, era, minimum node (nm), who introduced it.
Link to existing process nodes: N3E/N3P=FinFET, N2/A16/SF2=GAA, Intel_20A/18A=RibbonFET(GAA).""",
        "extraction_hints": [
            "IRDS roadmap data contains density/performance targets",
            "Note EUV layers per node (single vs double patterning)",
            "Track BSPDN adoption: TSMC A16 (Super Power Rail), Intel 20A/18A (PowerVia)",
            "CFET is R&D stage — extract research milestones",
        ],
    },
    "memory_standard": {
        "domain_context": """You are extracting JEDEC memory standard specifications.
Standards: DDR5, LPDDR5/5X, GDDR6X/GDDR7, HBM3/HBM3E/HBM4, CXL memory.
For each: extract JEDEC standard ID, speed (MT/s or GT/s), bandwidth (GB/s), voltage, channel width, burst length.
Note: HBM nodes already exist (HBM3, HBM3E). Create MemoryStandard nodes for non-HBM specs.""",
        "extraction_hints": [
            "Speeds in MT/s (megatransfers) or GT/s (GDDR7 PAM4)",
            "HBM4 may have preliminary/draft specs — mark confidence accordingly",
            "CXL 3.0/3.1 memory expansion specs are relevant",
            "LPDDR6 draft specs may be available",
        ],
    },
    "interconnect_standard": {
        "domain_context": """You are extracting chip-to-chip interconnect standards.
Standards: PCIe 5.0/6.0/7.0, CXL 3.0/3.1, UCIe 1.1/2.0, NVLink 5.0, AMD Infinity Fabric, UALink 1.0.
For each: extract version, bandwidth (GT/s and GB/s), encoding, max lanes, year, features.""",
        "extraction_hints": [
            "PCIe 7.0 is in development — extract timeline if available",
            "UALink is an open standard consortium (AMD, Google, Intel, Meta, Microsoft, Broadcom)",
            "CXL is based on PCIe PHY — note the base spec",
            "Link bandwidth to existing AI accelerators (H100, B200, MI300X)",
        ],
    },
    "packaging_detail": {
        "domain_context": """You are extracting advanced semiconductor packaging substrate and interconnect technologies.
Focus on: substrate types (ABF, silicon interposer, glass core, FC-BGA), bonding (hybrid Cu-Cu, micro-bump).
Link to existing packaging tech nodes: CoWoS-S, CoWoS-L, EMIB, InFO, Foveros, SoIC.""",
        "extraction_hints": [
            "Extract line/space dimensions (um), TSV pitch, layer count",
            "Glass core substrate is emerging (Absolics/SKC, Intel)",
            "Hybrid bonding pitch is approaching sub-1um",
            "Note capacity constraints (CoWoS supply shortage)",
        ],
    },
    "equipment_ecosystem": {
        "domain_context": """You are extracting semiconductor equipment vendor and model data.
Vendors: ASML, Applied Materials, Lam Research, Tokyo Electron, KLA.
For EquipmentVendor: extract revenue, market share, country, segment.
For EquipmentModel: extract category (LITHO/ETCH/DEP/INSP), throughput (WPH), resolution, price, generation.""",
        "extraction_hints": [
            "ASML EUV: NXE:3600D, NXE:3800E, EXE:5000 (High-NA), EXE:5200",
            "Track High-NA EUV adoption timeline",
            "Equipment categories: LITHOGRAPHY, ETCH, DEPOSITION, CMP, INSPECTION, METROLOGY",
            "Note equipment restrictions (US/Japan export controls to China)",
        ],
    },
    "material_suppliers": {
        "domain_context": """You are extracting semiconductor material supplier data.
Categories: photoresist (EUV/ArF/KrF), specialty gas, CMP slurry, silicon wafer, photomask blank.
For MaterialSupplier: extract country, specialization, market share, revenue.
Link suppliers to existing Material nodes and HBM generations.""",
        "extraction_hints": [
            "Key Japanese suppliers: JSR, TOK, Shin-Etsu, SUMCO",
            "Memory suppliers (SK Hynix, Samsung, Micron) and their HBM market share",
            "EUV photoresist is a critical chokepoint",
            "Track supply chain dependencies and single-source risks",
        ],
    },
    "design_ip": {
        "domain_context": """You are extracting semiconductor design IP and EDA tool data.
IP types: CPU cores (ARM Cortex, RISC-V), GPU IP, NPU IP, SerDes PHY, PCIe PHY.
EDA vendors: Synopsys, Cadence, Siemens EDA.
For DesignIP: extract vendor, type, architecture, data rate, target application.""",
        "extraction_hints": [
            "ARM Cortex-X series for premium mobile, Neoverse for servers",
            "RISC-V adoption tracking (SiFive, Andes, Ventana)",
            "224G SerDes PHY is next-gen (Synopsys, Cadence, Alphawave)",
            "EDA market is highly concentrated (Synopsys+Cadence ~70%)",
        ],
    },
    "company_landscape": {
        "domain_context": """You are extracting the semiconductor company ecosystem.
Categories: FABLESS (NVIDIA, AMD, Qualcomm, Broadcom, MediaTek, Apple), IDM (Intel, Samsung, TI), OSAT (ASE, Amkor, JCET).
For Company: extract type, country, HQ, revenue, market cap, focus areas, founded year.""",
        "extraction_hints": [
            "Company types: FABLESS, IDM, FOUNDRY, OSAT",
            "Track revenue and market cap for major players",
            "Link companies to their products (AI accelerators, etc.)",
            "Note M&A activity and strategic partnerships",
        ],
    },
    "benchmark_performance": {
        "domain_context": """You are extracting AI/semiconductor benchmark data.
Benchmarks: MLPerf Training/Inference, TOPS/Watt efficiency, memory bandwidth.
For Benchmark: extract category, metric unit, organization.
Link AI accelerators to benchmark scores with specific values.""",
        "extraction_hints": [
            "MLPerf has specific round numbers — note the round/version",
            "TOPS/Watt for INT8 precision is the standard efficiency metric",
            "Include both absolute performance and per-watt efficiency",
            "Track latest MLPerf results (2025-2026 rounds)",
        ],
    },
    "reliability_testing": {
        "domain_context": """You are extracting semiconductor reliability testing standards and methods.
Tests: HTOL, HAST, Temperature Cycling, ESD (HBM/CDM), Electromigration, TDDB, AEC-Q100.
For ReliabilityTest: extract standard ID, type, duration, temperature, pass criteria.""",
        "extraction_hints": [
            "JEDEC standards: JESD22 series for reliability tests",
            "AEC-Q100 has 4 temperature grades (Grade 0 to Grade 3)",
            "Advanced nodes face new reliability challenges (self-heating, BTI)",
        ],
    },
    "industry_standards": {
        "domain_context": """You are extracting semiconductor industry standards.
Organizations: JEDEC, SEMI, IEEE, AEC.
For Standard: extract organization, standard ID, scope, version, year.""",
        "extraction_hints": [
            "SEMI E10/E79 for fab equipment efficiency metrics",
            "JEDEC standards for memory interfaces",
            "Track standard updates and new releases",
        ],
    },
    "application_segments": {
        "domain_context": """You are extracting semiconductor application segment requirements.
Segments: Data Center (Training/Inference), Edge AI, Automotive ADAS, Mobile AI, HPC.
For Application: extract segment, workload type, compute/memory/power requirements.""",
        "extraction_hints": [
            "Data center training: FP8/BF16 PFLOPS, HBM 192GB+, NVLink",
            "Edge AI: 10-100 TOPS, <15W, LPDDR",
            "Automotive: AEC-Q100, ASIL-D safety, 100-1000 TOPS",
            "Link applications to specific AI accelerators",
        ],
    },
    "thermal_power": {
        "domain_context": """You are extracting thermal and power management solutions for semiconductors.
Solutions: air cooling, direct liquid cooling (DLC), single-phase immersion, two-phase immersion.
For ThermalSolution: extract type, max TDP (W), thermal resistance, coolant type.""",
        "extraction_hints": [
            "AI chips now exceed 1000W TDP (B200: ~1000W)",
            "Direct liquid cooling is becoming data center standard",
            "Track power delivery network (PDN) innovations",
            "Immersion cooling adoption rate in hyperscalers",
        ],
    },
    "regulation_geopolitics": {
        "domain_context": """You are extracting semiconductor regulation and geopolitics data.
Regulations: US Export Controls (2022/2023), CHIPS Act, EU Chips Act, Japan export controls.
For Regulation: extract jurisdiction, type (EXPORT_CONTROL/SUBSIDY), effective year, targets, funding amounts.""",
        "extraction_hints": [
            "US BIS export controls target China — track threshold changes",
            "CHIPS Act: $52.7B total, $39B manufacturing, track individual awards",
            "Track China's domestic semiconductor efforts despite restrictions",
            "Note Japan/Netherlands alignment with US export controls",
        ],
    },
    "inspection_metrology": {
        "domain_context": """You are extracting semiconductor inspection and metrology method data.
Methods: broadband plasma, e-beam, CD-SEM, OCD scatterometry, overlay metrology.
For InspectionMethod: extract equipment type, vendor, resolution, throughput, measurement capabilities.""",
        "extraction_hints": [
            "KLA dominates inspection/metrology market",
            "E-beam is highest resolution but lowest throughput",
            "AI/ML-powered defect classification is emerging",
            "Track metrology challenges for GAA/sub-2nm nodes",
        ],
    },
}


class LLMExtractor:
    """LLM 기반 구조화 데이터 추출기"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key and anthropic:
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    # ─────────────────────────────────────────────────────
    # Main Extraction
    # ─────────────────────────────────────────────────────

    def extract_for_topic(
        self,
        topic_id: str,
        tier: str,
        node_labels: list[str],
        relationship_types: list[str],
        context: str = "",
        description: str = "",
        raw_sources: Optional[list[dict]] = None,
    ) -> dict:
        """
        토픽에 맞는 구조화 데이터 추출.

        Args:
            raw_sources: 원시 수집 데이터 리스트 (우선순위 컨텍스트 빌딩에 사용)

        Returns:
            {
                "nodes": [{"key": "...", "label": "...", "properties": {...}}, ...],
                "relationships": [{"from_key": "...", "to_key": "...", "type": "...", "properties": {...}}, ...]
            }
        """
        # raw_sources가 있으면 우선순위 기반 컨텍스트 빌딩
        if raw_sources:
            context = self._build_prioritized_context(raw_sources, max_chars=20000)

        # LLM API 사용 가능 + 충분한 컨텍스트 → 멀티패스 추출
        if self.client and context and len(context) > 5000:
            return self._extract_with_llm_multipass(
                topic_id, tier, node_labels, relationship_types, context, description
            )

        # LLM API 사용 가능 + 소규모 컨텍스트 → 단일패스 추출
        if self.client and context and len(context) > 100:
            return self._extract_with_llm(
                topic_id, tier, node_labels, relationship_types, context, description
            )

        # 폴백: 내장 도메인 지식 + 웹 수집 데이터 보강
        has_web_data = context and len(context) > 100
        if has_web_data:
            print(f"    Using built-in knowledge + web data enrichment ({len(context):,} chars collected)")
        else:
            print("    Using built-in domain knowledge only (no web data)")

        base_data = self._extract_with_builtin_knowledge(topic_id, tier, node_labels, relationship_types)

        # 웹 데이터가 있으면 보강
        if has_web_data:
            base_data = self._enrich_with_web_data(base_data, context, topic_id)

        return base_data

    # ─────────────────────────────────────────────────────
    # LLM Extraction
    # ─────────────────────────────────────────────────────

    def _extract_with_llm(
        self,
        topic_id: str,
        tier: str,
        node_labels: list[str],
        relationship_types: list[str],
        context: str,
        description: str,
    ) -> dict:
        """Claude API를 사용한 단일패스 구조화 추출"""
        prompt = self._build_extraction_prompt(
            topic_id, tier, node_labels, relationship_types, context, description
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.content[0].text
            return self._parse_llm_response(response_text)
        except Exception as e:
            print(f"    ⚠ LLM extraction failed: {e}")
            return self._extract_with_builtin_knowledge(topic_id, tier, node_labels, relationship_types)

    def _extract_with_llm_multipass(
        self,
        topic_id: str,
        tier: str,
        node_labels: list[str],
        relationship_types: list[str],
        context: str,
        description: str,
    ) -> dict:
        """
        멀티패스 추출: Pass 1 (노드) → Pass 2 (관계)

        컨텍스트가 충분할 때 사용. 관계 추출 정확도를 높인다.
        """
        # Pass 1: 노드 추출
        pass1_prompt = self._build_extraction_prompt(
            topic_id, tier, node_labels, relationship_types, context, description
        )
        pass1_prompt += (
            "\n\n## IMPORTANT: PASS 1 — FOCUS ON NODES\n"
            "In this pass, focus on extracting comprehensive 'nodes' with all properties.\n"
            "Include relationships you are confident about, but prioritize completeness of nodes."
        )

        try:
            print("    LLM Pass 1/2: Extracting nodes...")
            resp1 = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[{"role": "user", "content": pass1_prompt}],
            )
            pass1_data = self._parse_llm_response(resp1.content[0].text)
        except Exception as e:
            print(f"    ⚠ Pass 1 failed, falling back to single-pass: {e}")
            return self._extract_with_llm(
                topic_id, tier, node_labels, relationship_types, context, description
            )

        nodes = pass1_data.get("nodes", [])
        if not nodes:
            return pass1_data

        # Pass 2: 노드 목록을 기반으로 관계 추출
        node_summary = json.dumps(
            [{"key": n["key"], "label": n["label"], "name": n.get("name", "")} for n in nodes],
            ensure_ascii=False,
        )

        pass2_prompt = f"""You are a semiconductor industry knowledge graph expert.

## Task
Given extracted nodes and source context, create comprehensive relationships between them.

## Extracted Nodes
{node_summary}

## Existing Graph Nodes (common keys for cross-references)
ProcessNode: N3E, N5, N4P, N7, N2, A16, SF3, SF2, Intel_18A, Intel_20A
PackagingTech: CoWoS-S, CoWoS-L, EMIB, InFO, Foveros, SoIC
HBMGeneration: HBM3, HBM3E, HBM4
AIAccelerator: H100_SXM, H200_SXM, B200, MI300X, MI325X, Gaudi3, TPUv5e
Material: EUV_RESIST, ARF_RESIST, NF3, WF6

## Allowed Relationship Types
{json.dumps(relationship_types)}

## Context (abbreviated)
{context[:10000]}

## Instructions
1. Create relationships between the extracted nodes
2. Also create cross-references to existing graph nodes where appropriate
3. Each relationship must have from_key, to_key, type, and properties
4. Include meaningful properties on relationships (e.g., capacity, funding amount)

## Response Format
Return ONLY valid JSON:
{{"relationships": [...]}}"""

        try:
            print("    LLM Pass 2/2: Extracting relationships...")
            resp2 = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": pass2_prompt}],
            )
            pass2_data = self._parse_llm_response(resp2.content[0].text)
            # Pass 1의 관계 + Pass 2의 관계를 병합 (중복 제거)
            pass1_rels = pass1_data.get("relationships", [])
            pass2_rels = pass2_data.get("relationships", [])
            seen_rels = set()
            merged_rels = []
            for rel in pass1_rels + pass2_rels:
                rel_key = (rel.get("from_key"), rel.get("to_key"), rel.get("type"))
                if rel_key not in seen_rels:
                    merged_rels.append(rel)
                    seen_rels.add(rel_key)
            return {"nodes": nodes, "relationships": merged_rels}
        except Exception as e:
            print(f"    ⚠ Pass 2 failed, using Pass 1 relationships: {e}")
            return pass1_data

    def _build_extraction_prompt(
        self,
        topic_id: str,
        tier: str,
        node_labels: list[str],
        relationship_types: list[str],
        context: str,
        description: str,
    ) -> str:
        """토픽별 맞춤 추출 프롬프트 생성"""
        template = TOPIC_PROMPT_TEMPLATES.get(topic_id, {})
        domain_context = template.get("domain_context", "")
        hints = template.get("extraction_hints", [])
        hints_str = "\n".join(f"- {h}" for h in hints) if hints else ""

        return f"""You are a semiconductor industry data extraction expert.
Your task is to extract structured graph database entities from research data.

## Topic
- ID: {topic_id}
- Tier: {tier}
- Description: {description}

## Domain Context
{domain_context}

## Target Schema
Node Labels: {json.dumps(node_labels)}
Relationship Types: {json.dumps(relationship_types)}

## Node Format
Each node MUST have:
- "key": unique identifier (UPPERCASE_WITH_UNDERSCORES, e.g., "TSMC", "TSMC_FAB_18")
- "label": one of {json.dumps(node_labels)}
- "name": human-readable name
- "properties": dict with:
  - All available factual properties (location, capacity, revenue, specs, etc.)
  - "confidence": float 0.0-1.0 (how confident in this data)
  - "source_date": approximate date if identifiable (e.g., "2025-Q3", "2026")

## Relationship Format
Each relationship MUST have:
- "from_key": source node key
- "to_key": target node key
- "type": one of {json.dumps(relationship_types)}
- "properties": dict of edge properties (can be empty {{}})

## Extraction Hints
{hints_str}

## Important Rules
1. Extract ALL relevant entities from the context
2. Use REAL, FACTUAL data — do NOT fabricate specifications or numbers
3. Create relationships to existing graph nodes:
   ProcessNode: N3E, N5, N4P, N7, N2, A16, SF3, SF2, Intel_18A, Intel_20A
   PackagingTech: CoWoS-S, CoWoS-L, EMIB, InFO, Foveros, SoIC
   HBMGeneration: HBM3, HBM3E, HBM4
   AIAccelerator: H100_SXM, H200_SXM, B200, MI300X, MI325X, Gaudi3, TPUv5e
4. When data conflicts between sources, prefer the most recent source
5. Include "confidence" (0.0-1.0) in each node's properties

## Context Data
{context}

## Response Format
Return ONLY valid JSON (no markdown, no explanation):
{{
    "nodes": [...],
    "relationships": [...]
}}
"""

    def _build_prioritized_context(
        self, raw_items: list[dict], max_chars: int = 20000
    ) -> str:
        """소스 신뢰도 기반 우선순위 컨텍스트 조립"""
        from .web_scraper import SOURCE_RELIABILITY_SCORES

        # 각 소스에 점수 부여
        scored_items = []
        for item in raw_items:
            reliability = SOURCE_RELIABILITY_SCORES.get(item.get("type", "general"), 0.4)
            is_news = item.get("_is_news", False)
            freshness_bonus = 0.15 if is_news else 0.0
            score = reliability + freshness_bonus
            scored_items.append((score, item))

        # 점수 내림차순 정렬
        scored_items.sort(key=lambda x: x[0], reverse=True)

        # max_chars까지 조립
        parts = []
        total = 0
        for score, item in scored_items:
            content = item.get("content", "")
            if not content:
                continue
            source = item.get("source", "unknown")
            header = f"[Source: {source} | reliability={score:.2f}]"
            entry = f"{header}\n{content}"

            if total + len(entry) > max_chars:
                remaining = max_chars - total - len(header) - 10
                if remaining > 200:
                    parts.append(f"{header}\n{content[:remaining]}...")
                break

            parts.append(entry)
            total += len(entry) + 10

        return "\n\n---\n\n".join(parts)

    def _parse_llm_response(self, response_text: str) -> dict:
        """LLM 응답에서 JSON 추출 — 3단계 파싱 + 구조 검증"""
        text = response_text.strip()

        data = None

        # Strategy 1: 직접 JSON 파싱
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: markdown 코드블록에서 추출
        if data is None:
            json_block = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
            if json_block:
                try:
                    data = json.loads(json_block.group(1))
                except json.JSONDecodeError:
                    pass

        # Strategy 3: 중괄호 깊이 탐색으로 최외곽 JSON 객체 추출
        if data is None:
            brace_depth = 0
            start = -1
            for i, ch in enumerate(text):
                if ch == '{':
                    if brace_depth == 0:
                        start = i
                    brace_depth += 1
                elif ch == '}':
                    brace_depth -= 1
                    if brace_depth == 0 and start >= 0:
                        try:
                            data = json.loads(text[start:i + 1])
                            break
                        except json.JSONDecodeError:
                            start = -1

        if data is None:
            return {"nodes": [], "relationships": []}

        if "nodes" not in data:
            data["nodes"] = []
        if "relationships" not in data:
            data["relationships"] = []

        # 노드 구조 유효성 검증
        valid_nodes = []
        for node in data["nodes"]:
            if isinstance(node, dict) and node.get("key") and node.get("label"):
                if "name" not in node:
                    node["name"] = node["key"]
                if "properties" not in node:
                    node["properties"] = {}
                valid_nodes.append(node)
        data["nodes"] = valid_nodes

        return data

    # ─────────────────────────────────────────────────────
    # Web Data Enrichment (규칙 기반)
    # ─────────────────────────────────────────────────────

    def _enrich_with_web_data(self, base_data: dict, context: str, topic_id: str) -> dict:
        """
        웹에서 수집한 텍스트로 빌트인 데이터를 보강.

        - Wikipedia 인포박스에서 숫자 속성 업데이트
        - 본문에서 새로운 엔티티 발견 시 노드 추가
        - 수집 소스 정보를 각 노드에 태깅
        """
        import re

        nodes = base_data.get("nodes", [])
        relationships = base_data.get("relationships", [])
        existing_keys = {n["key"] for n in nodes}

        # 1. 기존 노드의 속성을 웹 데이터로 보강
        for node in nodes:
            props = node.get("properties", {})

            # Wikipedia 인포박스에서 매칭되는 데이터 추출
            # Revenue 패턴
            revenue_patterns = [
                rf"{re.escape(node.get('name', ''))}.*?(?:revenue|Revenue).*?\$([\d.]+)\s*(?:billion|B)",
                rf"(?:revenue|Revenue).*?\$([\d.]+)\s*(?:billion|B).*?{re.escape(node.get('name', ''))}",
            ]
            for pat in revenue_patterns:
                match = re.search(pat, context, re.IGNORECASE)
                if match:
                    try:
                        props["revenue_b_usd_web"] = float(match.group(1))
                    except ValueError:
                        pass
                    break

            # Founded year 패턴
            founded_match = re.search(
                rf"{re.escape(node.get('name', ''))}.*?(?:founded|Founded|established).*?(\d{{4}})",
                context, re.IGNORECASE
            )
            if founded_match:
                try:
                    year = int(founded_match.group(1))
                    if 1900 < year < 2030:
                        props["founded_year_web"] = year
                except ValueError:
                    pass

            # Employees 패턴
            emp_match = re.search(
                rf"{re.escape(node.get('name', ''))}.*?(?:employees|Employees).*?([\d,]+)",
                context, re.IGNORECASE
            )
            if emp_match:
                try:
                    props["employees_web"] = int(emp_match.group(1).replace(",", ""))
                except ValueError:
                    pass

            # 웹 수집 여부 태깅
            props["_web_enriched"] = True
            node["properties"] = props

        # 2. 토픽별 추가 엔티티 발견
        new_nodes, new_rels = self._discover_entities_from_context(context, topic_id, existing_keys)
        if new_nodes:
            nodes.extend(new_nodes)
            print(f"    + Discovered {len(new_nodes)} additional entities from web data")
        if new_rels:
            relationships.extend(new_rels)

        base_data["nodes"] = nodes
        base_data["relationships"] = relationships
        base_data["_enrichment"] = {
            "web_context_chars": len(context),
            "new_entities_found": len(new_nodes),
        }

        return base_data

    def _discover_entities_from_context(
        self, context: str, topic_id: str, existing_keys: set
    ) -> tuple[list[dict], list[dict]]:
        """웹 텍스트에서 아직 그래프에 없는 새로운 엔티티를 발견"""
        import re

        new_nodes = []
        new_rels = []

        # 파운드리/팹 토픽: 추가 팹 사이트 발견
        if topic_id == "foundry_fabsite":
            # "Fab [number]" 또는 "[Company] [Location] fab" 패턴
            fab_mentions = re.findall(
                r"(?:Fab|FAB|fab)\s*(\d+[A-Z]?)\s+(?:in\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
                context
            )
            for fab_num, location in fab_mentions:
                key = f"FAB_{fab_num}_{location.upper().replace(' ', '_')}"
                if key not in existing_keys:
                    new_nodes.append({
                        "key": key,
                        "label": "FabSite",
                        "name": f"Fab {fab_num} ({location})",
                        "properties": {
                            "location": location,
                            "fab_number": fab_num,
                            "_source": "web_discovery",
                        },
                    })
                    existing_keys.add(key)

        # 장비 토픽: 장비 모델명 발견
        elif topic_id == "equipment_ecosystem":
            # ASML NXE/NXT, LAM Kiyo 등 장비 모델 패턴
            equip_patterns = [
                (r"(NXE[:\s-]*\d+\w*)", "ASML", "EquipmentModel"),
                (r"(NXT[:\s-]*\d+\w*)", "ASML", "EquipmentModel"),
                (r"(TWINSCAN\s+\w+)", "ASML", "EquipmentModel"),
            ]
            for pattern, vendor, label in equip_patterns:
                for match in re.finditer(pattern, context):
                    model_name = match.group(1).strip()
                    key = f"{vendor}_{model_name.upper().replace(' ', '_').replace(':', '_')}"
                    if key not in existing_keys:
                        new_nodes.append({
                            "key": key,
                            "label": label,
                            "name": f"{vendor} {model_name}",
                            "properties": {
                                "vendor_key": vendor.upper(),
                                "model": model_name,
                                "_source": "web_discovery",
                            },
                        })
                        new_rels.append({
                            "from_key": vendor.upper(),
                            "to_key": key,
                            "type": "MANUFACTURES_EQUIP",
                            "properties": {},
                        })
                        existing_keys.add(key)

        # 기업 토픽: 새로운 회사 발견
        elif topic_id == "company_landscape":
            # "company" 관련 패턴에서 대문자로 시작하는 기업명
            known_companies = {
                "NVIDIA", "AMD", "Intel", "TSMC", "Samsung", "Qualcomm",
                "Broadcom", "Texas Instruments", "SK Hynix", "Micron",
                "MediaTek", "Apple", "Google", "Amazon", "Microsoft",
                "Marvell", "Xilinx", "Analog Devices",
            }
            for company in known_companies:
                if company.lower() in context.lower() and company.upper().replace(" ", "_") not in existing_keys:
                    key = company.upper().replace(" ", "_")
                    # 기업 유형 추정
                    company_type = "FABLESS"
                    if any(kw in context.lower() for kw in [f"{company.lower()} foundry", f"{company.lower()} fab"]):
                        company_type = "IDM"
                    new_nodes.append({
                        "key": key,
                        "label": "Company",
                        "name": company,
                        "properties": {
                            "type": company_type,
                            "_source": "web_discovery",
                        },
                    })
                    existing_keys.add(key)

        return new_nodes, new_rels

    # ─────────────────────────────────────────────────────
    # Built-in Domain Knowledge Fallback
    # ─────────────────────────────────────────────────────

    def _extract_with_builtin_knowledge(
        self,
        topic_id: str,
        tier: str,
        node_labels: list[str],
        relationship_types: list[str],
    ) -> dict:
        """내장 도메인 지식 기반 데이터 생성 — LLM 없이도 동작"""
        extractor_map = {
            "foundry_fabsite": self._builtin_foundry_data,
            "process_generation": self._builtin_process_generation_data,
            "memory_standard": self._builtin_memory_standard_data,
            "interconnect_standard": self._builtin_interconnect_standard_data,
            "packaging_detail": self._builtin_packaging_detail_data,
            "equipment_ecosystem": self._builtin_equipment_ecosystem_data,
            "material_suppliers": self._builtin_material_supplier_data,
            "design_ip": self._builtin_design_ip_data,
            "company_landscape": self._builtin_company_landscape_data,
            "benchmark_performance": self._builtin_benchmark_data,
            "reliability_testing": self._builtin_reliability_data,
            "industry_standards": self._builtin_standards_data,
            "application_segments": self._builtin_application_data,
            "thermal_power": self._builtin_thermal_data,
            "regulation_geopolitics": self._builtin_regulation_data,
            "inspection_metrology": self._builtin_inspection_data,
        }

        extractor = extractor_map.get(topic_id)
        if extractor:
            return extractor()
        return {"nodes": [], "relationships": []}

    # ─────────────────────────────────────────────────────
    # Tier 1 Built-in Data
    # ─────────────────────────────────────────────────────

    def _builtin_foundry_data(self) -> dict:
        nodes = [
            {"key": "TSMC", "label": "Foundry", "name": "TSMC", "properties": {
                "full_name": "Taiwan Semiconductor Manufacturing Company",
                "country": "Taiwan", "hq": "Hsinchu, Taiwan",
                "founded_year": 1987, "fab_count": 16,
                "revenue_b_usd": 87.1, "market_share_pct": 61.7,
                "employees": 76000, "wafer_capacity_kwpm": 16000,
                "description": "세계 최대 파운드리, 순수 파운드리 모델의 선구자"
            }},
            {"key": "SAMSUNG_FOUNDRY", "label": "Foundry", "name": "Samsung Foundry", "properties": {
                "full_name": "Samsung Electronics Foundry Division",
                "country": "South Korea", "hq": "Hwaseong, South Korea",
                "founded_year": 2017, "fab_count": 6,
                "revenue_b_usd": 15.8, "market_share_pct": 11.3,
                "parent_company": "Samsung Electronics",
                "description": "IDM 겸 파운드리, GAA(MBCFET) 최초 양산"
            }},
            {"key": "INTEL_FOUNDRY", "label": "Foundry", "name": "Intel Foundry", "properties": {
                "full_name": "Intel Foundry Services (IFS)",
                "country": "United States", "hq": "Santa Clara, California",
                "founded_year": 2021, "fab_count": 8,
                "revenue_b_usd": 0.9, "market_share_pct": 0.6,
                "parent_company": "Intel Corporation",
                "description": "2021년 파운드리 사업부 분리, 18A부터 외부 고객 수주"
            }},
            {"key": "GLOBALFOUNDRIES", "label": "Foundry", "name": "GlobalFoundries", "properties": {
                "full_name": "GlobalFoundries Inc.",
                "country": "United States", "hq": "Malta, New York",
                "founded_year": 2009, "fab_count": 5,
                "revenue_b_usd": 7.4, "market_share_pct": 5.3,
                "description": "특수/아날로그 공정 집중 (12nm+), 첨단 공정 포기 (2018)"
            }},
            {"key": "SMIC", "label": "Foundry", "name": "SMIC", "properties": {
                "full_name": "Semiconductor Manufacturing International Corporation",
                "country": "China", "hq": "Shanghai, China",
                "founded_year": 2000, "fab_count": 7,
                "revenue_b_usd": 7.6, "market_share_pct": 5.4,
                "description": "중국 최대 파운드리, 미국 제재로 EUV 장비 도입 제한"
            }},
            {"key": "UMC", "label": "Foundry", "name": "UMC", "properties": {
                "full_name": "United Microelectronics Corporation",
                "country": "Taiwan", "hq": "Hsinchu, Taiwan",
                "founded_year": 1980, "fab_count": 11,
                "revenue_b_usd": 7.1, "market_share_pct": 5.0,
                "description": "성숙 노드 (22nm+) 전문, 자동차/IoT 시장 강점"
            }},
            # Fab Sites
            {"key": "TSMC_FAB_18", "label": "FabSite", "name": "TSMC Fab 18", "properties": {
                "foundry_key": "TSMC", "location": "Tainan, Taiwan",
                "wafer_size_mm": 300, "capacity_wspm": 100000,
                "status": "ACTIVE", "process_nodes": ["N5", "N4P", "N3E", "N3P"],
                "opened_year": 2020, "investment_b_usd": 19.5,
                "description": "TSMC 최대 규모 GigaFab, 5nm/3nm 주력 양산"
            }},
            {"key": "TSMC_FAB_21", "label": "FabSite", "name": "TSMC Fab 21 (Arizona)", "properties": {
                "foundry_key": "TSMC", "location": "Phoenix, Arizona, USA",
                "wafer_size_mm": 300, "capacity_wspm": 60000,
                "status": "UNDER_CONSTRUCTION", "process_nodes": ["N4P", "N3E", "N2"],
                "opened_year": 2025, "investment_b_usd": 40.0,
                "description": "CHIPS Act 지원, Phase 1 (4nm) 2025 양산 목표"
            }},
            {"key": "TSMC_FAB_20", "label": "FabSite", "name": "TSMC Fab 20", "properties": {
                "foundry_key": "TSMC", "location": "Hsinchu, Taiwan",
                "wafer_size_mm": 300, "capacity_wspm": 50000,
                "status": "ACTIVE", "process_nodes": ["N2", "A16"],
                "opened_year": 2025, "investment_b_usd": 25.0,
                "description": "TSMC N2 (2nm) 양산 전용 팹"
            }},
            {"key": "TSMC_KUMAMOTO", "label": "FabSite", "name": "JASM (TSMC Kumamoto)", "properties": {
                "foundry_key": "TSMC", "location": "Kumamoto, Japan",
                "wafer_size_mm": 300, "capacity_wspm": 55000,
                "status": "ACTIVE", "process_nodes": ["N28", "N16", "N7"],
                "opened_year": 2024, "investment_b_usd": 8.6,
                "description": "소니/도요타 합작, 일본 정부 보조금, 자동차/이미지센서용"
            }},
            {"key": "TSMC_DRESDEN", "label": "FabSite", "name": "ESMC (TSMC Dresden)", "properties": {
                "foundry_key": "TSMC", "location": "Dresden, Germany",
                "wafer_size_mm": 300, "capacity_wspm": 40000,
                "status": "UNDER_CONSTRUCTION", "process_nodes": ["N28", "N16"],
                "opened_year": 2027, "investment_b_usd": 10.0,
                "description": "EU Chips Act 지원, Bosch/Infineon/NXP 합작, 자동차용"
            }},
            {"key": "SAMSUNG_PYEONGTAEK", "label": "FabSite", "name": "Samsung Pyeongtaek Campus", "properties": {
                "foundry_key": "SAMSUNG_FOUNDRY", "location": "Pyeongtaek, South Korea",
                "wafer_size_mm": 300, "capacity_wspm": 200000,
                "status": "ACTIVE", "process_nodes": ["SF3", "SF2"],
                "opened_year": 2017, "investment_b_usd": 30.0,
                "description": "삼성 최대 규모 반도체 캠퍼스, 파운드리+메모리"
            }},
            {"key": "SAMSUNG_TAYLOR", "label": "FabSite", "name": "Samsung Taylor Fab", "properties": {
                "foundry_key": "SAMSUNG_FOUNDRY", "location": "Taylor, Texas, USA",
                "wafer_size_mm": 300, "capacity_wspm": 30000,
                "status": "UNDER_CONSTRUCTION", "process_nodes": ["SF3", "SF2"],
                "opened_year": 2026, "investment_b_usd": 17.0,
                "description": "미국 내 첨단 파운드리 팹, CHIPS Act 보조금"
            }},
            {"key": "INTEL_D1X", "label": "FabSite", "name": "Intel D1X (Oregon)", "properties": {
                "foundry_key": "INTEL_FOUNDRY", "location": "Hillsboro, Oregon, USA",
                "wafer_size_mm": 300, "capacity_wspm": 60000,
                "status": "ACTIVE", "process_nodes": ["Intel_20A", "Intel_18A"],
                "opened_year": 2013, "investment_b_usd": 3.0,
                "description": "인텔 최첨단 공정 개발 R&D 팹"
            }},
            {"key": "INTEL_FAB_52_62", "label": "FabSite", "name": "Intel Fab 52/62 (Arizona)", "properties": {
                "foundry_key": "INTEL_FOUNDRY", "location": "Chandler, Arizona, USA",
                "wafer_size_mm": 300, "capacity_wspm": 80000,
                "status": "UNDER_CONSTRUCTION", "process_nodes": ["Intel_18A"],
                "opened_year": 2025, "investment_b_usd": 20.0,
                "description": "Intel 18A 양산 팹, CHIPS Act 주요 수혜"
            }},
            {"key": "INTEL_OHIO", "label": "FabSite", "name": "Intel Ohio Mega Fab", "properties": {
                "foundry_key": "INTEL_FOUNDRY", "location": "New Albany, Ohio, USA",
                "wafer_size_mm": 300, "capacity_wspm": 100000,
                "status": "UNDER_CONSTRUCTION", "process_nodes": ["Intel_18A", "Intel_14A"],
                "opened_year": 2027, "investment_b_usd": 28.0,
                "description": "인텔 역대 최대 투자, 4개 팹 예정, 패키징 시설 포함"
            }},
        ]

        relationships = []
        # Foundry → FabSite
        for node in nodes:
            if node["label"] == "FabSite":
                foundry_key = node["properties"].get("foundry_key")
                if foundry_key:
                    relationships.append({
                        "from_key": foundry_key,
                        "to_key": node["key"],
                        "type": "OPERATES_FAB",
                        "properties": {}
                    })
                # FabSite → ProcessNode
                for pn in node["properties"].get("process_nodes", []):
                    relationships.append({
                        "from_key": node["key"],
                        "to_key": pn,
                        "type": "PRODUCES_ON",
                        "properties": {}
                    })

        return {"nodes": nodes, "relationships": relationships}

    def _builtin_process_generation_data(self) -> dict:
        nodes = [
            {"key": "GEN_PLANAR", "label": "ProcessGeneration", "name": "Planar MOSFET", "properties": {
                "transistor_type": "Planar", "era": "1960s-2011",
                "min_node_nm": 22, "description": "전통적 평면 MOSFET, 22nm까지 사용"
            }},
            {"key": "GEN_FINFET", "label": "ProcessGeneration", "name": "FinFET", "properties": {
                "transistor_type": "FinFET", "era": "2011-2025",
                "min_node_nm": 3, "introduced_by": "Intel (22nm, 2011)",
                "description": "3D 핀 구조로 누설 전류 감소, 3nm까지 사용"
            }},
            {"key": "GEN_GAA", "label": "ProcessGeneration", "name": "GAA (Nanosheet)", "properties": {
                "transistor_type": "GAA Nanosheet", "era": "2022-2028+",
                "min_node_nm": 1.4,
                "variants": ["Samsung MBCFET", "Intel RibbonFET", "TSMC Nanosheet"],
                "description": "게이트가 채널을 완전 둘러싸는 구조, 가변 시트 폭으로 성능 최적화"
            }},
            {"key": "GEN_CFET", "label": "ProcessGeneration", "name": "CFET (Complementary FET)", "properties": {
                "transistor_type": "CFET", "era": "2028+",
                "min_node_nm": 1, "status": "R&D",
                "description": "nFET 위에 pFET 수직 적층, 로직 밀도 극대화 (Angstrom era)"
            }},
            {"key": "GEN_BSPDN", "label": "ProcessGeneration", "name": "Backside Power Delivery (BSPDN)", "properties": {
                "type": "Power Delivery Innovation", "era": "2025+",
                "adopters": ["TSMC A16 (Super Power Rail)", "Intel 20A/18A (PowerVia)", "Samsung SF2"],
                "description": "전력 배선을 칩 뒷면으로 이동, 신호 배선 밀도 향상 + IR drop 감소"
            }},
        ]

        relationships = [
            # ProcessNode → ProcessGeneration
            {"from_key": "N7", "to_key": "GEN_FINFET", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "N5", "to_key": "GEN_FINFET", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "N4P", "to_key": "GEN_FINFET", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "N3E", "to_key": "GEN_FINFET", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "N3P", "to_key": "GEN_FINFET", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "N2", "to_key": "GEN_GAA", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "A16", "to_key": "GEN_GAA", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "SF3", "to_key": "GEN_GAA", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "SF2", "to_key": "GEN_GAA", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "Intel_20A", "to_key": "GEN_GAA", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "Intel_18A", "to_key": "GEN_GAA", "type": "GENERATION_OF", "properties": {}},
            # BSPDN adoption
            {"from_key": "A16", "to_key": "GEN_BSPDN", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "Intel_20A", "to_key": "GEN_BSPDN", "type": "GENERATION_OF", "properties": {}},
            {"from_key": "Intel_18A", "to_key": "GEN_BSPDN", "type": "GENERATION_OF", "properties": {}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    def _builtin_memory_standard_data(self) -> dict:
        nodes = [
            {"key": "DDR5", "label": "MemoryStandard", "name": "DDR5 SDRAM", "properties": {
                "jedec_id": "JESD79-5C", "type": "DDR", "generation": 5,
                "max_speed_mtps": 8800, "bandwidth_gbps": 70.4, "voltage_v": 1.1,
                "channel_width_bits": 32, "burst_length": 16,
                "description": "서버/데스크탑 표준 메모리, 듀얼 채널 구조"
            }},
            {"key": "LPDDR5X", "label": "MemoryStandard", "name": "LPDDR5X", "properties": {
                "jedec_id": "JESD209-5B", "type": "LPDDR", "generation": 5,
                "max_speed_mtps": 8533, "bandwidth_gbps": 68.3, "voltage_v": 1.05,
                "description": "모바일/노트북용 저전력 메모리"
            }},
            {"key": "GDDR7", "label": "MemoryStandard", "name": "GDDR7", "properties": {
                "jedec_id": "JESD239", "type": "GDDR", "generation": 7,
                "max_speed_gtps": 36, "bandwidth_per_chip_gbps": 144, "voltage_v": 1.1,
                "bus_width_bits": 32, "pam4_signaling": True,
                "description": "GPU용 고대역 메모리, PAM4 시그널링 도입"
            }},
            {"key": "GDDR6X", "label": "MemoryStandard", "name": "GDDR6X", "properties": {
                "jedec_id": "JESD250C", "type": "GDDR", "generation": 6,
                "max_speed_gbps": 24, "voltage_v": 1.35,
                "description": "NVIDIA RTX 40 시리즈 탑재, PAM4"
            }},
            {"key": "CXL_MEM", "label": "MemoryStandard", "name": "CXL Memory Expansion", "properties": {
                "type": "CXL", "version": "3.0",
                "bandwidth_gtps": 64, "latency_ns_additional": 50,
                "description": "PCIe 기반 메모리 확장 프로토콜, Type 3 디바이스"
            }},
        ]

        relationships = [
            # HBMGeneration → MemoryStandard 매핑은 별도 (HBM은 이미 별도 노드)
            {"from_key": "HBM3", "to_key": "DDR5", "type": "IMPLEMENTS", "properties": {"note": "HBM3 uses DDR5 I/O logic"}},
            {"from_key": "HBM3E", "to_key": "DDR5", "type": "IMPLEMENTS", "properties": {"note": "HBM3E uses DDR5 I/O logic"}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    def _builtin_interconnect_standard_data(self) -> dict:
        nodes = [
            {"key": "PCIE_5_0", "label": "InterconnectStandard", "name": "PCIe 5.0", "properties": {
                "version": "5.0", "protocol_type": "PCIe",
                "bandwidth_gtps": 32, "bandwidth_per_lane_gbps": 3.94,
                "max_lanes": 16, "total_bandwidth_gbps": 63,
                "encoding": "128b/130b", "year": 2019,
                "description": "현재 데이터센터 표준 인터커넥트"
            }},
            {"key": "PCIE_6_0", "label": "InterconnectStandard", "name": "PCIe 6.0", "properties": {
                "version": "6.0", "protocol_type": "PCIe",
                "bandwidth_gtps": 64, "bandwidth_per_lane_gbps": 7.56,
                "max_lanes": 16, "total_bandwidth_gbps": 121,
                "encoding": "PAM4 + FLIT", "year": 2022,
                "description": "PAM4 시그널링 도입, 대역폭 2배"
            }},
            {"key": "CXL_3_0", "label": "InterconnectStandard", "name": "CXL 3.0", "properties": {
                "version": "3.0", "protocol_type": "CXL",
                "bandwidth_gtps": 64, "base_spec": "PCIe 6.0",
                "features": ["Memory Pooling", "Switching", "Multi-headed Device", "Global Fabric"],
                "year": 2023,
                "description": "패브릭 기반 메모리 공유, 멀티호스트 지원"
            }},
            {"key": "UCIE_1_1", "label": "InterconnectStandard", "name": "UCIe 1.1", "properties": {
                "version": "1.1", "protocol_type": "UCIe",
                "bandwidth_per_lane_gbps": 32, "bump_pitch_um": 25,
                "standard_package_bandwidth_gbps": 1317,
                "year": 2023,
                "description": "유니버설 칩렛 인터커넥트, 패키지 내 die-to-die 표준"
            }},
            {"key": "NVLINK_5_0", "label": "InterconnectStandard", "name": "NVLink 5.0", "properties": {
                "version": "5.0", "protocol_type": "NVLink",
                "bandwidth_per_link_gbps": 100, "total_bandwidth_gbps": 1800,
                "links": 18, "vendor": "NVIDIA", "year": 2024,
                "description": "Blackwell (B200) 세대, GPU-GPU 직접 연결"
            }},
            {"key": "INFINITY_FABRIC", "label": "InterconnectStandard", "name": "AMD Infinity Fabric", "properties": {
                "version": "4.0", "protocol_type": "Infinity Fabric",
                "bandwidth_gbps": 896, "vendor": "AMD", "year": 2023,
                "description": "AMD chiplet 간 인터커넥트, MI300X 탑재"
            }},
            {"key": "UALINK_1_0", "label": "InterconnectStandard", "name": "UALink 1.0", "properties": {
                "version": "1.0", "protocol_type": "UALink",
                "bandwidth_per_link_gbps": 200, "year": 2024,
                "consortium": ["AMD", "Google", "Intel", "Meta", "Microsoft", "Broadcom"],
                "description": "NVLink 대항 오픈 표준, AI 가속기 간 스케일업 인터커넥트"
            }},
        ]

        relationships = [
            # AIAccelerator → InterconnectStandard
            {"from_key": "H100_SXM", "to_key": "PCIE_5_0", "type": "USES_INTERCONNECT", "properties": {}},
            {"from_key": "H200_SXM", "to_key": "PCIE_5_0", "type": "USES_INTERCONNECT", "properties": {}},
            {"from_key": "B200", "to_key": "PCIE_5_0", "type": "USES_INTERCONNECT", "properties": {}},
            {"from_key": "B200", "to_key": "NVLINK_5_0", "type": "USES_INTERCONNECT", "properties": {}},
            {"from_key": "MI300X", "to_key": "PCIE_5_0", "type": "USES_INTERCONNECT", "properties": {}},
            {"from_key": "MI300X", "to_key": "INFINITY_FABRIC", "type": "USES_INTERCONNECT", "properties": {}},
            {"from_key": "MI325X", "to_key": "PCIE_5_0", "type": "USES_INTERCONNECT", "properties": {}},
            {"from_key": "MI325X", "to_key": "INFINITY_FABRIC", "type": "USES_INTERCONNECT", "properties": {}},
            # CXL is based on PCIe
            {"from_key": "CXL_3_0", "to_key": "PCIE_6_0", "type": "USES_INTERCONNECT", "properties": {"note": "CXL 3.0 is based on PCIe 6.0 PHY"}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    def _builtin_packaging_detail_data(self) -> dict:
        nodes = [
            {"key": "SUBSTRATE_ABF", "label": "SubstrateType", "name": "ABF Substrate", "properties": {
                "type": "organic", "material": "Ajinomoto Build-up Film",
                "vendor": "Ajinomoto", "line_space_um": 8,
                "layer_count": "12-20", "application": "HPC/AI 패키징",
                "description": "고급 유기 기판, 미세 배선으로 HPC 패키징에 필수"
            }},
            {"key": "SUBSTRATE_SI_INTERPOSER", "label": "SubstrateType", "name": "Silicon Interposer", "properties": {
                "type": "silicon", "line_space_um": 0.5,
                "tsv_pitch_um": 10, "application": "CoWoS, 2.5D",
                "description": "실리콘 인터포저, TSV로 다이 간 초고밀도 연결"
            }},
            {"key": "SUBSTRATE_GLASS", "label": "SubstrateType", "name": "Glass Core Substrate", "properties": {
                "type": "glass", "line_space_um": 2,
                "vendors": ["Absolics (SKC)", "Intel"],
                "advantage": "낮은 열팽창, 대면적, TGV (Through Glass Via)",
                "status": "Early Production (2025+)",
                "description": "차세대 패키징 기판, ABF/Si 인터포저 대체 후보"
            }},
            {"key": "SUBSTRATE_FCBGA", "label": "SubstrateType", "name": "FC-BGA Substrate", "properties": {
                "type": "organic", "line_space_um": 15,
                "application": "범용 플립칩 BGA",
                "description": "가장 일반적인 유기 기판, 서버/PC/모바일 범용"
            }},
            {"key": "HYBRID_BONDING", "label": "SubstrateType", "name": "Hybrid Bonding (Cu-Cu)", "properties": {
                "type": "interconnect_technology",
                "bond_pitch_um": 1.0, "min_pitch_um": 0.5,
                "bandwidth_density_tbps_per_mm2": 12.8,
                "vendors": ["TSMC (SoIC)", "Intel (Foveros Direct)", "Samsung"],
                "description": "구리-구리 직접 접합, 3D 적층의 핵심 기술, µ-bump 대체"
            }},
        ]

        relationships = [
            # PackagingTech → SubstrateType
            {"from_key": "CoWoS-S", "to_key": "SUBSTRATE_SI_INTERPOSER", "type": "USES_SUBSTRATE", "properties": {}},
            {"from_key": "CoWoS-L", "to_key": "SUBSTRATE_SI_INTERPOSER", "type": "USES_SUBSTRATE", "properties": {}},
            {"from_key": "CoWoS-S", "to_key": "SUBSTRATE_ABF", "type": "USES_SUBSTRATE", "properties": {"note": "base substrate"}},
            {"from_key": "EMIB", "to_key": "SUBSTRATE_ABF", "type": "USES_SUBSTRATE", "properties": {}},
            {"from_key": "InFO", "to_key": "SUBSTRATE_FCBGA", "type": "USES_SUBSTRATE", "properties": {}},
            {"from_key": "Foveros", "to_key": "HYBRID_BONDING", "type": "CONNECTS_VIA", "properties": {}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    # ─────────────────────────────────────────────────────
    # Tier 2 Built-in Data
    # ─────────────────────────────────────────────────────

    def _builtin_equipment_ecosystem_data(self) -> dict:
        nodes = [
            {"key": "VENDOR_ASML", "label": "EquipmentVendor", "name": "ASML", "properties": {
                "country": "Netherlands", "hq": "Veldhoven",
                "revenue_b_usd": 27.6, "market_segment": "Lithography",
                "founded_year": 1984, "employees": 42000,
                "market_share_litho_pct": 90,
                "description": "세계 유일 EUV 장비 제조사, 반도체 장비 시가총액 1위"
            }},
            {"key": "VENDOR_AMAT", "label": "EquipmentVendor", "name": "Applied Materials", "properties": {
                "country": "United States", "hq": "Santa Clara, CA",
                "revenue_b_usd": 26.5, "market_segment": "Deposition, Etch, CMP",
                "founded_year": 1967, "employees": 35000,
                "description": "세계 최대 반도체 장비 회사 (매출 기준)"
            }},
            {"key": "VENDOR_LAM", "label": "EquipmentVendor", "name": "Lam Research", "properties": {
                "country": "United States", "hq": "Fremont, CA",
                "revenue_b_usd": 17.4, "market_segment": "Etch, Deposition, Clean",
                "founded_year": 1980,
                "description": "에칭/증착 장비 선도, 3D NAND/GAA 공정 필수"
            }},
            {"key": "VENDOR_TEL", "label": "EquipmentVendor", "name": "Tokyo Electron (TEL)", "properties": {
                "country": "Japan", "hq": "Tokyo",
                "revenue_b_usd": 16.2, "market_segment": "Coater/Developer, Etch, Deposition",
                "founded_year": 1963,
                "description": "코터/디벨로퍼 1위, EUV 트랙 필수 장비"
            }},
            {"key": "VENDOR_KLA", "label": "EquipmentVendor", "name": "KLA Corporation", "properties": {
                "country": "United States", "hq": "Milpitas, CA",
                "revenue_b_usd": 10.5, "market_segment": "Inspection, Metrology",
                "founded_year": 1975,
                "description": "웨이퍼 검사/계측 장비 1위, 수율 관리의 핵심"
            }},
            # Equipment Models
            {"key": "ASML_NXE_3800E", "label": "EquipmentModel", "name": "ASML NXE:3800E", "properties": {
                "vendor_key": "VENDOR_ASML", "category": "LITHOGRAPHY",
                "generation": "EUV 0.33NA", "min_node_nm": 3,
                "throughput_wph": 220, "wavelength_nm": 13.5,
                "numerical_aperture": 0.33, "resolution_nm": 13,
                "price_m_usd": 200,
                "description": "현재 가장 많이 사용되는 EUV 스캐너"
            }},
            {"key": "ASML_NXE_3600D", "label": "EquipmentModel", "name": "ASML NXE:3600D", "properties": {
                "vendor_key": "VENDOR_ASML", "category": "LITHOGRAPHY",
                "generation": "EUV 0.33NA", "min_node_nm": 5,
                "throughput_wph": 185, "wavelength_nm": 13.5,
                "numerical_aperture": 0.33,
                "price_m_usd": 180,
                "description": "이전 세대 EUV 스캐너"
            }},
            {"key": "ASML_EXE_5000", "label": "EquipmentModel", "name": "ASML EXE:5000 (High-NA)", "properties": {
                "vendor_key": "VENDOR_ASML", "category": "LITHOGRAPHY",
                "generation": "High-NA EUV 0.55NA", "min_node_nm": 1.4,
                "throughput_wph": 185, "wavelength_nm": 13.5,
                "numerical_aperture": 0.55, "resolution_nm": 8,
                "price_m_usd": 380,
                "description": "High-NA EUV, 2nm 이하 필수, 인텔 최초 도입 (2025)"
            }},
            {"key": "LAM_VANTEX", "label": "EquipmentModel", "name": "Lam Vantex", "properties": {
                "vendor_key": "VENDOR_LAM", "category": "ETCH",
                "generation": "Dielectric Etch", "min_node_nm": 3,
                "throughput_wph": 120,
                "description": "GAA/3D 구조용 고선택비 유전체 에칭"
            }},
            {"key": "AMAT_CENTURA_SCULPTA", "label": "EquipmentModel", "name": "Applied Centura Sculpta", "properties": {
                "vendor_key": "VENDOR_AMAT", "category": "ETCH",
                "generation": "Pattern Shaping", "min_node_nm": 3,
                "description": "EUV 패턴 보정용, 마스크 공정 수 감소"
            }},
        ]

        relationships = [
            # Vendor → Model
            {"from_key": "VENDOR_ASML", "to_key": "ASML_NXE_3800E", "type": "MANUFACTURES_EQUIP", "properties": {}},
            {"from_key": "VENDOR_ASML", "to_key": "ASML_NXE_3600D", "type": "MANUFACTURES_EQUIP", "properties": {}},
            {"from_key": "VENDOR_ASML", "to_key": "ASML_EXE_5000", "type": "MANUFACTURES_EQUIP", "properties": {}},
            {"from_key": "VENDOR_LAM", "to_key": "LAM_VANTEX", "type": "MANUFACTURES_EQUIP", "properties": {}},
            {"from_key": "VENDOR_AMAT", "to_key": "AMAT_CENTURA_SCULPTA", "type": "MANUFACTURES_EQUIP", "properties": {}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    def _builtin_material_supplier_data(self) -> dict:
        nodes = [
            {"key": "SUP_JSR", "label": "MaterialSupplier", "name": "JSR Corporation", "properties": {
                "country": "Japan", "specialization": "EUV/ArF Photoresist",
                "market_share_pct": 28, "revenue_b_usd": 3.2,
                "description": "EUV 포토레지스트 시장 선두, 인히비터 기술"
            }},
            {"key": "SUP_TOK", "label": "MaterialSupplier", "name": "Tokyo Ohka Kogyo (TOK)", "properties": {
                "country": "Japan", "specialization": "Photoresist, Developer",
                "market_share_pct": 22,
                "description": "ArF/KrF 포토레지스트 강자"
            }},
            {"key": "SUP_SHINETSUCHEM", "label": "MaterialSupplier", "name": "Shin-Etsu Chemical", "properties": {
                "country": "Japan", "specialization": "Silicon Wafer, Photomask Blank, Photoresist",
                "market_share_wafer_pct": 32, "revenue_b_usd": 15.8,
                "description": "실리콘 웨이퍼 세계 1위, 포토마스크 블랭크 공급"
            }},
            {"key": "SUP_SUMCO", "label": "MaterialSupplier", "name": "SUMCO", "properties": {
                "country": "Japan", "specialization": "Silicon Wafer",
                "market_share_wafer_pct": 24,
                "description": "실리콘 웨이퍼 세계 2위"
            }},
            {"key": "SUP_ENTEGRIS", "label": "MaterialSupplier", "name": "Entegris", "properties": {
                "country": "United States", "specialization": "Filtration, CMP Slurry, Chemical Delivery",
                "revenue_b_usd": 3.6,
                "description": "반도체 공정 소재/필터/CMP 통합 솔루션"
            }},
            {"key": "SUP_AIRLIQUIDE", "label": "MaterialSupplier", "name": "Air Liquide", "properties": {
                "country": "France", "specialization": "Electronic Specialty Gas",
                "revenue_b_usd": 30.0,
                "description": "반도체 공정용 특수 가스 (NF3, WF6, SiH4 등)"
            }},
            {"key": "SUP_SKHYNIX_HBM", "label": "MaterialSupplier", "name": "SK Hynix", "properties": {
                "country": "South Korea", "specialization": "HBM, DRAM, NAND",
                "revenue_b_usd": 35.3, "market_share_hbm_pct": 53,
                "description": "HBM 시장 점유율 1위, NVIDIA 독점 공급 (HBM3E)"
            }},
            {"key": "SUP_SAMSUNG_MEM", "label": "MaterialSupplier", "name": "Samsung Memory", "properties": {
                "country": "South Korea", "specialization": "HBM, DRAM, NAND",
                "revenue_b_usd": 50.2, "market_share_hbm_pct": 35,
                "description": "종합 메모리 세계 1위, HBM 2위"
            }},
            {"key": "SUP_MICRON", "label": "MaterialSupplier", "name": "Micron Technology", "properties": {
                "country": "United States", "specialization": "HBM, DRAM, NAND",
                "revenue_b_usd": 25.1, "market_share_hbm_pct": 12,
                "description": "미국 유일 메모리 대기업, HBM4 경쟁 참여"
            }},
        ]

        relationships = [
            # MaterialSupplier → Material (기존 Material 노드와 연결)
            {"from_key": "SUP_JSR", "to_key": "EUV_RESIST", "type": "SUPPLIES", "properties": {}},
            {"from_key": "SUP_TOK", "to_key": "ARF_RESIST", "type": "SUPPLIES", "properties": {}},
            {"from_key": "SUP_AIRLIQUIDE", "to_key": "NF3", "type": "SUPPLIES", "properties": {}},
            {"from_key": "SUP_AIRLIQUIDE", "to_key": "WF6", "type": "SUPPLIES", "properties": {}},
            # HBM suppliers → HBMGeneration
            {"from_key": "SUP_SKHYNIX_HBM", "to_key": "HBM3", "type": "SUPPLIES", "properties": {"product": "HBM3 16GB"}},
            {"from_key": "SUP_SKHYNIX_HBM", "to_key": "HBM3E", "type": "SUPPLIES", "properties": {"product": "HBM3E 36GB"}},
            {"from_key": "SUP_SAMSUNG_MEM", "to_key": "HBM3", "type": "SUPPLIES", "properties": {}},
            {"from_key": "SUP_SAMSUNG_MEM", "to_key": "HBM3E", "type": "SUPPLIES", "properties": {}},
            {"from_key": "SUP_MICRON", "to_key": "HBM3E", "type": "SUPPLIES", "properties": {}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    def _builtin_design_ip_data(self) -> dict:
        nodes = [
            {"key": "IP_CORTEX_X4", "label": "DesignIP", "name": "ARM Cortex-X4", "properties": {
                "vendor": "ARM", "type": "CPU_CORE", "architecture": "ARMv9.2-A",
                "microarchitecture": "Out-of-Order", "issue_width": 10,
                "description": "최고 성능 ARM CPU 코어, Snapdragon 8 Gen3 / Dimensity 9300 탑재"
            }},
            {"key": "IP_CORTEX_X5", "label": "DesignIP", "name": "ARM Cortex-X5", "properties": {
                "vendor": "ARM", "type": "CPU_CORE", "architecture": "ARMv9.2-A",
                "description": "2025년 출시, X4 대비 IPC 15% 향상 예상"
            }},
            {"key": "IP_NEOVERSE_V3", "label": "DesignIP", "name": "ARM Neoverse V3", "properties": {
                "vendor": "ARM", "type": "CPU_CORE", "architecture": "ARMv9.2-A",
                "target": "Server/Cloud",
                "description": "서버용 ARM 코어, AWS Graviton4 / NVIDIA Grace 탑재"
            }},
            {"key": "IP_RISCV_P550", "label": "DesignIP", "name": "SiFive P550", "properties": {
                "vendor": "SiFive", "type": "CPU_CORE", "architecture": "RISC-V (RV64GBC)",
                "description": "고성능 RISC-V 코어, Linux 지원"
            }},
            {"key": "IP_SYNOPSYS_PCIE6", "label": "DesignIP", "name": "Synopsys PCIe 6.0 PHY", "properties": {
                "vendor": "Synopsys", "type": "PHY", "protocol": "PCIe 6.0",
                "data_rate_gtps": 64,
                "description": "업계 최초 PCIe 6.0 PHY IP"
            }},
            {"key": "IP_CADENCE_224G", "label": "DesignIP", "name": "Cadence 224G SerDes", "properties": {
                "vendor": "Cadence", "type": "SERDES", "data_rate_gbps": 224,
                "description": "차세대 224Gbps SerDes PHY, 800GbE/1.6TbE 지원"
            }},
        ]

        relationships = [
            {"from_key": "H100_SXM", "to_key": "IP_SYNOPSYS_PCIE6", "type": "USES_IP", "properties": {"note": "PCIe 5.0 version"}},
            {"from_key": "B200", "to_key": "IP_SYNOPSYS_PCIE6", "type": "USES_IP", "properties": {}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    def _builtin_company_landscape_data(self) -> dict:
        nodes = [
            {"key": "COMPANY_NVIDIA", "label": "Company", "name": "NVIDIA", "properties": {
                "type": "FABLESS", "country": "United States", "hq": "Santa Clara, CA",
                "revenue_b_usd": 130.5, "market_cap_b_usd": 3200,
                "focus": ["AI Accelerator", "GPU", "Data Center", "Automotive"],
                "founded_year": 1993,
                "description": "AI 가속기 시장 지배적 위치, 데이터센터 GPU 시장점유율 80%+"
            }},
            {"key": "COMPANY_AMD", "label": "Company", "name": "AMD", "properties": {
                "type": "FABLESS", "country": "United States", "hq": "Santa Clara, CA",
                "revenue_b_usd": 22.7,
                "focus": ["CPU", "GPU", "AI Accelerator", "FPGA"],
                "founded_year": 1969,
                "description": "CPU/GPU 듀얼 라인업, MI300X로 AI 가속기 시장 진입"
            }},
            {"key": "COMPANY_INTEL", "label": "Company", "name": "Intel", "properties": {
                "type": "IDM", "country": "United States", "hq": "Santa Clara, CA",
                "revenue_b_usd": 54.2,
                "focus": ["CPU", "Foundry", "AI Accelerator", "FPGA"],
                "founded_year": 1968,
                "description": "IDM + 파운드리 전환 중, Gaudi AI 가속기"
            }},
            {"key": "COMPANY_QUALCOMM", "label": "Company", "name": "Qualcomm", "properties": {
                "type": "FABLESS", "country": "United States", "hq": "San Diego, CA",
                "revenue_b_usd": 38.9,
                "focus": ["Mobile SoC", "5G Modem", "Automotive", "IoT"],
                "founded_year": 1985,
                "description": "모바일 AP/모뎀 시장 지배, 자동차/IoT 확장"
            }},
            {"key": "COMPANY_BROADCOM", "label": "Company", "name": "Broadcom", "properties": {
                "type": "FABLESS", "country": "United States", "hq": "Palo Alto, CA",
                "revenue_b_usd": 51.6,
                "focus": ["Networking ASIC", "Custom AI ASIC", "Broadband", "Storage"],
                "founded_year": 1961,
                "description": "네트워크 칩 1위, 구글 TPU 등 커스텀 AI ASIC 설계"
            }},
            {"key": "COMPANY_GOOGLE", "label": "Company", "name": "Google (Alphabet)", "properties": {
                "type": "FABLESS", "country": "United States", "hq": "Mountain View, CA",
                "revenue_b_usd": 350.0,
                "focus": ["Custom AI ASIC (TPU)", "Cloud"],
                "description": "자체 TPU 설계, AI 학습/추론 인프라"
            }},
            {"key": "COMPANY_APPLE", "label": "Company", "name": "Apple", "properties": {
                "type": "FABLESS", "country": "United States", "hq": "Cupertino, CA",
                "revenue_b_usd": 383.0,
                "focus": ["Mobile SoC", "PC SoC", "Custom Silicon"],
                "description": "A/M 시리즈 자체 설계, TSMC 최대 고객"
            }},
            # OSAT
            {"key": "COMPANY_ASE", "label": "Company", "name": "ASE Technology", "properties": {
                "type": "OSAT", "country": "Taiwan", "hq": "Kaohsiung",
                "revenue_b_usd": 18.9,
                "description": "세계 최대 OSAT (반도체 패키징/테스트)"
            }},
            {"key": "COMPANY_AMKOR", "label": "Company", "name": "Amkor Technology", "properties": {
                "type": "OSAT", "country": "United States", "hq": "Tempe, AZ",
                "revenue_b_usd": 7.0,
                "description": "OSAT 2위, 어드밴스드 패키징 확대"
            }},
        ]

        relationships = [
            # Company → AIAccelerator (DESIGNS)
            {"from_key": "COMPANY_NVIDIA", "to_key": "H100_SXM", "type": "DESIGNS", "properties": {}},
            {"from_key": "COMPANY_NVIDIA", "to_key": "H200_SXM", "type": "DESIGNS", "properties": {}},
            {"from_key": "COMPANY_NVIDIA", "to_key": "B200", "type": "DESIGNS", "properties": {}},
            {"from_key": "COMPANY_AMD", "to_key": "MI300X", "type": "DESIGNS", "properties": {}},
            {"from_key": "COMPANY_AMD", "to_key": "MI325X", "type": "DESIGNS", "properties": {}},
            {"from_key": "COMPANY_INTEL", "to_key": "Gaudi3", "type": "DESIGNS", "properties": {}},
            {"from_key": "COMPANY_GOOGLE", "to_key": "TPUv5e", "type": "DESIGNS", "properties": {}},
            # Company → Foundry (OPERATES)
            {"from_key": "COMPANY_INTEL", "to_key": "INTEL_FOUNDRY", "type": "OPERATES", "properties": {}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    def _builtin_benchmark_data(self) -> dict:
        nodes = [
            {"key": "BENCH_MLPERF_TRAIN", "label": "Benchmark", "name": "MLPerf Training", "properties": {
                "category": "MLPERF", "metric_unit": "time_to_train_minutes",
                "higher_is_better": False, "org": "MLCommons",
                "description": "AI 학습 성능 업계 표준 벤치마크"
            }},
            {"key": "BENCH_MLPERF_INFER", "label": "Benchmark", "name": "MLPerf Inference", "properties": {
                "category": "MLPERF", "metric_unit": "queries_per_second",
                "higher_is_better": True, "org": "MLCommons",
                "description": "AI 추론 성능 벤치마크 (Server/Offline 시나리오)"
            }},
            {"key": "BENCH_TOPS_PER_W", "label": "Benchmark", "name": "TOPS/Watt", "properties": {
                "category": "EFFICIENCY", "metric_unit": "TOPS_per_watt",
                "higher_is_better": True,
                "description": "전력 효율 지표 (INT8 TOPS / TDP)"
            }},
            {"key": "BENCH_MEM_BW", "label": "Benchmark", "name": "Memory Bandwidth", "properties": {
                "category": "BANDWIDTH", "metric_unit": "TB_per_s",
                "higher_is_better": True,
                "description": "메모리 대역폭 벤치마크"
            }},
        ]

        relationships = [
            {"from_key": "H100_SXM", "to_key": "BENCH_TOPS_PER_W", "type": "SCORES_ON", "properties": {"score": 5.65, "precision": "INT8"}},
            {"from_key": "B200", "to_key": "BENCH_TOPS_PER_W", "type": "SCORES_ON", "properties": {"score": 9.0, "precision": "INT8"}},
            {"from_key": "MI300X", "to_key": "BENCH_TOPS_PER_W", "type": "SCORES_ON", "properties": {"score": 3.49, "precision": "INT8"}},
            {"from_key": "H100_SXM", "to_key": "BENCH_MEM_BW", "type": "SCORES_ON", "properties": {"score": 3.35}},
            {"from_key": "B200", "to_key": "BENCH_MEM_BW", "type": "SCORES_ON", "properties": {"score": 8.0}},
            {"from_key": "MI300X", "to_key": "BENCH_MEM_BW", "type": "SCORES_ON", "properties": {"score": 5.3}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    # ─────────────────────────────────────────────────────
    # Tier 3 Built-in Data
    # ─────────────────────────────────────────────────────

    def _builtin_reliability_data(self) -> dict:
        nodes = [
            {"key": "TEST_HTOL", "label": "ReliabilityTest", "name": "HTOL (High Temperature Operating Life)", "properties": {
                "standard": "JEDEC JESD22-A108", "type": "HTOL",
                "duration_hours": 1000, "temperature_c": 125, "voltage": "Vmax",
                "description": "고온 동작 수명 시험, 반도체 신뢰성 기본 시험"
            }},
            {"key": "TEST_TC", "label": "ReliabilityTest", "name": "Temperature Cycling", "properties": {
                "standard": "JEDEC JESD22-A104", "type": "TC",
                "cycles": 1000, "temp_range": "-65°C to +150°C",
                "description": "온도 변화에 의한 기계적 스트레스 시험"
            }},
            {"key": "TEST_ESD_HBM", "label": "ReliabilityTest", "name": "ESD-HBM (Human Body Model)", "properties": {
                "standard": "JEDEC JS-001", "type": "ESD",
                "pass_voltage_v": 2000,
                "description": "정전기 방전 내성 시험 (인체 모델)"
            }},
            {"key": "TEST_ESD_CDM", "label": "ReliabilityTest", "name": "ESD-CDM (Charged Device Model)", "properties": {
                "standard": "JEDEC JS-002", "type": "ESD",
                "pass_voltage_v": 500,
                "description": "충전된 소자 모델 ESD 시험"
            }},
            {"key": "TEST_EM", "label": "ReliabilityTest", "name": "Electromigration (EM)", "properties": {
                "standard": "JEDEC JEP154", "type": "EM",
                "temperature_c": 300, "stress_current_density": "1-10 MA/cm²",
                "description": "배선의 전류 밀도에 의한 원자 이동 시험"
            }},
            {"key": "TEST_TDDB", "label": "ReliabilityTest", "name": "TDDB (Time Dependent Dielectric Breakdown)", "properties": {
                "standard": "JEDEC JEP122", "type": "TDDB",
                "description": "게이트 산화막 시간 의존 절연 파괴 시험"
            }},
            {"key": "TEST_AECQ100", "label": "ReliabilityTest", "name": "AEC-Q100 (Automotive Qualification)", "properties": {
                "standard": "AEC-Q100", "type": "AUTOMOTIVE",
                "grades": ["Grade 0: -40~150°C", "Grade 1: -40~125°C", "Grade 2: -40~105°C", "Grade 3: -40~85°C"],
                "description": "차량용 반도체 신뢰성 인증 표준"
            }},
        ]
        return {"nodes": nodes, "relationships": []}

    def _builtin_standards_data(self) -> dict:
        nodes = [
            {"key": "STD_SEMI_E10", "label": "Standard", "name": "SEMI E10 (OEE)", "properties": {
                "org": "SEMI", "version": "0718", "year": 2018,
                "scope": "Equipment reliability/utilization metrics (OEE)",
                "description": "장비 종합 효율(OEE) 측정 표준"
            }},
            {"key": "STD_SEMI_E79", "label": "Standard", "name": "SEMI E79 (Overall Fab Efficiency)", "properties": {
                "org": "SEMI", "scope": "Fab-level metrics",
                "description": "팹 전체 효율 측정 표준"
            }},
            {"key": "STD_JEDEC_HBM", "label": "Standard", "name": "JEDEC JESD238 (HBM3)", "properties": {
                "org": "JEDEC", "version": "JESD238", "year": 2022,
                "scope": "HBM3 interface specification",
                "description": "HBM3 인터페이스 규격"
            }},
        ]
        return {"nodes": nodes, "relationships": []}

    def _builtin_application_data(self) -> dict:
        nodes = [
            {"key": "APP_DATACENTER_TRAINING", "label": "Application", "name": "AI Training (Data Center)", "properties": {
                "segment": "DATACENTER", "workload": "LLM/Foundation Model Training",
                "requirements": {"compute": "FP8/BF16 PFLOPS", "memory": "HBM 192GB+", "interconnect": "NVLink/InfiniBand", "power": "700W+"},
                "description": "LLM 학습용 데이터센터, 수천 GPU 클러스터"
            }},
            {"key": "APP_DATACENTER_INFERENCE", "label": "Application", "name": "AI Inference (Data Center)", "properties": {
                "segment": "DATACENTER", "workload": "LLM Serving, Image Gen",
                "requirements": {"compute": "INT8/INT4 TOPS", "memory": "Large capacity for KV cache", "latency": "<50ms TTFT"},
                "description": "AI 추론 서빙, 비용/성능 최적화 중요"
            }},
            {"key": "APP_EDGE_AI", "label": "Application", "name": "Edge AI Inference", "properties": {
                "segment": "EDGE", "workload": "On-device LLM, Vision",
                "requirements": {"compute": "10-100 TOPS", "power": "<15W", "memory": "8-16GB LPDDR"},
                "description": "엣지 디바이스에서의 AI 추론 (스마트폰, IoT)"
            }},
            {"key": "APP_AUTOMOTIVE", "label": "Application", "name": "Automotive ADAS/AD", "properties": {
                "segment": "AUTOMOTIVE", "workload": "Perception, Planning, Control",
                "requirements": {"compute": "100-1000 TOPS", "reliability": "AEC-Q100 Grade 1", "power": "50-200W"},
                "description": "자율주행/ADAS용 SoC, 안전등급(ASIL-D) 필수"
            }},
            {"key": "APP_MOBILE", "label": "Application", "name": "Mobile AI (Smartphone)", "properties": {
                "segment": "MOBILE", "workload": "On-device LLM, Camera AI, Voice",
                "requirements": {"compute": "10-45 TOPS NPU", "power": "<5W", "process": "3-4nm"},
                "description": "스마트폰 온디바이스 AI, Qualcomm/MediaTek/Apple SoC"
            }},
        ]

        relationships = [
            {"from_key": "H100_SXM", "to_key": "APP_DATACENTER_TRAINING", "type": "OPTIMIZED_FOR", "properties": {}},
            {"from_key": "B200", "to_key": "APP_DATACENTER_TRAINING", "type": "OPTIMIZED_FOR", "properties": {}},
            {"from_key": "H200_SXM", "to_key": "APP_DATACENTER_INFERENCE", "type": "OPTIMIZED_FOR", "properties": {}},
            {"from_key": "MI300X", "to_key": "APP_DATACENTER_INFERENCE", "type": "OPTIMIZED_FOR", "properties": {}},
            {"from_key": "TPUv5e", "to_key": "APP_DATACENTER_INFERENCE", "type": "OPTIMIZED_FOR", "properties": {}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    def _builtin_thermal_data(self) -> dict:
        nodes = [
            {"key": "THERMAL_AIR", "label": "ThermalSolution", "name": "Air Cooling (Heatsink + Fan)", "properties": {
                "type": "AIR", "max_tdp_w": 350,
                "thermal_resistance_c_per_w": 0.15,
                "description": "전통적 공냉, TDP 350W 이하 적합"
            }},
            {"key": "THERMAL_DLC", "label": "ThermalSolution", "name": "Direct Liquid Cooling (Cold Plate)", "properties": {
                "type": "LIQUID", "max_tdp_w": 1200,
                "thermal_resistance_c_per_w": 0.05,
                "coolant": "Water/Glycol",
                "description": "콜드플레이트 직접 수냉, H100/B200 데이터센터 표준"
            }},
            {"key": "THERMAL_IMMERSION", "label": "ThermalSolution", "name": "Single-Phase Immersion Cooling", "properties": {
                "type": "IMMERSION", "max_tdp_w": 2000,
                "thermal_resistance_c_per_w": 0.02,
                "coolant": "Dielectric Fluid (3M Novec/Fluorinert)",
                "description": "서버를 냉각유에 침지, 1000W+ AI 가속기용"
            }},
            {"key": "THERMAL_2PHASE", "label": "ThermalSolution", "name": "Two-Phase Immersion Cooling", "properties": {
                "type": "IMMERSION", "max_tdp_w": 3000,
                "thermal_resistance_c_per_w": 0.01,
                "description": "비등/응축 사이클 이용, 가장 높은 냉각 효율"
            }},
            {"key": "THERMAL_REAR_DOOR", "label": "ThermalSolution", "name": "Rear-Door Heat Exchanger", "properties": {
                "type": "LIQUID", "max_tdp_w": 800,
                "description": "랙 뒷면 열교환기, 기존 데이터센터 레트로핏"
            }},
        ]

        relationships = [
            {"from_key": "H100_SXM", "to_key": "THERMAL_DLC", "type": "COOLED_BY", "properties": {"note": "NVIDIA recommends DLC"}},
            {"from_key": "B200", "to_key": "THERMAL_DLC", "type": "COOLED_BY", "properties": {"note": "1000W TDP requires liquid"}},
            {"from_key": "B200", "to_key": "THERMAL_IMMERSION", "type": "COOLED_BY", "properties": {"note": "Also immersion option"}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    def _builtin_regulation_data(self) -> dict:
        nodes = [
            {"key": "REG_US_EXPORT_2022", "label": "Regulation", "name": "US Semiconductor Export Controls (Oct 2022)", "properties": {
                "jurisdiction": "United States", "type": "EXPORT_CONTROL",
                "effective_year": 2022,
                "targets": ["China"], "agency": "BIS (Bureau of Industry and Security)",
                "key_restrictions": ["Advanced compute chips (>300 TOPS or >600 TFLOPS)", "EUV equipment", "Advanced packaging equipment"],
                "description": "중국향 첨단 반도체/장비 수출 통제, A100+ 수준 AI 가속기 제한"
            }},
            {"key": "REG_US_EXPORT_2023", "label": "Regulation", "name": "US Export Controls Update (Oct 2023)", "properties": {
                "jurisdiction": "United States", "type": "EXPORT_CONTROL",
                "effective_year": 2023,
                "key_changes": ["Performance density threshold added", "Broader country coverage", "Cloud computing restrictions"],
                "description": "2022년 규제 강화, H800/A800도 제한"
            }},
            {"key": "REG_CHIPS_ACT", "label": "Regulation", "name": "CHIPS and Science Act", "properties": {
                "jurisdiction": "United States", "type": "SUBSIDY",
                "effective_year": 2022, "total_funding_b_usd": 52.7,
                "manufacturing_incentives_b_usd": 39.0,
                "rd_funding_b_usd": 13.2,
                "recipients": ["Intel ($8.5B)", "TSMC ($6.6B)", "Samsung ($6.4B)", "Micron ($6.1B)"],
                "description": "미국 내 반도체 제조/R&D 육성 법안"
            }},
            {"key": "REG_EU_CHIPS_ACT", "label": "Regulation", "name": "European Chips Act", "properties": {
                "jurisdiction": "European Union", "type": "SUBSIDY",
                "effective_year": 2023, "total_funding_b_eur": 43.0,
                "target_market_share_pct": 20,
                "description": "EU 반도체 시장점유율 20% 목표, 생산/R&D 투자"
            }},
            {"key": "REG_JAPAN_EXPORT", "label": "Regulation", "name": "Japan Semiconductor Equipment Export Controls", "properties": {
                "jurisdiction": "Japan", "type": "EXPORT_CONTROL",
                "effective_year": 2023,
                "affected_equipment": ["EUV-related", "Advanced deposition", "Advanced lithography"],
                "description": "일본, 미국과 협조하여 23종 장비 수출 규제 (중국향)"
            }},
        ]

        relationships = [
            {"from_key": "REG_US_EXPORT_2022", "to_key": "VENDOR_ASML", "type": "RESTRICTED_BY", "properties": {"impact": "EUV equipment to China banned"}},
            {"from_key": "REG_CHIPS_ACT", "to_key": "TSMC_FAB_21", "type": "SUBJECT_TO", "properties": {"funding_b_usd": 6.6}},
            {"from_key": "REG_CHIPS_ACT", "to_key": "INTEL_FAB_52_62", "type": "SUBJECT_TO", "properties": {"funding_b_usd": 8.5}},
            {"from_key": "REG_CHIPS_ACT", "to_key": "SAMSUNG_TAYLOR", "type": "SUBJECT_TO", "properties": {"funding_b_usd": 6.4}},
        ]

        return {"nodes": nodes, "relationships": relationships}

    def _builtin_inspection_data(self) -> dict:
        nodes = [
            {"key": "INSP_BROADBAND_PLASMA", "label": "InspectionMethod", "name": "Broadband Plasma Inspection", "properties": {
                "equipment_type": "Wafer Inspection", "vendor": "KLA",
                "model": "KLA 39xx series", "resolution_nm": 15,
                "throughput": "100+ WPH", "detection_capability": "Random defects, pattern defects",
                "description": "광대역 플라즈마 광원 기반 웨이퍼 검사, 인라인 표준"
            }},
            {"key": "INSP_EBEAM", "label": "InspectionMethod", "name": "E-beam Inspection", "properties": {
                "equipment_type": "Wafer Inspection", "vendor": "KLA/Applied/Hermes",
                "resolution_nm": 1, "throughput": "1-5 WPH",
                "detection_capability": "Sub-surface defects, voltage contrast",
                "description": "전자빔 기반 고해상도 검사, 저속이지만 최고 해상도"
            }},
            {"key": "INSP_CD_SEM", "label": "InspectionMethod", "name": "CD-SEM (Critical Dimension SEM)", "properties": {
                "equipment_type": "Metrology", "vendor": "Hitachi/KLA",
                "resolution_nm": 0.5, "measurement": "CD, Line Edge Roughness, Pattern Profile",
                "description": "패턴 임계 치수 측정, 리소그래피 공정 모니터링"
            }},
            {"key": "INSP_OCD", "label": "InspectionMethod", "name": "OCD Scatterometry", "properties": {
                "equipment_type": "Metrology", "vendor": "Nova/KLA",
                "throughput": "60+ WPH", "measurement": "Film thickness, CD, Profile, Overlay",
                "description": "광학 산란 기반 비파괴 계측, 인라인 생산 모니터링"
            }},
            {"key": "INSP_OVERLAY", "label": "InspectionMethod", "name": "Overlay Metrology", "properties": {
                "equipment_type": "Metrology", "vendor": "KLA/ASML",
                "resolution_nm": 0.1, "measurement": "Layer-to-layer alignment accuracy",
                "description": "레이어 간 정렬 정밀도 측정, 다층 리소그래피 핵심"
            }},
        ]

        relationships = [
            # InspectionMethod → Equipment (KLA 장비)
            {"from_key": "INSP_BROADBAND_PLASMA", "to_key": "VENDOR_KLA", "type": "INSPECTED_BY", "properties": {}},
            {"from_key": "INSP_CD_SEM", "to_key": "VENDOR_KLA", "type": "INSPECTED_BY", "properties": {}},
        ]

        return {"nodes": nodes, "relationships": relationships}
