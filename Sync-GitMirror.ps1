<# 
.SYNOPSIS
  Sincroniza de um repositório origem para um destino no GitHub.

.DESCRIPTION
  - Mode 'mirror': deixa o destino idêntico à origem (branches, tags e refs). Requer force-push.
  - Mode 'main'  : envia apenas a branch 'main' (opcionalmente força; pode enviar tags).

.PARAMETERS
  -Mode         : 'mirror' (espelhar tudo) ou 'main' (apenas branch main). Padrão: 'main'
  -Source       : URL HTTPS do repo de origem. Padrão: https://github.com/vpsmoju/docfinance.git
  -Dest         : dono/repositorio do destino (ex.: kinhomoju/docfinance_copia)
  -Token        : PAT com escrita no destino. Se não informado, será solicitado com segurança.
  -Force        : (Mode=main) usa --force-with-lease ao enviar a main.
  -IncludeTags  : (Mode=main) envia tags após a main.
  -KeepTemp     : mantém pasta temporária criada para debug.

.EXAMPLES
  # Espelhar tudo (branches+tags) para o destino
  .\Sync-GitMirror.ps1 -Mode mirror -Dest kinhomoju/docfinance_copia -Token 'SEU_TOKEN'

  # Enviar somente a main (sem forçar) e sem tags
  .\Sync-GitMirror.ps1 -Mode main -Dest kinhomoju/docfinance_copia -Token 'SEU_TOKEN'

  # Enviar somente a main, forçando, e enviar tags
  .\Sync-GitMirror.ps1 -Mode main -Dest kinhomoju/docfinance_copia -Force -IncludeTags -Token 'SEU_TOKEN'
#>

param(
  [ValidateSet('mirror','main')]
  [string]$Mode = 'main',

  [string]$Source = 'https://github.com/vpsmoju/docfinance.git',

  [Parameter(Mandatory=$true)]
  [string]$Dest, # formato: owner/repo (ex.: kinhomoju/docfinance_copia)

  [string]$Token,

  [switch]$Force,
  [switch]$IncludeTags,
  [switch]$KeepTemp
)

$ErrorActionPreference = 'Stop'

function Assert-Tool {
  param([string]$Tool)
  $exists = (Get-Command $Tool -ErrorAction SilentlyContinue) -ne $null
  if (-not $exists) { throw "Ferramenta obrigatória não encontrada: $Tool" }
}

function Read-TokenSecure {
  $sec = Read-Host -AsSecureString "Informe o token de acesso (PAT) da conta do destino ($Dest)"
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
  try {
    return [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
  } finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
}

function Run-Git {
  param([string]$Cmd, [string]$WorkDir = $null)
  if ($WorkDir) {
    Push-Location $WorkDir
    try {
      Write-Host ">> $Cmd" -ForegroundColor Cyan
      cmd /c $Cmd
      if ($LASTEXITCODE -ne 0) { throw "Comando falhou com código ${LASTEXITCODE}: $Cmd" }
    } finally {
      Pop-Location
    }
  } else {
    Write-Host ">> $Cmd" -ForegroundColor Cyan
    cmd /c $Cmd
    if ($LASTEXITCODE -ne 0) { throw "Comando falhou com código ${LASTEXITCODE}: $Cmd" }
  }
}

try {
  Assert-Tool git

  if (-not $Token) {
    $Token = Read-TokenSecure
  }

  if ([string]::IsNullOrWhiteSpace($Token)) {
    throw "Token não informado. Gere um PAT na conta do destino com permissão de escrita (Contents: Read and write)."
  }

  $ts = Get-Date -Format 'yyyyMMdd-HHmmss'
  $tempRoot = Join-Path $env:TEMP "git-sync-$ts"
  New-Item -ItemType Directory -Path $tempRoot | Out-Null

  $destUrl = "https://x-access-token:$Token@github.com/$Dest.git"

  if ($Mode -eq 'mirror') {
    $repoDir = Join-Path $tempRoot "source.git"
    Write-Host "Clonando origem em modo espelho..." -ForegroundColor Yellow
    Run-Git "git clone --mirror `"$Source`" `"$repoDir`""

    Write-Host "Configurando URL de push para o destino..." -ForegroundColor Yellow
    Run-Git "git remote set-url --push origin `"$destUrl`"" $repoDir

    Write-Host "Enviando espelho completo para o destino..." -ForegroundColor Yellow
    Run-Git "git push --mirror" $repoDir

    Write-Host "Sincronização (mirror) concluída com sucesso." -ForegroundColor Green
  }
  else {
    $repoDir = Join-Path $tempRoot "source"
    Write-Host "Clonando somente a branch 'main'..." -ForegroundColor Yellow
    Run-Git "git clone --no-tags --single-branch -b main `"$Source`" `"$repoDir`""

    Write-Host "Adicionando remoto 'mirror' do destino..." -ForegroundColor Yellow
    Run-Git "git remote add mirror `"$destUrl`"" $repoDir

    $forceFlag = if ($Force) { "--force-with-lease" } else { "" }
    Write-Host "Enviando branch 'main' para o destino..." -ForegroundColor Yellow
    Run-Git "git push $forceFlag mirror main:main" $repoDir

    if ($IncludeTags.IsPresent) {
      Write-Host "Buscando e enviando tags..." -ForegroundColor Yellow
      Run-Git "git fetch --tags" $repoDir
      Run-Git "git push mirror --tags" $repoDir
    }

    Write-Host "Sincronização (main) concluída com sucesso." -ForegroundColor Green
  }

  if (-not $KeepTemp) {
    Remove-Item -Recurse -Force $tempRoot
  } else {
    Write-Host "Diretório temporário mantido: $tempRoot" -ForegroundColor DarkYellow
  }
}
catch {
  Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}
