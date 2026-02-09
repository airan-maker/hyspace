"""
AI Insight Service

Claude API를 사용하여 그래프 쿼리 결과에 대한 도메인 분석을 생성합니다.
"""

import json
from typing import AsyncGenerator

import anthropic

from ..config import get_settings

settings = get_settings()

# 쿼리 타입별 시스템 프롬프트
SYSTEM_PROMPT = """당신은 반도체 제조 공급망 전문 분석가입니다.
Neo4j 그래프 데이터베이스의 쿼리 결과를 바탕으로, 반도체 공정/소재/장비 전문 지식을 활용하여
실무 엔지니어가 즉시 활용할 수 있는 분석을 제공합니다.

분석 시 다음을 포함하세요:
1. 핵심 발견 사항 (가장 중요한 인사이트 3개)
2. 리스크 평가 및 우선순위
3. 실무 권장 사항

간결하고 구조적으로 작성하세요. 마크다운 형식을 사용하세요."""

# 쿼리 타입별 사용자 프롬프트 템플릿
PROMPT_TEMPLATES: dict[str, str] = {
    "h100_context": """다음은 NVIDIA H100 AI 가속기의 전체 컨텍스트 (공정, 메모리, 패키징, 호환 모델) 쿼리 결과입니다.

{results}

H100의 기술적 포지셔닝, 제조 공정 의존성, 경쟁 구도를 분석하고, 공급망 관점의 잠재적 리스크를 평가해주세요.""",

    "h100_supply_risks": """다음은 H100 AI 가속기에 영향을 주는 공급망 리스크 분석 결과입니다 (가속기 → 공정 → 소재 경로의 다중 홉 질의).

{results}

각 리스크의 심각도를 평가하고, 단일 장애점(Single Point of Failure)을 식별하며, 공급 중단 시 H100 생산에 미치는 영향과 완화 전략을 제안해주세요.""",

    "b200_supply_risks": """다음은 NVIDIA B200 (Blackwell) AI 가속기의 공급망 리스크 분석 결과입니다.

{results}

B200은 차세대 가속기로서 H100 대비 어떤 추가 공급망 리스크가 있는지, 특히 첨단 공정(N3P 등)과 HBM3E 의존성 측면에서 분석해주세요.""",

    "process_flow": """다음은 반도체 13단계 공정 플로우와 각 단계별 결함/장비/소재 리스크 분석 결과입니다.

{results}

수율 영향이 HIGH인 공정 단계를 식별하고, 결함 발생 확률이 높은 구간의 원인과 장비/소재 의존성을 분석해주세요. 전체 수율 개선을 위한 우선 대응 공정을 3가지 추천해주세요.""",

    "euv_impact": """다음은 ASML EUV 장비 고장 시 전체 영향 분석 결과입니다.

{results}

EUV 장비 고장 시 연쇄 영향 범위 (영향받는 공정, 결함 타입, 관련 소재)를 분석하고, MTBF/MTTR 기반 가동률 영향과 예방 보전 전략을 제안해주세요.""",

    "euv_resist_dep": """다음은 EUV 포토레지스트의 소재 의존성 체인 분석 결과입니다 (소재 → 공정 → 장비 → 고장모드).

{results}

EUV 레지스트 공급 중단 시 영향 체인을 분석하고, 지리적 집중도와 대체 공급원 확보 가능성을 평가해주세요.""",

    "critical_materials": """다음은 공급 리스크가 HIGH 이상인 핵심 소재 목록과 영향 범위입니다.

{results}

가장 위험한 소재 TOP 3를 선정하고, 각각의 공급 중단 시나리오별 영향 범위와 대응 전략을 제안해주세요. 지정학적 리스크(geographic concentration)도 고려해주세요.""",

    "h100_to_euv": """다음은 H100 가속기와 EUV Photoresist 간의 관계 경로 탐색 결과입니다.

{results}

H100 생산과 EUV 소재 간의 의존 경로를 분석하고, 이 경로상의 취약점과 병목 구간을 식별해주세요.""",

    "custom": """다음은 사용자가 실행한 Cypher 쿼리의 결과입니다.

{results}

이 결과에서 발견할 수 있는 주요 패턴, 잠재적 리스크, 실무적 시사점을 분석해주세요.""",
}


def _get_client() -> anthropic.Anthropic:
    api_key = settings.anthropic_api_key
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일에 ANTHROPIC_API_KEY를 추가하세요.")
    return anthropic.Anthropic(api_key=api_key)


def _build_prompt(query_type: str, results: object) -> str:
    template = PROMPT_TEMPLATES.get(query_type, PROMPT_TEMPLATES["custom"])
    results_str = json.dumps(results, ensure_ascii=False, indent=2, default=str)
    # 토큰 제한을 위해 결과 크기 제한
    if len(results_str) > 8000:
        results_str = results_str[:8000] + "\n... (결과 일부 생략)"
    return template.format(results=results_str)


def generate_insight(query_type: str, results: object) -> str:
    """쿼리 결과에 대한 AI 인사이트를 생성합니다 (동기)."""
    client = _get_client()
    user_prompt = _build_prompt(query_type, results)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text


async def generate_insight_stream(query_type: str, results: object) -> AsyncGenerator[str, None]:
    """쿼리 결과에 대한 AI 인사이트를 SSE 스트리밍으로 생성합니다."""
    client = _get_client()
    user_prompt = _build_prompt(query_type, results)

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {json.dumps({'chunk': text}, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"
