# 00 — 환경 설정

**상태:** 진행 전

## 목표
템플릿이 내 컴퓨터에서 돌아가고, LLM·임베딩 서버에 연결된다.

## 파일
- `.env` (`.env.example` 을 복사. 커밋하지 않음)

## 완료 조건
- [ ] conda(Miniforge) 설치 후 `bash setup.sh` (Windows: `setup.ps1`) 가 ✅ 완료로 끝났다
- [ ] `.env` 에 LLM / 임베딩 / 재순위화 주소와 키 입력
- [ ] `python -m ragbot check --fast` 통과 (데이터가 없어도 통과해야 정상; `test_domain.py` 는 skip)
- [ ] 코딩 에이전트(Claude Code, Codex, Cursor 중 하나)를 이 폴더에서 열고, AGENTS.md 를 읽었는지 확인

## 확인
```
python -m ragbot check --fast
```
