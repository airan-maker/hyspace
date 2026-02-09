"""
Semiconductor Industry Research Agent

반도체 산업 그래프 DB 데이터를 확장하기 위한 Research Agent.
웹 리서치 + LLM 기반 구조화를 통해 Tier 1/2/3 데이터를 수집·정리하고,
기존 온톨로지/GraphMigrator 패턴에 맞게 Neo4j에 적재한다.

Usage:
    python -m research_agent --tier 1 --dry-run
    python -m research_agent --tier 1 --topic foundry
    python -m research_agent --tier all
"""

__version__ = "0.1.0"
