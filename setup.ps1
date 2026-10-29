# 한 번에 개발 환경 만들기 (Windows PowerShell):  powershell -ExecutionPolicy Bypass -File setup.ps1 [환경이름]
# conda 환경 생성 → 고정 버전 파이썬 패키지 → kordoc 엔진(npm ci) → .env → 단위 테스트.
# 여러 번 실행해도 안전합니다 (이미 있는 환경은 갱신, .env 는 덮어쓰지 않음).
param([string]$EnvName = "my_ragbot")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Step($cmd) {
    & $cmd
    if ($LASTEXITCODE -ne 0) { Write-Host "실패: 위의 오류를 확인하세요." -ForegroundColor Red; exit $LASTEXITCODE }
}

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "conda 를 찾을 수 없습니다. Miniforge 를 설치한 뒤 'Miniforge Prompt' 나 새 PowerShell 에서 다시 실행하세요:"
    Write-Host "  https://github.com/conda-forge/miniforge"
    exit 1
}
(& conda shell.powershell hook) | Out-String | Invoke-Expression

Write-Host "▶ 1/5 conda 환경 '$EnvName' (Python 3.11 + Node.js 20)"
$exists = (conda env list) -match "^$EnvName\s"
if ($exists) { Step { conda env update -n $EnvName -f environment.yml --prune } }
else { Step { conda env create -n $EnvName -f environment.yml } }
conda activate $EnvName

Write-Host "▶ 2/5 파이썬 패키지 (requirements.lock)"
Step { python -m pip install --upgrade pip }
Step { python -m pip install -r requirements.lock }
Step { python -m pip install -e ".[dev]" --no-deps }

Write-Host "▶ 3/5 kordoc 엔진 (package-lock.json)"
Step { npm ci }

Write-Host "▶ 4/5 .env"
if (Test-Path .env) { Write-Host "  .env 가 이미 있어 그대로 둡니다" }
else { Copy-Item .env.example .env; Write-Host "  .env 를 만들었습니다. LLM / 임베딩 주소와 키를 채우세요" }

Write-Host "▶ 5/5 단위 테스트"
Step { python -m ragbot check --fast }

Write-Host ""
Write-Host "✅ 완료. 새 터미널에서:  conda activate $EnvName"
Write-Host "   다음: .env 를 채우고 tasks/01_goal.md 부터 시작하세요."
