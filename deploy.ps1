# Deploy INSTAR to Cloudflare Pages (instar.jonbailey.xyz)
# Runs the public-safe shed check first. No secrets. Not a decipherment.
# Uses CLOUDFLARE_API_TOKEN from the environment.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Project = if ($env:INSTAR_PAGES_PROJECT) { $env:INSTAR_PAGES_PROJECT } else { "instar-jonbailey" }
$Og = Join-Path $Root "public\og.jpg"
$Shed = Join-Path $Root "scripts\shed_check.py"

if (-not (Test-Path $Og)) {
  Write-Error "Missing public/og.jpg. Run: py -3 scripts/build_payloads.py"
}
if (-not (Test-Path $Shed)) {
  Write-Error "Missing scripts/shed_check.py"
}

Write-Host "[DEPLOY] Shed check (no secrets)" -ForegroundColor Cyan
Push-Location $Root
try {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 $Shed
  } elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    python3 $Shed
  } else {
    Write-Error "py -3 (or python3) required for shed_check before deploy"
  }
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

  Write-Host "[DEPLOY] Pages deploy project=$Project" -ForegroundColor Cyan
  npx --yes wrangler pages deploy public --project-name=$Project --branch=main --commit-dirty=true
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
  Pop-Location
}

Write-Host ""
Write-Host "Site:    https://instar.jonbailey.xyz/"
Write-Host "Preview: https://$Project.pages.dev/"
