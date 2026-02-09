"""
Tier 2 Ontology Writer

장비 벤더, 소재 공급사, 설계 IP, 기업, 벤치마크 온톨로지 생성
"""

from pathlib import Path
from datetime import datetime


class Tier2OntologyWriter:
    """Tier 2 데이터를 Python 온톨로지로 변환"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent.parent.parent / "app" / "ontology"

    def write_all(self, data: dict) -> list[Path]:
        """Tier 2 온톨로지 파일 생성"""
        # Tier 2는 기존 equipment.py, materials.py를 확장하는 형태
        # 별도 파일 생성 대신 기존 데이터에 추가
        return []
