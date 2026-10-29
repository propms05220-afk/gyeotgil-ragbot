"""표 데이터용 도구 (tasks/05, 선택). 처음에는 도메인 도구가 하나도 없습니다.

도구를 켜는 순서:
  1. 아래 예시의 주석을 풀고, 이름·설명·인자를 내 표에 맞게 고칩니다.
  2. config.yaml 의 agent.tools 와, 표 소스 카드(sources.<이름>.tools)에 도구 이름을 적습니다.
  3. tests/test_domain.py 에 단위 테스트, eval/golden_qa.jsonl 에 이 도구가 필요한 질문을 하나 이상 추가합니다.

LLM은 코드를 보지 않습니다. 이름, 설명, 인자 설명만 봅니다. 그래서 설명에는 "언제 쓰는지"와
"언제 쓰지 않는지"를 구체적으로 씁니다. 결과에는 항상 "source"가 있어야 답변에 출처가 붙습니다.
"""
# from ragbot.domain import queries
# from ragbot.domain.tables import db_path
# from ragbot.tools import Context, tool
#
#
# @tool("search_items",
#       "Search the TODO table. Use for ANY question about TODO (which items exist, prices, counts …). "
#       "Not for TODO (use search_documents). Returns total_matches (use it for 'how many') and example rows.",
#       {"keyword": {"type": "string", "description": "Words to find in TODO columns, e.g. 'TODO'"},
#        "max_results": {"type": "integer", "description": "Default 15"}})
# def search_items(ctx: Context, keyword: str | None = None, max_results: int | None = None):
#     return queries.search_rows(db_path(ctx.cfg), keyword, max_results or ctx.cfg["tables"]["max_results"])
