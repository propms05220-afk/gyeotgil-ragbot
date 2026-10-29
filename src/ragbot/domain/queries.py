"""표에 대한 안전한 질의 (tasks/05, 선택). LLM은 SQL을 쓰지 않습니다. 필터 인자만 채웁니다.

규칙: 열 이름과 SQL 문장은 코드가 정하고, 사용자가 준 값은 언제나 ? 자리표시자로 넘깁니다.
질문 유형마다 함수 하나를 만드세요 (찾기, 하나 자세히 보기, 개수 세기 …).
search_rows 는 시작점 예시입니다. 원본 프로젝트의 search_courses / get_course 도 참고하세요.
"""
import sqlite3

from ragbot.domain.tables import TABLE

SOURCE = "table"   # TODO(05): 답변의 출처 표시에 쓰일 이름 (예: "product catalog")

# TODO(05): keyword 가 검색할 열 (tables.py 의 COLUMNS 에서 정한 이름)
SEARCH_COLUMNS: list[str] = []


def _rows(db_path, sql: str, params: list) -> list[dict]:
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        return [dict(r) for r in con.execute(sql, params)]


def search_rows(db_path, keyword: str | None = None, max_results: int = 15) -> dict:
    where, params = [], []
    if keyword and SEARCH_COLUMNS:
        for word in keyword.split():   # 모든 단어가 어느 한 열에는 있어야 함
            where.append("(" + " OR ".join(f"{col} LIKE ?" for col in SEARCH_COLUMNS) + ")")
            params += [f"%{word}%"] * len(SEARCH_COLUMNS)
    # TODO(05): 필터 추가. 예: if max_price is not None: where.append("CAST(price AS REAL) <= ?"); params.append(max_price)
    clause = " WHERE " + " AND ".join(where) if where else ""
    total = _rows(db_path, f"SELECT COUNT(*) AS n FROM {TABLE}{clause}", params)[0]["n"]
    rows = _rows(db_path, f"SELECT * FROM {TABLE}{clause} LIMIT ?", params + [int(max_results)])
    return {"source": SOURCE, "total_matches": total, "shown": len(rows), "rows": rows,
            "summary": f"{total} rows match in total; the first {len(rows)} are listed. "
                       "For 'how many' questions answer with the total, not the number listed."}
