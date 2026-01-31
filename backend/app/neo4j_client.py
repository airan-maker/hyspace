"""
Neo4j Graph Database Client

싱글톤 드라이버 관리 및 FastAPI 의존성 주입
"""

from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError
from typing import Optional, Any
from .config import get_settings

settings = get_settings()


class Neo4jClient:
    """Neo4j 드라이버 싱글톤 관리"""

    _driver: Optional[Driver] = None
    _available: bool = False

    @classmethod
    def connect(cls) -> bool:
        """Neo4j 연결 초기화. 성공 시 True 반환."""
        try:
            cls._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_lifetime=3600,
            )
            cls._driver.verify_connectivity()
            cls._available = True
            print(f"Neo4j connected: {settings.neo4j_uri}")
            return True
        except (ServiceUnavailable, AuthError, Exception) as e:
            cls._driver = None
            cls._available = False
            print(f"Neo4j unavailable (fallback to in-memory ontology): {e}")
            return False

    @classmethod
    def close(cls):
        """드라이버 종료"""
        if cls._driver:
            cls._driver.close()
            cls._driver = None
            cls._available = False

    @classmethod
    def is_available(cls) -> bool:
        return cls._available and cls._driver is not None

    @classmethod
    def get_session(cls) -> Optional[Session]:
        """Neo4j 세션 반환. 미연결 시 None."""
        if not cls.is_available():
            return None
        return cls._driver.session()

    @classmethod
    def run_query(
        cls,
        cypher: str,
        params: Optional[dict] = None,
    ) -> list[dict]:
        """
        Cypher 쿼리 실행 후 결과를 dict 리스트로 반환.

        Neo4j 미연결 시 빈 리스트 반환.
        """
        if not cls.is_available():
            return []

        with cls._driver.session() as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]

    @classmethod
    def run_write(
        cls,
        cypher: str,
        params: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        쓰기 트랜잭션 실행. counters (nodes_created, relationships_created 등) 반환.
        """
        if not cls.is_available():
            return None

        with cls._driver.session() as session:
            result = session.run(cypher, params or {})
            summary = result.consume()
            counters = summary.counters
            return {
                "nodes_created": counters.nodes_created,
                "nodes_deleted": counters.nodes_deleted,
                "relationships_created": counters.relationships_created,
                "relationships_deleted": counters.relationships_deleted,
                "properties_set": counters.properties_set,
            }

    @classmethod
    def get_stats(cls) -> dict:
        """그래프 내 노드/관계 통계 반환"""
        if not cls.is_available():
            return {"available": False}

        node_counts = cls.run_query(
            "CALL db.labels() YIELD label "
            "CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) as cnt', {}) "
            "YIELD value "
            "RETURN label, value.cnt as count"
        )
        rel_counts = cls.run_query(
            "CALL db.relationshipTypes() YIELD relationshipType "
            "CALL apoc.cypher.run("
            "'MATCH ()-[r:`' + relationshipType + '`]->() RETURN count(r) as cnt', {}) "
            "YIELD value "
            "RETURN relationshipType, value.cnt as count"
        )

        return {
            "available": True,
            "nodes": {r["label"]: r["count"] for r in node_counts},
            "relationships": {r["relationshipType"]: r["count"] for r in rel_counts},
            "total_nodes": sum(r["count"] for r in node_counts),
            "total_relationships": sum(r["count"] for r in rel_counts),
        }
