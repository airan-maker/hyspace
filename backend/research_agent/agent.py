"""
Research Agent — 메인 CLI 오케스트레이터

Usage:
    python -m research_agent --tier 1
    python -m research_agent --tier 1 --topic foundry_fabsite
    python -m research_agent --tier all --dry-run
    python -m research_agent --list-topics
    python -m research_agent --status
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Windows 콘솔 UTF-8 출력 보장
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# .env 파일에서 환경변수 로드 (ANTHROPIC_API_KEY 등)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from .config import (
    Tier, TopicStatus, ResearchTopic,
    ALL_TOPICS, get_topics_by_tier, get_topic,
)

# 진행 상태 파일 경로
STATE_FILE = Path(__file__).parent / "data" / "agent_state.json"


class ResearchAgent:
    """반도체 산업 데이터 리서치 에이전트 v2"""

    def __init__(self, dry_run: bool = False, verbose: bool = True, quality_report: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.quality_report = quality_report
        self.state = self._load_state()

    # ─────────────────────────────────────────────────────
    # State Management
    # ─────────────────────────────────────────────────────

    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"topics": {}, "last_run": None, "stats": {}}

    def _save_state(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False, default=str)

    def _update_topic_status(self, topic_id: str, status: TopicStatus, detail: str = ""):
        self.state["topics"][topic_id] = {
            "status": status.value,
            "detail": detail,
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._save_state()

    # ─────────────────────────────────────────────────────
    # Topic Listing & Status
    # ─────────────────────────────────────────────────────

    def list_topics(self):
        """모든 토픽 목록 출력"""
        for tier_name, tier_val in [("Tier 1", Tier.TIER1), ("Tier 2", Tier.TIER2), ("Tier 3", Tier.TIER3)]:
            topics = get_topics_by_tier(tier_val)
            print(f"\n{'='*60}")
            print(f"  {tier_name} — {len(topics)} topics")
            print(f"{'='*60}")
            for tid, topic in topics.items():
                status = self.state.get("topics", {}).get(tid, {}).get("status", "pending")
                status_icon = {
                    "pending": "○", "collecting": "◐", "extracting": "◑",
                    "validating": "◕", "complete": "●", "failed": "✗",
                }.get(status, "?")
                print(f"  {status_icon} {tid:<30s} {topic.name_kr}")
                print(f"    Nodes: {topic.node_labels}")
                print(f"    Edges: {topic.relationship_types}")

    def show_status(self):
        """현재 진행 상태 출력"""
        print("\n=== Research Agent Status ===")
        print(f"Last run: {self.state.get('last_run', 'Never')}")

        total = len(ALL_TOPICS)
        completed = sum(
            1 for t in ALL_TOPICS
            if self.state.get("topics", {}).get(t, {}).get("status") == "complete"
        )
        print(f"Progress: {completed}/{total} topics completed")

        stats = self.state.get("stats", {})
        if stats:
            print(f"\nCollected Data:")
            print(f"  Nodes collected: {stats.get('total_nodes', 0)}")
            print(f"  Relationships: {stats.get('total_relationships', 0)}")
            print(f"  Web pages fetched: {stats.get('pages_fetched', 0)}")
            print(f"  LLM calls: {stats.get('llm_calls', 0)}")

    # ─────────────────────────────────────────────────────
    # Main Execution
    # ─────────────────────────────────────────────────────

    def run(self, tier: Optional[str] = None, topic_id: Optional[str] = None):
        """리서치 실행"""
        self.state["last_run"] = datetime.utcnow().isoformat()
        self._save_state()

        # 실행할 토픽 결정
        if topic_id:
            topic = get_topic(topic_id)
            if not topic:
                print(f"Error: Unknown topic '{topic_id}'")
                print(f"Available: {list(ALL_TOPICS.keys())}")
                return
            topics_to_run = {topic_id: topic}
        elif tier:
            tier_enum = {"1": Tier.TIER1, "2": Tier.TIER2, "3": Tier.TIER3, "all": None}.get(tier)
            if tier == "all":
                topics_to_run = ALL_TOPICS
            elif tier_enum:
                topics_to_run = get_topics_by_tier(tier_enum)
            else:
                print(f"Error: Invalid tier '{tier}'. Use 1, 2, 3, or all")
                return
        else:
            print("Error: Specify --tier or --topic")
            return

        print(f"\n{'='*60}")
        print(f"  Research Agent — {len(topics_to_run)} topics to process")
        print(f"  Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"{'='*60}")

        for tid, topic in topics_to_run.items():
            self._process_topic(tid, topic)

        print(f"\n{'='*60}")
        print("  Research complete!")
        print(f"{'='*60}")
        self.show_status()

    def _process_topic(self, topic_id: str, topic: ResearchTopic):
        """단일 토픽 처리 파이프라인 v2"""
        print(f"\n--- [{topic.tier.value}] {topic.name_kr} ({topic_id}) ---")

        # Step 1: 웹 수집
        self._update_topic_status(topic_id, TopicStatus.COLLECTING)
        print("  [1/4] 웹 데이터 수집 중...")
        raw_data = self._collect_web_data(topic)

        # Step 1.5: 수집된 원시 데이터 저장
        self._save_raw_data(topic_id, raw_data)

        # Step 2: LLM 구조화 (raw_sources 직접 전달로 우선순위 컨텍스트 빌딩)
        self._update_topic_status(topic_id, TopicStatus.EXTRACTING)
        print("  [2/4] 구조화 추출 중...")
        structured_data = self._extract_structured_data(topic, raw_data)

        # Step 3: 검증 + 품질 평가
        self._update_topic_status(topic_id, TopicStatus.VALIDATING)
        print("  [3/4] 데이터 검증 및 품질 평가 중...")
        validated_data = self._validate_data(topic, structured_data, raw_data=raw_data)

        # Step 3.5: 품질 리포트 (옵션)
        if self.quality_report:
            self._print_quality_report(validated_data)

        # Step 4: 온톨로지/그래프 적재
        print("  [4/4] 온톨로지 생성 및 그래프 적재...")
        if self.dry_run:
            print(f"    [DRY RUN] Would create {len(validated_data.get('nodes', []))} nodes, "
                  f"{len(validated_data.get('relationships', []))} relationships")
            self._save_dry_run_output(topic_id, validated_data)
        else:
            self._load_to_graph(topic, validated_data)

        self._update_topic_status(topic_id, TopicStatus.COMPLETE,
                                  f"nodes={len(validated_data.get('nodes', []))}, "
                                  f"sources={len(raw_data)}")
        print(f"  ✓ {topic.name_kr} 완료")

    # ─────────────────────────────────────────────────────
    # Pipeline Steps
    # ─────────────────────────────────────────────────────

    def _collect_web_data(self, topic: ResearchTopic) -> list[dict]:
        """웹 데이터 수집 (Wikipedia API 기반)"""
        from .collectors.web_scraper import WebScraper

        scraper = WebScraper(cache_dir=Path(__file__).parent / "data" / "cache")
        results = []
        seen_urls = set()

        # Step 1: 직접 URL 소스에서 수집
        for source in topic.sources:
            print(f"    Fetching: {source.name}")
            try:
                content = scraper.fetch_and_extract(source.url, source.source_type)
                if content and len(content) > 50:
                    results.append({
                        "source": source.name,
                        "url": source.url,
                        "content": content,
                        "type": source.source_type,
                    })
                    seen_urls.add(source.url)
            except Exception as e:
                print(f"    ! Failed: {source.name} -- {e}")

        # Step 2: 멀티소스 검색 (WikiChip + Wikipedia + 기업 뉴스룸 + 표준 기관)
        for query in topic.search_queries:
            print(f"    Searching: {query[:55]}...")
            try:
                search_results = scraper.search_all_sources(query, topic_id=topic.topic_id)
                for r in search_results:
                    if r["url"] not in seen_urls:
                        results.append(r)
                        seen_urls.add(r["url"])
            except Exception as e:
                print(f"    ! Search failed: {e}")

        scraper.close()

        content_count = sum(1 for r in results if len(r.get("content", "")) > 100)
        print(f"    Collected: {len(results)} sources ({content_count} with substantial content)")

        # 수집 통계 업데이트
        stats = self.state.setdefault("stats", {})
        stats["pages_fetched"] = stats.get("pages_fetched", 0) + len(results)
        self._save_state()

        return results

    def _extract_structured_data(self, topic: ResearchTopic, raw_data: list[dict]) -> dict:
        """원시 데이터를 구조화 (LLM 또는 빌트인 + 웹 데이터 보강)"""
        from .collectors.llm_extractor import LLMExtractor

        extractor = LLMExtractor()

        # v2: raw_sources를 직접 전달 → 우선순위 기반 컨텍스트 빌딩
        result = extractor.extract_for_topic(
            topic_id=topic.topic_id,
            tier=topic.tier.value,
            node_labels=topic.node_labels,
            relationship_types=topic.relationship_types,
            description=topic.description,
            raw_sources=raw_data,
        )

        # 수집된 소스 메타데이터를 결과에 첨부
        result["sources"] = [
            {"source": item.get("source", ""), "url": item.get("url", ""), "type": item.get("type", "")}
            for item in raw_data if item.get("content")
        ]
        result["context_length"] = sum(len(item.get("content", "")) for item in raw_data)

        stats = self.state.setdefault("stats", {})
        if extractor.client:
            # 멀티패스 시 2회 호출
            stats["llm_calls"] = stats.get("llm_calls", 0) + (2 if result.get("context_length", 0) > 5000 else 1)
        self._save_state()

        return result

    def _validate_data(self, topic: ResearchTopic, data: dict, raw_data: list[dict] = None) -> dict:
        """추출된 데이터 검증 + 품질 평가"""
        from .collectors.quality_scorer import QualityScorer

        nodes = data.get("nodes", [])
        relationships = data.get("relationships", [])

        # 기본 검증: 필수 필드, 중복 제거
        validated_nodes = []
        for node in nodes:
            if not node.get("key") or not node.get("label"):
                print(f"    ⚠ Skipping node without key/label: {node}")
                continue
            if any(n["key"] == node["key"] for n in validated_nodes):
                continue
            validated_nodes.append(node)

        validated_rels = []
        for rel in relationships:
            if not rel.get("from_key") or not rel.get("to_key") or not rel.get("type"):
                continue
            validated_rels.append(rel)

        result = {"nodes": validated_nodes, "relationships": validated_rels}

        # v2: 품질 평가 (confidence, freshness) + 교차 검증
        scorer = QualityScorer()
        if raw_data:
            result = scorer.score_extracted_data(result, raw_data)
        result = scorer.cross_validate_nodes(result)

        # 검증 경고 출력
        for warning in result.get("_validation_warnings", []):
            print(f"    ⚠ {warning}")

        print(f"    Validated: {len(result['nodes'])} nodes, {len(result['relationships'])} relationships")

        return result

    def _load_to_graph(self, topic: ResearchTopic, data: dict):
        """Neo4j 그래프에 적재"""
        from .graph.migrator_ext import ExtendedMigrator

        migrator = ExtendedMigrator()
        result = migrator.migrate_research_data(data)

        stats = self.state.setdefault("stats", {})
        stats["total_nodes"] = stats.get("total_nodes", 0) + result.get("nodes_created", 0)
        stats["total_relationships"] = stats.get("total_relationships", 0) + result.get("relationships_created", 0)
        self._save_state()

        print(f"    Graph: +{result.get('nodes_created', 0)} nodes, "
              f"+{result.get('relationships_created', 0)} relationships")

    def _save_raw_data(self, topic_id: str, raw_data: list[dict]):
        """수집된 원시 웹 데이터를 토픽별 JSON으로 저장"""
        raw_dir = Path(__file__).parent / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_file = raw_dir / f"{topic_id}.json"

        # 기존 데이터가 있으면 병합 (새 소스 추가)
        existing = []
        if raw_file.exists():
            try:
                existing = json.loads(raw_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, KeyError):
                pass

        existing_urls = {item.get("url") for item in existing}
        new_items = [item for item in raw_data if item.get("url") not in existing_urls]

        merged = existing + new_items

        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False, default=str)

        if new_items:
            print(f"    Saved: {len(new_items)} new sources -> {raw_file.name} (total: {len(merged)})")

    def _print_quality_report(self, data: dict):
        """품질 리포트 출력"""
        nodes = data.get("nodes", [])
        if not nodes:
            return

        confidences = [n.get("properties", {}).get("confidence", 0) for n in nodes]
        freshness = [n.get("properties", {}).get("freshness_score", 0) for n in nodes]

        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        avg_fresh = sum(freshness) / len(freshness) if freshness else 0
        low_conf = sum(1 for c in confidences if c < 0.5)

        print(f"    ── Quality Report ──")
        print(f"      Avg confidence: {avg_conf:.2f}")
        print(f"      Avg freshness:  {avg_fresh:.2f}")
        print(f"      Low-confidence nodes (<0.5): {low_conf}/{len(nodes)}")

        for w in data.get("_validation_warnings", []):
            print(f"      Warning: {w}")

    def _save_dry_run_output(self, topic_id: str, data: dict):
        """드라이런 결과를 파일로 저장"""
        output_dir = Path(__file__).parent / "data" / "dry_run"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{topic_id}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        print(f"    Saved to: {output_file}")


# ============================================================
# CLI Entry Point
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Semiconductor Industry Research Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m research_agent --list-topics          # 전체 토픽 목록
  python -m research_agent --status               # 진행 상태
  python -m research_agent --tier 1 --dry-run     # Tier 1 드라이런
  python -m research_agent --tier 1               # Tier 1 실행
  python -m research_agent --topic foundry_fabsite # 특정 토픽만
  python -m research_agent --tier all              # 전체 실행
        """,
    )
    parser.add_argument("--tier", choices=["1", "2", "3", "all"],
                        help="실행할 Tier (1, 2, 3, or all)")
    parser.add_argument("--topic", help="특정 토픽 ID만 실행")
    parser.add_argument("--dry-run", action="store_true",
                        help="실제 적재 없이 결과만 출력/저장")
    parser.add_argument("--list-topics", action="store_true",
                        help="사용 가능한 토픽 목록 출력")
    parser.add_argument("--status", action="store_true",
                        help="현재 진행 상태 출력")
    parser.add_argument("--quality-report", action="store_true",
                        help="처리 후 데이터 품질 리포트 출력")
    parser.add_argument("--verbose", "-v", action="store_true", default=True)

    args = parser.parse_args()

    agent = ResearchAgent(
        dry_run=args.dry_run,
        verbose=args.verbose,
        quality_report=args.quality_report,
    )

    if args.list_topics:
        agent.list_topics()
    elif args.status:
        agent.show_status()
    elif args.tier or args.topic:
        agent.run(tier=args.tier, topic_id=args.topic)
    else:
        parser.print_help()
