# Deploy INSTAR to Cloudflare Pages (instar.jonbailey.xyz)
# Runs the public-safe shed check first. No secrets. Not a decipherment.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Project = "instar-jonbailey"
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

  $tokFile = Join-Path $env:USERPROFILE ".grok\secrets\cloudflare_full_token.txt"
  if (-not (Test-Path $tokFile)) {
    $tokFile = Join-Path $env:USERPROFILE ".cloudflare\api-token-agent-full.txt"
  }
  if (Test-Path $tokFile) {
    $tok = (Get-Content -Raw $tokFile).Trim()
    $zid = "5edf60c2008504386dd2d572415c8fb0"
    try {
      $purge = Invoke-RestMethod -Method POST -Uri "https://api.cloudflare.com/client/v4/zones/$zid/purge_cache" -Headers @{ Authorization = "Bearer $tok" } -ContentType "application/json" -Body '{"hosts":["instar.jonbailey.xyz"]}'
      if ($purge.success) {
        Write-Host "[DEPLOY] Purged instar.jonbailey.xyz cache"
      } else {
        Write-Host "[DEPLOY] Cache purge did not succeed (deploy still live on Pages)"
      }
    } catch {
      Write-Host "[DEPLOY] Cache purge skipped"
    }
  }
} finally {
  Pop-Location
}

Write-Host ""
Write-Host "Site:    https://instar.jonbailey.xyz/"
Write-Host "Preview: https://$Project.pages.dev/"
