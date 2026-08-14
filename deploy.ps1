# Deploy INSTAR to Cloudflare Pages (instar.jonbailey.xyz)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Project = "instar-jonbailey"
$Og = Join-Path $Root "public\og.jpg"

if (-not (Test-Path $Og)) {
  Write-Error "Missing public/og.jpg. Run: py -3 scripts/build_payloads.py"
}

Write-Host "[DEPLOY] Pages deploy project=$Project" -ForegroundColor Cyan
Push-Location $Root
try {
  npx --yes wrangler pages deploy public --project-name=$Project --branch=main --commit-dirty=true
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
  Pop-Location
}

Write-Host ""
Write-Host "Site:    https://instar.jonbailey.xyz/"
Write-Host "Preview: https://$Project.pages.dev/"
