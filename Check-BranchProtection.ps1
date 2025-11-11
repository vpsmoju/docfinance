param(
  [Parameter(Mandatory=$true)] [string]$Owner,   # ex.: 'kinhomoju'
  [Parameter(Mandatory=$true)] [string]$Repo,    # ex.: 'docfinance_copia'
  [Parameter(Mandatory=$true)] [string]$Branch,  # ex.: 'main'
  [string]$Token
)

$ErrorActionPreference = 'Stop'

function Read-TokenSecure {
  $sec = Read-Host -AsSecureString "Informe o token (PAT) com acesso ao repo $Owner/$Repo"
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
  try { return [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

if (-not $Token) { $Token = Read-TokenSecure }
if ([string]::IsNullOrWhiteSpace($Token)) { throw "Token não informado." }

$headers = @{ Authorization = "token $Token"; 'User-Agent' = 'PS-BranchProtection'; 'Accept' = 'application/vnd.github+json' }
$url = "https://api.github.com/repos/$Owner/$Repo/branches/$Branch/protection"

try {
  $resp = Invoke-RestMethod -Method Get -Uri $url -Headers $headers
} catch {
  if ($_.Exception.Response -and $_.Exception.Response.StatusCode.Value__ -eq 404) {
    Write-Host "Branch '$Branch' não possui proteção configurada." -ForegroundColor Yellow
    exit 0
  }
  throw $_
}

function BoolStr($b) { if ($b) { 'true' } else { 'false' } }

$linear = $resp.required_linear_history.enabled
$force = $resp.allow_force_pushes.enabled
$deletions = $resp.allow_deletions.enabled
$strict = $false
if ($resp.required_status_checks) { $strict = $resp.required_status_checks.strict }

Write-Host "Resumo de proteções para $Owner/$Repo ($Branch):" -ForegroundColor Cyan
Write-Host ("  required_linear_history: {0}" -f (BoolStr $linear))
Write-Host ("  allow_force_pushes    : {0}" -f (BoolStr $force))
Write-Host ("  allow_deletions       : {0}" -f (BoolStr $deletions))
Write-Host ("  status_checks.strict  : {0}" -f (BoolStr $strict))

Write-Host "Recomendações:" -ForegroundColor Cyan
if (-not $force) {
  Write-Host "  Para 'git push --mirror', habilite 'Allow force pushes' temporariamente." -ForegroundColor Yellow
}
if ($linear) {
  Write-Host "  'Require linear history' impede force-push; desative se for espelhar inteira." -ForegroundColor Yellow
}
if (-not $linear -and $force) {
  Write-Host "  Configuração compatível com espelho completo." -ForegroundColor Green
}
Write-Host "  Alternativa: sincronizar apenas 'main' sem forçar (modo main do script)." -ForegroundColor Yellow

