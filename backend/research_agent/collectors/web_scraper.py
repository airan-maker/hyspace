"""
Web Scraper v3 — 반도체 산업 전문 멀티소스 수집기

수집 전략 (우선순위 순):
1. Wikipedia API        — 무료 구조화 데이터, 기업/기술 개요
2. WikiChip             — 공정 노드, 파운드리, 칩 세부 스펙
3. 기업 뉴스룸/IR       — TSMC, NVIDIA, Intel, Samsung 등 공식 발표
4. IEEE/컨퍼런스 초록   — IEDM, ISSCC, VLSI, Hot Chips 논문 초록
5. 산업 분석 블로그     — SemiAnalysis, AnandTech 아카이브, TechInsights 공개 콘텐츠
6. 표준 기관 공개 문서  — JEDEC, SEMI 공개 페이지

API 키 불필요. httpx + BeautifulSoup만 사용.
"""

import hashlib
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import quote

try:
    import httpx
except ImportError:
    httpx = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


# ─────────────────────────────────────────────────────
# Source Registry — 전문 소스 URL 패턴 정의
# ─────────────────────────────────────────────────────

WIKICHIP_PAGES = {
    # 파운드리
    "tsmc": "https://en.wikichip.org/wiki/tsmc",
    "intel": "https://en.wikichip.org/wiki/intel",
    "samsung": "https://en.wikichip.org/wiki/samsung",
    # 공정 노드
    "3nm": "https://en.wikichip.org/wiki/3_nm_lithography_process",
    "5nm": "https://en.wikichip.org/wiki/5_nm_lithography_process",
    "7nm": "https://en.wikichip.org/wiki/7_nm_lithography_process",
    "2nm": "https://en.wikichip.org/wiki/2_nm_lithography_process",
    "10nm": "https://en.wikichip.org/wiki/10_nm_lithography_process",
    # TSMC 공정
    "tsmc n3": "https://en.wikichip.org/wiki/tsmc/n3",
    "tsmc n5": "https://en.wikichip.org/wiki/tsmc/n5",
    "tsmc n4": "https://en.wikichip.org/wiki/tsmc/n4",
    "tsmc n7": "https://en.wikichip.org/wiki/tsmc/n7",
    "tsmc n2": "https://en.wikichip.org/wiki/tsmc/n2",
    # Intel 공정
    "intel 4": "https://en.wikichip.org/wiki/intel/process/intel_4",
    "intel 3": "https://en.wikichip.org/wiki/intel/process/intel_3",
    "intel 7": "https://en.wikichip.org/wiki/intel/process/intel_7",
    "intel 18a": "https://en.wikichip.org/wiki/intel/process/intel_18a",
    "intel 20a": "https://en.wikichip.org/wiki/intel/process/intel_20a",
    # Samsung 공정
    "samsung 3nm": "https://en.wikichip.org/wiki/samsung/process/3_nm",
    "samsung 5nm": "https://en.wikichip.org/wiki/samsung/process/5_nm",
    # 칩 아키텍처
    "nvidia h100": "https://en.wikichip.org/wiki/nvidia/microarchitectures/hopper",
    "nvidia blackwell": "https://en.wikichip.org/wiki/nvidia/microarchitectures/blackwell",
}

CORPORATE_NEWSROOMS = {
    # 기업 → (뉴스룸 URL, source_type)
    "tsmc": [
        ("https://pr.tsmc.com/english/news/all", "corporate_news"),
        ("https://www.tsmc.com/english/dedicatedFoundry/technology/logic", "corporate_tech"),
    ],
    "nvidia": [
        ("https://nvidianews.nvidia.com/news/latest", "corporate_news"),
    ],
    "intel": [
        ("https://www.intc.com/news-events/press-releases", "corporate_news"),
    ],
    "asml": [
        ("https://www.asml.com/en/news", "corporate_news"),
    ],
    "samsung": [
        ("https://news.samsung.com/global/semiconductor", "corporate_news"),
    ],
    "amd": [
        ("https://www.amd.com/en/corporate/newsroom.html", "corporate_news"),
    ],
    "sk hynix": [
        ("https://news.skhynix.com/", "corporate_news"),
    ],
}

IEEE_CONFERENCE_SOURCES = {
    "iedm": [
        ("https://www.ieee-iedm.org/", "conference"),
    ],
    "isscc": [
        ("https://www.isscc.org/", "conference"),
    ],
    "vlsi": [
        ("https://www.vlsisymposium.org/", "conference"),
    ],
}

INDUSTRY_ANALYSIS_SOURCES = [
    # 공개 접근 가능한 산업 분석 블로그/사이트
    ("https://semianalysis.com/", "industry_blog"),
    ("https://semiwiki.com/", "industry_blog"),
    ("https://www.anandtech.com/tag/semiconductors", "tech_media"),
    ("https://www.techinsights.com/blog", "industry_report"),
    ("https://www.yolegroup.com/press-releases/", "industry_report"),
]

STANDARDS_SOURCES = {
    "jedec": [
        ("https://www.jedec.org/standards-documents", "standards_org"),
        ("https://www.jedec.org/category/technology-focus-area/main-memory-ddr3-ddr4-ddr5-etc", "standards_org"),
    ],
    "semi": [
        ("https://www.semi.org/en/products-services/standards", "standards_org"),
    ],
}

# ─────────────────────────────────────────────────────
# Source Reliability Scores — 소스 유형별 신뢰도
# ─────────────────────────────────────────────────────

SOURCE_RELIABILITY_SCORES = {
    "standards_org": 0.90,
    "wikipedia": 0.85,
    "wikipedia_api": 0.85,
    "conference": 0.85,
    "wikichip": 0.80,
    "corporate_tech": 0.80,
    "corporate_news": 0.75,
    "industry_report": 0.70,
    "industry_blog": 0.60,
    "tech_media": 0.55,
    "web_search": 0.50,
    "general": 0.40,
}


class WebScraper:
    """반도체 산업 전문 멀티소스 웹 수집기 v3"""

    RATE_LIMIT_SECONDS = 1.5
    CACHE_TTL_HOURS = 24 * 7  # 1주일
    # Wikipedia는 bot UA를 요구, 일반 사이트는 browser UA가 유리
    WIKI_USER_AGENT = (
        "SiliconNexusResearchBot/0.3 "
        "(https://github.com/silicon-nexus; semiconductor-research) httpx/0.26"
    )
    BROWSER_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    WIKI_API = "https://en.wikipedia.org/w/api.php"

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last_request_time = 0.0
        self._wiki_client: Optional["httpx.Client"] = None
        self._browser_client: Optional["httpx.Client"] = None

    @property
    def wiki_client(self) -> Optional["httpx.Client"]:
        """Wikipedia API 전용 클라이언트 (bot UA)"""
        if self._wiki_client is None and httpx is not None:
            self._wiki_client = httpx.Client(
                headers={"User-Agent": self.WIKI_USER_AGENT},
                timeout=30.0,
                follow_redirects=True,
            )
        return self._wiki_client

    @property
    def client(self) -> Optional["httpx.Client"]:
        """일반 웹 크롤링용 클라이언트 (browser UA)"""
        if self._browser_client is None and httpx is not None:
            self._browser_client = httpx.Client(
                headers={"User-Agent": self.BROWSER_USER_AGENT},
                timeout=30.0,
                follow_redirects=True,
            )
        return self._browser_client

    def close(self):
        if self._wiki_client:
            self._wiki_client.close()
            self._wiki_client = None
        if self._browser_client:
            self._browser_client.close()
            self._browser_client = None

    # ─────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────

    def fetch_and_extract(self, url: str, source_type: str = "general") -> str:
        """URL에서 텍스트 콘텐츠 추출"""
        # Wikipedia URL은 API로 우회 (직접 크롤링 시 403 방지)
        if "wikipedia.org/wiki/" in url:
            title = url.split("/wiki/")[-1].replace("_", " ")
            from urllib.parse import unquote
            title = unquote(title)
            content = self._wikipedia_get_page_content(title)
            if content:
                return content

        html = self._fetch_with_cache(url)
        if not html:
            return ""
        return self._extract_text(html, source_type)

    def search_and_extract(self, query: str, max_results: int = 3) -> list[dict]:
        """
        멀티소스 검색 + 데이터 수집.

        소스 우선순위:
        0. DuckDuckGo 웹 검색 → 실제 검색 엔진 결과 (NEW)
        1. WikiChip 키워드 매칭 → 직접 페이지 크롤링
        2. Wikipedia API 검색 → 본문 추출
        3. 기업 뉴스룸/IR (키워드 매칭)
        4. 표준 기관 소스 (관련 키워드 있을 때)
        """
        results = []
        seen_urls = set()

        # Strategy 0 (NEW): DuckDuckGo 웹 검색 — 실제 검색 엔진 활용
        ddg_results = self._duckduckgo_html_search(query, max_results=5)
        fetched_ddg = self._fetch_search_result_content(ddg_results, max_fetch=3)
        for r in fetched_ddg:
            if r["url"] not in seen_urls and len(results) < max_results + 2:
                results.append(r)
                seen_urls.add(r["url"])

        # Strategy 1: WikiChip 전문 페이지 (존재 확인된 URL만)
        wikichip_results = self._fetch_wikichip_pages(query)
        for r in wikichip_results:
            if r["url"] not in seen_urls and len(results) < max_results + 2:
                results.append(r)
                seen_urls.add(r["url"])

        # Strategy 2: Wikipedia API 검색
        wiki_results = self._wikipedia_search_and_extract(query, max_results=2)
        for r in wiki_results:
            if r["url"] not in seen_urls and len(results) < max_results + 2:
                results.append(r)
                seen_urls.add(r["url"])

        # Strategy 3: 기업 뉴스룸 (관련 키워드 있을 때)
        corp_results = self._fetch_corporate_sources(query)
        for r in corp_results:
            if r["url"] not in seen_urls and len(results) < max_results + 3:
                results.append(r)
                seen_urls.add(r["url"])

        # Strategy 4: 표준 기관 소스 (관련 키워드 있을 때)
        std_results = self._fetch_standards_sources(query)
        for r in std_results:
            if r["url"] not in seen_urls and len(results) < max_results + 3:
                results.append(r)
                seen_urls.add(r["url"])

        return results

    def search_all_sources(self, query: str, topic_id: str = "") -> list[dict]:
        """
        토픽 ID를 활용한 심화 검색 — agent.py에서 호출.

        search_and_extract보다 더 넓은 범위의 전문 소스를 탐색.
        """
        results = self.search_and_extract(query, max_results=3)
        seen = {r["url"] for r in results}

        # NEW: 뉴스 포커스 검색 — 최신 동향 수집
        news_results = self._search_recent_news(query, max_results=3)
        news_fetched = self._fetch_search_result_content(news_results, max_fetch=2)
        for r in news_fetched:
            if r["url"] not in seen:
                r["_is_news"] = True
                results.append(r)
                seen.add(r["url"])

        # 토픽별 추가 소스 검색
        if topic_id:
            extra = self._fetch_topic_specific_sources(topic_id, query)
            for r in extra:
                if r["url"] not in seen:
                    results.append(r)
                    seen.add(r["url"])

        return results

    # ─────────────────────────────────────────────────────
    # WikiChip — 공정 노드, 파운드리 전문 데이터
    # ─────────────────────────────────────────────────────

    def _fetch_wikichip_pages(self, query: str) -> list[dict]:
        """WikiChip에서 키워드 매칭으로 관련 페이지 크롤링"""
        results = []
        query_lower = query.lower()

        for keyword, url in WIKICHIP_PAGES.items():
            if keyword in query_lower:
                try:
                    content = self.fetch_and_extract(url, "wikichip")
                    if content and len(content) > 100:
                        results.append({
                            "source": f"WikiChip: {keyword}",
                            "url": url,
                            "content": content[:8000],
                            "type": "wikichip",
                        })
                except Exception:
                    continue

        return results

    # ─────────────────────────────────────────────────────
    # Wikipedia API — 검색 + 본문 추출
    # ─────────────────────────────────────────────────────

    def _wikipedia_search_and_extract(self, query: str, max_results: int = 3) -> list[dict]:
        """Wikipedia API 검색 → 본문 추출"""
        if not self.client:
            return []

        results = []

        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": max_results + 2,
            "srnamespace": "0",
            "format": "json",
            "utf8": "1",
        }

        search_data = self._fetch_wikipedia_api(search_params)
        if not search_data:
            return []

        search_results = search_data.get("query", {}).get("search", [])

        for item in search_results[:max_results]:
            title = item.get("title", "")
            if not title:
                continue

            content = self._wikipedia_get_page_content(title)
            if content and len(content) > 100:
                results.append({
                    "source": f"Wikipedia: {title}",
                    "url": f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
                    "content": content[:8000],
                    "type": "wikipedia_api",
                })

        return results

    def _wikipedia_get_page_content(self, title: str) -> str:
        """Wikipedia TextExtracts API로 plaintext 본문 추출"""
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": "0",
            "explaintext": "1",
            "exsectionformat": "plain",
            "format": "json",
            "utf8": "1",
        }

        data = self._fetch_wikipedia_api(params)
        if not data:
            return ""

        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id == "-1":
                continue
            extract = page.get("extract", "")
            if extract:
                return extract[:10000]

        return self._wikipedia_parse_page(title)

    def _wikipedia_parse_page(self, title: str) -> str:
        """Wikipedia parse API 폴백"""
        params = {
            "action": "parse",
            "page": title,
            "prop": "text|sections",
            "disabletoc": "1",
            "format": "json",
            "utf8": "1",
        }

        data = self._fetch_wikipedia_api(params)
        if not data:
            return ""

        html = data.get("parse", {}).get("text", {}).get("*", "")
        if not html:
            return ""

        if BeautifulSoup:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all(["script", "style", "sup", "span.mw-editsection"]):
                tag.decompose()
            tables_text = self._extract_tables_from_soup(soup)
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
            result = "\n\n".join(paragraphs[:40])
            if tables_text:
                result += "\n\n[Tables]\n" + tables_text
            return result[:10000]
        else:
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text)
            return text[:10000]

    def _fetch_wikipedia_api(self, params: dict) -> Optional[dict]:
        """Wikipedia API 호출 (캐싱, bot UA 사용)"""
        if not self.wiki_client:
            return None

        cache_key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        cache_file = self.cache_dir / f"wikiapi_{cache_key}.json"

        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                cached_time = datetime.fromisoformat(cached["fetched_at"])
                if datetime.utcnow() - cached_time < timedelta(hours=self.CACHE_TTL_HOURS):
                    return cached["data"]
            except (json.JSONDecodeError, KeyError):
                pass

        self._rate_limit()

        try:
            response = self.wiki_client.get(self.WIKI_API, params=params)
            if response.status_code == 200:
                data = response.json()
                cache_file.write_text(
                    json.dumps({
                        "params": params,
                        "data": data,
                        "fetched_at": datetime.utcnow().isoformat(),
                    }, ensure_ascii=False),
                    encoding="utf-8",
                )
                return data
            else:
                return None
        except Exception:
            return None

    # ─────────────────────────────────────────────────────
    # Corporate Newsrooms — 기업 공식 소스
    # ─────────────────────────────────────────────────────

    def _fetch_corporate_sources(self, query: str) -> list[dict]:
        """쿼리에서 기업명 감지 → 해당 기업 뉴스룸 크롤링"""
        results = []
        query_lower = query.lower()

        for company, sources in CORPORATE_NEWSROOMS.items():
            if company in query_lower:
                for url, stype in sources[:1]:  # 기업당 1개만 (속도)
                    try:
                        content = self.fetch_and_extract(url, stype)
                        if content and len(content) > 100:
                            results.append({
                                "source": f"Corporate: {company.upper()} newsroom",
                                "url": url,
                                "content": content[:6000],
                                "type": stype,
                            })
                    except Exception:
                        continue

        return results

    # ─────────────────────────────────────────────────────
    # Standards Organizations — JEDEC, SEMI 공개 페이지
    # ─────────────────────────────────────────────────────

    def _fetch_standards_sources(self, query: str) -> list[dict]:
        """표준 기관 관련 키워드 감지 → 공개 페이지 크롤링"""
        results = []
        query_lower = query.lower()

        # JEDEC 관련 키워드
        jedec_keywords = ["jedec", "ddr", "lpddr", "gddr", "hbm", "memory standard"]
        if any(kw in query_lower for kw in jedec_keywords):
            for url, stype in STANDARDS_SOURCES.get("jedec", [])[:1]:
                try:
                    content = self.fetch_and_extract(url, stype)
                    if content and len(content) > 100:
                        results.append({
                            "source": "JEDEC Standards",
                            "url": url,
                            "content": content[:6000],
                            "type": stype,
                        })
                except Exception:
                    pass

        # SEMI 관련 키워드
        semi_keywords = ["semi standard", "semiconductor manufacturing standard", "semi e10", "semi e79"]
        if any(kw in query_lower for kw in semi_keywords):
            for url, stype in STANDARDS_SOURCES.get("semi", [])[:1]:
                try:
                    content = self.fetch_and_extract(url, stype)
                    if content and len(content) > 100:
                        results.append({
                            "source": "SEMI Standards",
                            "url": url,
                            "content": content[:6000],
                            "type": stype,
                        })
                except Exception:
                    pass

        return results

    # ─────────────────────────────────────────────────────
    # DuckDuckGo Web Search — 실제 검색 엔진 연동
    # ─────────────────────────────────────────────────────

    def _duckduckgo_html_search(self, query: str, max_results: int = 5) -> list[dict]:
        """DuckDuckGo HTML 검색 (API 키 불필요, JS 불필요)"""
        if not self.client:
            return []

        search_url = "https://html.duckduckgo.com/html/"
        self._rate_limit()

        try:
            response = self.client.post(
                search_url,
                data={"q": query, "b": ""},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if response.status_code != 200:
                return []
        except Exception:
            return []

        if not BeautifulSoup:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for result_div in soup.find_all("div", class_="result")[:max_results]:
            title_el = result_div.find("a", class_="result__a")
            snippet_el = result_div.find("a", class_="result__snippet")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

            actual_url = self._extract_ddg_url(href)
            if not actual_url or not actual_url.startswith("http"):
                continue

            # 저가치 도메인 제외
            if any(skip in actual_url for skip in [
                "youtube.com", "facebook.com", "twitter.com", "x.com",
                "reddit.com", "tiktok.com", "instagram.com",
            ]):
                continue

            results.append({
                "title": title,
                "url": actual_url,
                "snippet": snippet,
                "source": f"DuckDuckGo: {title[:50]}",
                "type": "web_search",
            })

        return results

    @staticmethod
    def _extract_ddg_url(href: str) -> str:
        """DuckDuckGo 리다이렉트 URL에서 실제 URL 추출"""
        from urllib.parse import urlparse, parse_qs, unquote
        if "duckduckgo.com" in href:
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            if "uddg" in params:
                return unquote(params["uddg"][0])
        return href

    def _fetch_search_result_content(self, search_results: list[dict], max_fetch: int = 3) -> list[dict]:
        """검색 결과 URL을 실제 크롤링하여 본문 수집"""
        enriched = []
        for result in search_results[:max_fetch]:
            url = result["url"]
            try:
                source_type = self._classify_source_type(url)
                content = self.fetch_and_extract(url, source_type)
                if content and len(content) > 100:
                    result["content"] = content[:8000]
                    result["type"] = source_type
                    enriched.append(result)
                elif result.get("snippet"):
                    result["content"] = result["snippet"]
                    enriched.append(result)
            except Exception:
                if result.get("snippet"):
                    result["content"] = result["snippet"]
                    enriched.append(result)
        return enriched

    @staticmethod
    def _classify_source_type(url: str) -> str:
        """URL 도메인으로 source_type 자동 분류"""
        url_lower = url.lower()
        if "wikipedia.org" in url_lower:
            return "wikipedia"
        elif "wikichip.org" in url_lower:
            return "wikichip"
        elif any(d in url_lower for d in ["semianalysis", "semiwiki", "techinsights"]):
            return "industry_blog"
        elif any(d in url_lower for d in ["anandtech", "tomshardware", "techpowerup"]):
            return "tech_media"
        elif any(d in url_lower for d in ["jedec.org", "semi.org", "ieee.org"]):
            return "standards_org"
        elif any(d in url_lower for d in [
            "tsmc.com", "intel.com", "nvidia.com", "samsung.com",
            "asml.com", "amd.com", "skhynix.com", "micron.com",
        ]):
            return "corporate_news"
        elif any(d in url_lower for d in ["arxiv.org", "acm.org"]):
            return "conference"
        return "general"

    def _search_recent_news(self, query: str, max_results: int = 3) -> list[dict]:
        """최신 뉴스 검색 — 날짜 한정자 추가"""
        from datetime import datetime
        year = datetime.now().year
        news_query = f"{query} {year} news announcement"
        return self._duckduckgo_html_search(news_query, max_results=max_results)

    # ─────────────────────────────────────────────────────
    # Source Reliability — 소스 신뢰도 평가
    # ─────────────────────────────────────────────────────

    def score_source_reliability(self, source_type: str, url: str = "") -> float:
        """소스 유형 + URL 도메인 기반 신뢰도 점수 (0~1)"""
        base = SOURCE_RELIABILITY_SCORES.get(source_type, 0.40)

        if url:
            url_lower = url.lower()
            if "arxiv.org" in url_lower:
                base = max(base, 0.80)
            elif any(d in url_lower for d in ["ieee.org", "acm.org"]):
                base = max(base, 0.85)
            elif any(d in url_lower for d in [".gov", ".edu"]):
                base = max(base, 0.75)

        return round(base, 2)

    # ─────────────────────────────────────────────────────
    # Topic-Specific Sources — 토픽별 추가 전문 소스
    # ─────────────────────────────────────────────────────

    def _fetch_topic_specific_sources(self, topic_id: str, _query: str = "") -> list[dict]:
        """토픽 ID에 따라 전문 소스에서 추가 데이터 수집"""
        results = []

        # 토픽별 추가 WikiChip 페이지
        TOPIC_EXTRA_WIKICHIP = {
            "foundry_fabsite": [
                "https://en.wikichip.org/wiki/tsmc",
                "https://en.wikichip.org/wiki/intel",
                "https://en.wikichip.org/wiki/samsung",
            ],
            "process_generation": [
                "https://en.wikichip.org/wiki/3_nm_lithography_process",
                "https://en.wikichip.org/wiki/5_nm_lithography_process",
                "https://en.wikichip.org/wiki/7_nm_lithography_process",
                "https://en.wikichip.org/wiki/2_nm_lithography_process",
            ],
            "equipment_ecosystem": [
                "https://en.wikipedia.org/wiki/ASML_Holding",
                "https://en.wikipedia.org/wiki/Applied_Materials",
                "https://en.wikipedia.org/wiki/Lam_Research",
                "https://en.wikipedia.org/wiki/Tokyo_Electron",
                "https://en.wikipedia.org/wiki/KLA_Corporation",
            ],
            "benchmark_performance": [
                "https://en.wikipedia.org/wiki/MLPerf",
            ],
            "regulation_geopolitics": [
                "https://en.wikipedia.org/wiki/CHIPS_and_Science_Act",
                "https://en.wikipedia.org/wiki/European_Chips_Act",
                "https://en.wikipedia.org/wiki/United_States_sanctions_against_China",
            ],
        }

        # 토픽별 Wikipedia 심화 검색 쿼리
        TOPIC_EXTRA_WIKI_QUERIES = {
            "foundry_fabsite": [
                "semiconductor fabrication plant",
                "list of semiconductor fabrication plants",
            ],
            "process_generation": [
                "semiconductor device fabrication",
                "transistor count Moore's law",
            ],
            "memory_standard": [
                "JEDEC memory standards",
                "high bandwidth memory",
                "DDR SDRAM",
            ],
            "interconnect_standard": [
                "PCI Express",
                "NVLink interconnect",
                "Compute Express Link",
            ],
            "packaging_detail": [
                "three-dimensional integrated circuit",
                "chiplet",
                "system in package",
            ],
            "equipment_ecosystem": [
                "semiconductor equipment",
                "photolithography",
                "chemical vapor deposition semiconductor",
            ],
            "material_suppliers": [
                "semiconductor materials",
                "photoresist semiconductor",
                "chemical mechanical polishing",
            ],
            "design_ip": [
                "ARM architecture",
                "RISC-V",
                "electronic design automation",
            ],
            "company_landscape": [
                "semiconductor industry",
                "fabless manufacturing",
                "outsourced semiconductor assembly and test",
            ],
            "thermal_power": [
                "data center cooling",
                "immersion cooling",
                "thermal design power",
            ],
            "reliability_testing": [
                "semiconductor device reliability",
                "electromigration",
                "electrostatic discharge",
            ],
            "inspection_metrology": [
                "semiconductor metrology",
                "wafer inspection",
            ],
        }

        # WikiChip 추가 페이지
        extra_urls = TOPIC_EXTRA_WIKICHIP.get(topic_id, [])
        for url in extra_urls[:2]:
            try:
                stype = "wikichip" if "wikichip" in url else "wikipedia"
                content = self.fetch_and_extract(url, stype)
                if content and len(content) > 100:
                    results.append({
                        "source": f"TopicExtra: {url.split('/')[-1][:40]}",
                        "url": url,
                        "content": content[:6000],
                        "type": stype,
                    })
            except Exception:
                continue

        # Wikipedia 심화 검색
        extra_queries = TOPIC_EXTRA_WIKI_QUERIES.get(topic_id, [])
        for eq in extra_queries[:2]:
            wiki_results = self._wikipedia_search_and_extract(eq, max_results=1)
            results.extend(wiki_results)

        return results

    # ─────────────────────────────────────────────────────
    # HTTP Fetching
    # ─────────────────────────────────────────────────────

    def _rate_limit(self):
        """요청 간 최소 대기 시간 보장"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_SECONDS:
            time.sleep(self.RATE_LIMIT_SECONDS - elapsed)
        self._last_request_time = time.time()

    def _fetch_with_cache(self, url: str) -> Optional[str]:
        """캐시 확인 후 HTTP 요청"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"

        # 캐시 히트
        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                cached_time = datetime.fromisoformat(cached["fetched_at"])
                if datetime.utcnow() - cached_time < timedelta(hours=self.CACHE_TTL_HOURS):
                    return cached["html"]
            except (json.JSONDecodeError, KeyError):
                pass

        if not self.client:
            print("    ! httpx not installed. Cannot fetch web content.")
            return None

        self._rate_limit()

        try:
            response = self.client.get(url)

            if response.status_code == 200:
                html = response.text
                cache_file.write_text(
                    json.dumps({
                        "url": url,
                        "html": html[:500000],
                        "fetched_at": datetime.utcnow().isoformat(),
                    }, ensure_ascii=False),
                    encoding="utf-8",
                )
                return html
            else:
                print(f"    ! HTTP {response.status_code}: {url}")
                return None
        except Exception as e:
            print(f"    ! Fetch error ({url}): {e}")
            return None

    # ─────────────────────────────────────────────────────
    # Text Extraction — 소스 유형별 최적화
    # ─────────────────────────────────────────────────────

    def _extract_text(self, html: str, source_type: str) -> str:
        """소스 유형에 따라 최적화된 텍스트 추출"""
        if BeautifulSoup is None:
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text)
            return text[:10000]

        soup = BeautifulSoup(html, "lxml" if _has_lxml() else "html.parser")

        # 공통: 불필요 태그 제거
        for tag in soup.find_all(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()

        if source_type == "wikichip":
            return self._extract_wikichip(soup)
        elif source_type == "wikipedia":
            return self._extract_wikipedia(soup)
        elif source_type in ("corporate_news", "corporate_tech"):
            return self._extract_corporate(soup)
        elif source_type == "conference":
            return self._extract_conference(soup)
        elif source_type in ("industry_blog", "tech_media", "industry_report"):
            return self._extract_article(soup)
        elif source_type == "standards_org":
            return self._extract_standards(soup)
        else:
            return self._extract_general(soup)

    def _extract_wikichip(self, soup) -> str:
        """WikiChip 페이지 추출 — 스펙 테이블 + 본문"""
        content = soup.find("div", {"id": "mw-content-text"})
        if not content:
            content = soup.find("main") or soup.find("body")
        if not content:
            return ""

        # 스펙 테이블 (WikiChip의 핵심 데이터)
        tables_text = self._extract_tables_from_soup(content)

        # 본문
        paragraphs = [p.get_text(strip=True) for p in content.find_all("p") if p.get_text(strip=True)]

        result = "\n\n".join(paragraphs[:30])
        if tables_text:
            result += "\n\n[Spec Tables]\n" + tables_text

        return result[:10000]

    def _extract_wikipedia(self, soup) -> str:
        """Wikipedia 페이지 추출 — 인포박스 + 본문 + 테이블"""
        content = soup.find("div", {"id": "mw-content-text"})
        if not content:
            return ""

        for tag in content.find_all("span", class_="mw-editsection"):
            tag.decompose()
        for tag in content.find_all("sup", class_="reference"):
            tag.decompose()

        # 인포박스
        infobox_text = ""
        infobox = content.find("table", class_=re.compile(r"infobox"))
        if infobox:
            rows = []
            for tr in infobox.find_all("tr"):
                th = tr.find("th")
                td = tr.find("td")
                if th and td:
                    rows.append(f"{th.get_text(strip=True)}: {td.get_text(strip=True)}")
            if rows:
                infobox_text = "[Infobox]\n" + "\n".join(rows)

        paragraphs = [p.get_text(strip=True) for p in content.find_all("p") if p.get_text(strip=True)]
        tables_text = self._extract_tables_from_soup(content)

        parts = []
        if infobox_text:
            parts.append(infobox_text)
        parts.append("\n\n".join(paragraphs[:30]))
        if tables_text:
            parts.append("[Tables]\n" + tables_text)

        return "\n\n".join(parts)[:10000]

    def _extract_corporate(self, soup) -> str:
        """기업 뉴스룸/IR 페이지 추출 — 뉴스 제목 + 날짜 + 요약"""
        articles = []

        # 뉴스 아이템 패턴 탐색
        for article in soup.find_all(["article", "div"], class_=re.compile(
            r"news|press|release|post|article|item|card", re.I
        ))[:20]:
            title_el = article.find(["h2", "h3", "h4", "a"])
            title = title_el.get_text(strip=True) if title_el else ""

            date_el = article.find(["time", "span", "div"], class_=re.compile(r"date|time|published", re.I))
            date = date_el.get_text(strip=True) if date_el else ""

            summary_el = article.find(["p", "div"], class_=re.compile(r"summary|excerpt|desc|body", re.I))
            summary = summary_el.get_text(strip=True) if summary_el else ""

            if title:
                entry = f"- {title}"
                if date:
                    entry += f" ({date})"
                if summary:
                    entry += f"\n  {summary[:200]}"
                articles.append(entry)

        if articles:
            return "[Corporate News]\n" + "\n".join(articles)

        # 폴백: 일반 텍스트 추출
        return self._extract_general(soup)

    def _extract_conference(self, soup) -> str:
        """컨퍼런스 사이트 추출 — 프로그램/세션/논문 목록"""
        # 프로그램/세션 관련 링크와 텍스트
        sessions = []
        for heading in soup.find_all(["h2", "h3", "h4"]):
            text = heading.get_text(strip=True)
            if text:
                sessions.append(f"\n## {text}")
                # 형제 요소에서 내용 추출
                sibling = heading.find_next_sibling()
                if sibling and sibling.name in ["p", "ul", "ol", "div"]:
                    sessions.append(sibling.get_text(strip=True)[:500])

        if sessions:
            return "[Conference Info]\n" + "\n".join(sessions)[:10000]

        return self._extract_general(soup)

    def _extract_article(self, soup) -> str:
        """기술 블로그/산업 분석 기사 추출"""
        # 기사 목록 페이지
        articles = []
        for item in soup.find_all(["article", "div"], class_=re.compile(
            r"post|article|entry|blog|card", re.I
        ))[:15]:
            title_el = item.find(["h2", "h3", "a"])
            title = title_el.get_text(strip=True) if title_el else ""
            if title and len(title) > 10:
                excerpt_el = item.find(["p", "div"], class_=re.compile(r"excerpt|summary|desc|preview", re.I))
                excerpt = excerpt_el.get_text(strip=True)[:200] if excerpt_el else ""
                entry = f"- {title}"
                if excerpt:
                    entry += f"\n  {excerpt}"
                articles.append(entry)

        if articles:
            return "[Industry Analysis]\n" + "\n".join(articles)

        # 단일 기사 페이지
        article = soup.find("article") or soup.find("main")
        if article:
            paragraphs = [p.get_text(strip=True) for p in article.find_all("p") if p.get_text(strip=True)]
            return "\n\n".join(paragraphs[:30])[:10000]

        return self._extract_general(soup)

    def _extract_standards(self, soup) -> str:
        """표준 기관 페이지 추출 — 표준 목록, 문서 번호"""
        # 표준 문서 목록 추출
        standards = []
        for item in soup.find_all(["tr", "li", "div", "article"], class_=re.compile(
            r"standard|document|spec|result|item", re.I
        ))[:30]:
            text = item.get_text(strip=True)
            if text and len(text) > 20:
                standards.append(f"- {text[:300]}")

        if standards:
            return "[Standards Documents]\n" + "\n".join(standards)

        return self._extract_general(soup)

    def _extract_general(self, soup) -> str:
        """일반 웹페이지 텍스트 추출"""
        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_="content")
            or soup.find("body")
        )
        if not main:
            return ""

        text = main.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines[:200])[:10000]

    def _extract_tables_from_soup(self, soup) -> str:
        """HTML에서 테이블 데이터를 텍스트로 변환"""
        tables_text = []
        for table in soup.find_all("table", class_=re.compile(r"wikitable|infobox|sortable|spec")):
            rows = []
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(" | ".join(cells))
            if rows:
                tables_text.append("\n".join(rows))

        return "\n\n".join(tables_text[:10])


def _has_lxml() -> bool:
    try:
        import lxml  # noqa: F401
        return True
    except ImportError:
        return False
