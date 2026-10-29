"""표 데이터(xlsx 또는 csv) → SQLite (tasks/05, 선택).

표가 없는 챗봇: config.yaml 의 `tables:` 블록을 지우면 build_tables 는 아무것도 하지 않고,
tables_ready 는 None 을 돌려줍니다.

표가 있는 챗봇: 아래 TODO를 채우세요. 표는 "산문"이 아니므로 임베딩하지 않습니다. SQLite에 넣고,
queries.py 의 정해진 필터로만 조회합니다. 원본 프로젝트의 예: 두 줄 머리글을 합치고, "월 05 ,06 [E8-7-342]"
같은 수업시간 문자열을 요일·교시·강의실로 나눴습니다 (rag_chatbot_starter/src/ragbot/domain/tables.py).
"""
import sqlite3
from pathlib import Path

import pandas as pd

from ragbot.config import ROOT

TABLE = "items"   # TODO(05): SQLite 테이블 이름 (예: products, books, doctors)

# TODO(05): 원본 열 이름 → SQLite 열 이름 (영문 소문자, 밑줄). 비워 두면 원본 열을 모두 그대로 저장합니다.
# 예: {"상품코드": "code", "상품명": "name", "가격": "price"}
COLUMNS: dict[str, str] = {}


def file_path(cfg: dict) -> Path:
    return (ROOT / cfg["tables"]["file"]).resolve()


def db_path(cfg: dict) -> Path:
    return (ROOT / cfg["tables"]["db"]).resolve()


def read_table(path) -> pd.DataFrame:
    """파일 → 정리된 DataFrame. 데이터의 특이점은 여기서 처리하고 docs/DATA.md 에 적습니다."""
    path = Path(path)
    df = pd.read_csv(path, dtype=str) if path.suffix.lower() == ".csv" else pd.read_excel(path, dtype=str)
    if COLUMNS:
        missing = [k for k in COLUMNS if k not in df.columns]
        if missing:
            raise ValueError(f"Table file is missing columns {missing}. Found: {list(df.columns)}")
        df = df[list(COLUMNS)].rename(columns=COLUMNS)
    for col in df.columns:   # 앞뒤 공백 제거
        df[col] = df[col].str.strip()
    # TODO(05): 머리글이 두 줄인가? 숫자 열은 pd.to_numeric 으로, 빈 행은 제거, Y/N 은 1/0 으로 …
    return df.fillna("")


def build_tables(cfg: dict, progress=print) -> int:
    """도메인 hook: 표 파일 → SQLite. `python -m ragbot tables` (또는 build)가 호출합니다."""
    if not cfg.get("tables"):
        progress("  no tables in config.yaml, skipped")
        return 0
    df = read_table(file_path(cfg))
    with sqlite3.connect(db_path(cfg)) as con:
        df.to_sql(TABLE, con, if_exists="replace", index=False)
    progress(f"  {len(df)} rows → {db_path(cfg).name} (table {TABLE})")
    return len(df)


def tables_ready(cfg: dict) -> str | None:
    """도메인 hook: 표가 없거나 데이터베이스가 있으면 None, 아니면 실행할 명령."""
    if not cfg.get("tables"):
        return None
    return None if db_path(cfg).exists() else "Table database is missing. Run: python -m ragbot build"
