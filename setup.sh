#!/usr/bin/env bash
# 한 번에 개발 환경 만들기 (macOS / Linux):  bash setup.sh [환경이름]
# conda 환경 생성 → 고정 버전 파이썬 패키지 → kordoc 엔진(npm ci) → .env → 단위 테스트.
# 여러 번 실행해도 안전합니다 (이미 있는 환경은 갱신, .env 는 덮어쓰지 않음).
set -euo pipefail
cd "$(dirname "$0")"
ENV_NAME="${1:-my_ragbot}"

if ! command -v conda >/dev/null 2>&1; then
  echo "conda 를 찾을 수 없습니다. Miniforge 를 설치한 뒤 새 터미널에서 다시 실행하세요:"
  echo "  https://github.com/conda-forge/miniforge"
  exit 1
fi
eval "$(conda shell.bash hook)"

echo "▶ 1/5 conda 환경 '$ENV_NAME' (Python 3.11 + Node.js 20)"
if conda env list | grep -qE "^${ENV_NAME}[[:space:]]"; then
  conda env update -n "$ENV_NAME" -f environment.yml --prune
else
  conda env create -n "$ENV_NAME" -f environment.yml
fi
conda activate "$ENV_NAME"

echo "▶ 2/5 파이썬 패키지 (requirements.lock)"
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install -e ".[dev]" --no-deps

echo "▶ 3/5 kordoc 엔진 (package-lock.json)"
npm ci

echo "▶ 4/5 .env"
if [ -f .env ]; then
  echo "  .env 가 이미 있어 그대로 둡니다"
else
  cp .env.example .env
  echo "  .env 를 만들었습니다. LLM / 임베딩 주소와 키를 채우세요"
fi

echo "▶ 5/5 단위 테스트"
python -m ragbot check --fast

echo
echo "✅ 완료. 새 터미널에서:  conda activate $ENV_NAME"
echo "   다음: .env 를 채우고 tasks/01_goal.md 부터 시작하세요."
