$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
uv sync --frozen
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
npm ci
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
npm run model:download
exit $LASTEXITCODE
