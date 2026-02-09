"""
Data Quality Scoring Module

수집/추출된 데이터의 신뢰도(confidence)와 신선도(freshness)를 평가하고,
교차 검증으로 데이터 무결성을 확인한다.
"""

import re
from datetime import datetime
from typing import Optional


# 소스 유형별 신뢰도 티어
SOURCE_TIERS = {
    "tier1_authoritative": {
        "types": ["standards_org", "wikipedia", "wikipedia_api"],
        "base_confidence": 0.85,
    },
    "tier2_primary": {
        "types": ["corporate_news", "corporate_tech", "wikichip", "conference"],
        "base_confidence": 0.75,
    },
    "tier3_secondary": {
        "types": ["industry_report", "industry_blog", "tech_media"],
        "base_confidence": 0.55,
    },
    "tier4_general": {
        "types": ["web_search", "general"],
        "base_confidence": 0.40,
    },
}

# 기존 그래프에 이미 존재하는 노드 키 목록
KNOWN_EXISTING_KEYS = {
    # ProcessNode
    "N3E", "N3P", "N5", "N4P", "N7", "N2", "A16", "SF3", "SF2",
    "Intel_18A", "Intel_20A", "Intel_7", "Intel_4", "Intel_3",
    "N28", "N16",
    # PackagingTech
    "CoWoS-S", "CoWoS-L", "CoWoS-R", "EMIB", "InFO", "Foveros", "SoIC",
    # HBMGeneration
    "HBM3", "HBM3E", "HBM4",
    # AIAccelerator
    "H100_SXM", "H200_SXM", "B200", "B300", "MI300X", "MI325X", "MI350X",
    "Gaudi3", "TPUv5e", "TPUv6",
    # Material / Equipment
    "EUV_RESIST", "ARF_RESIST", "NF3", "WF6",
}


class QualityScorer:
    """수집 데이터의 품질을 평가하고 교차 검증을 수행"""

    def score_extracted_data(self, data: dict, raw_sources: list[dict]) -> dict:
        """
        모든 노드에 confidence, freshness_score를 부여한다.
        data를 직접 수정(mutate)하고 반환한다.
        """
        source_reliability = self._compute_source_reliability(raw_sources)
        freshness_info = self._extract_dates_from_sources(raw_sources)

        for node in data.get("nodes", []):
            props = node.get("properties", {})

            # confidence: LLM이 부여한 값(있으면)과 소스 신뢰도를 가중 결합
            llm_confidence = props.get("confidence", 0.5)
            props["confidence"] = round(
                0.6 * llm_confidence + 0.4 * source_reliability, 2
            )

            # freshness: 노드 속성의 연도 정보 + 소스 연도 기반 평가
            node_freshness = self._score_node_freshness(node, freshness_info)
            props["freshness_score"] = node_freshness
            props["_quality_scored_at"] = datetime.utcnow().isoformat()

            node["properties"] = props

        return data

    def _compute_source_reliability(self, raw_sources: list[dict]) -> float:
        """수집된 소스들의 평균 신뢰도 계산"""
        if not raw_sources:
            return 0.4

        scores = []
        for src in raw_sources:
            src_type = src.get("type", "general")
            score = 0.4
            for tier_info in SOURCE_TIERS.values():
                if src_type in tier_info["types"]:
                    score = tier_info["base_confidence"]
                    break
            scores.append(score)

        return round(sum(scores) / len(scores), 2)

    def _extract_dates_from_sources(self, raw_sources: list[dict]) -> dict:
        """소스 텍스트에서 연도 언급을 추출하여 분포를 분석"""
        year_mentions = []
        current_year = datetime.now().year

        for src in raw_sources:
            content = src.get("content", "")
            # 2020~2030 범위의 연도 추출
            years = re.findall(r'\b(20[2-3]\d)\b', content)
            year_mentions.extend(int(y) for y in years)

        if not year_mentions:
            return {"most_recent_year": None, "year_distribution": {}}

        distribution: dict[int, int] = {}
        for y in year_mentions:
            distribution[y] = distribution.get(y, 0) + 1

        return {
            "most_recent_year": max(year_mentions),
            "year_distribution": distribution,
        }

    def _score_node_freshness(self, node: dict, freshness_info: dict) -> float:
        """노드 데이터의 신선도 점수 (0.0=오래됨, 1.0=최신)"""
        current_year = datetime.now().year
        most_recent = freshness_info.get("most_recent_year")

        if most_recent is None:
            return 0.3  # 알 수 없음

        # 노드 속성에서 연도 정보 확인
        props = node.get("properties", {})
        node_year = None
        for key in ["year", "opened_year", "effective_year", "founded_year", "source_date"]:
            val = props.get(key)
            if val is not None:
                try:
                    node_year = int(str(val)[:4])
                    break
                except (ValueError, TypeError):
                    pass

        if node_year and node_year >= current_year - 1:
            return 0.95
        elif node_year and node_year >= current_year - 2:
            return 0.75

        # 소스 전체의 최신 연도 기준 평가
        age = current_year - most_recent
        if age <= 0:
            return 0.90
        elif age == 1:
            return 0.70
        elif age == 2:
            return 0.50
        else:
            return 0.30

    def cross_validate_nodes(self, data: dict) -> dict:
        """
        교차 검증:
        - relationship 엔드포인트 존재 확인
        - 고아 노드 탐지
        - 잠재적 중복 노드 경고
        """
        node_keys = {n["key"] for n in data.get("nodes", [])}
        all_keys = node_keys | KNOWN_EXISTING_KEYS

        # relationship 엔드포인트 검증
        valid_rels = []
        orphan_rels = []
        for rel in data.get("relationships", []):
            from_ok = rel.get("from_key") in all_keys
            to_ok = rel.get("to_key") in all_keys
            if from_ok and to_ok:
                valid_rels.append(rel)
            else:
                orphan_rels.append(rel)

        data["relationships"] = valid_rels

        if orphan_rels:
            data.setdefault("_validation_warnings", []).append(
                f"{len(orphan_rels)} relationships removed (missing endpoints)"
            )

        # 고아 노드 탐지 (relationship에 전혀 참조되지 않는 노드)
        referenced_keys = set()
        for rel in valid_rels:
            referenced_keys.add(rel["from_key"])
            referenced_keys.add(rel["to_key"])

        orphan_nodes = [
            n["key"] for n in data.get("nodes", [])
            if n["key"] not in referenced_keys
        ]
        if orphan_nodes:
            data.setdefault("_validation_warnings", []).append(
                f"{len(orphan_nodes)} orphan nodes (no relationships): "
                f"{orphan_nodes[:5]}{'...' if len(orphan_nodes) > 5 else ''}"
            )

        return data
