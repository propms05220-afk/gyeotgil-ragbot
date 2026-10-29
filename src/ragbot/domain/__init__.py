"""이 챗봇에만 해당하는 코드는 모두 이 패키지에 둡니다 (config.yaml, data/, eval/golden_qa.jsonl과 함께).

코어는 다음 네 가지 이름만 호출합니다:
  SECTION_RULES        문서가 섹션을 표시하는 방식                    (sections.py, tasks/04)
  build_tables(cfg)    표 데이터 → 데이터베이스, build 때 한 번         (tables.py, tasks/05, 선택)
  tables_ready(cfg)    데이터베이스가 준비됐으면 None, 아니면 실행할 명령을 알려 주는 메시지
  tools.py             @tool로 등록하는 도메인 도구; config.yaml의 agent.tools와 sources에 이름을 적습니다

처음 상태: 섹션 규칙은 kordoc 기본값, 표 없음, 도메인 도구 없음. 문서 검색과 웹 검색만으로 동작합니다.
완성된 예시는 원본 프로젝트(rag_chatbot_starter)의 src/ragbot/domain/ 을 보세요.
"""
from ragbot.domain.sections import SECTION_RULES
from ragbot.domain.tables import build_tables, tables_ready

__all__ = ["SECTION_RULES", "build_tables", "tables_ready"]
