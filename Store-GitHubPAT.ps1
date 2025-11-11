<#
  Armazena PAT do GitHub com segurança no Windows Credential Manager para o host
  `github.com`, evitando prompts de login em pushes (inclui push duplo).

  Como usar:
    - Execute no PowerShell:  .\Store-GitHubPAT.ps1
    - Escolha opcionalmente limpar credenciais antigas.
    - Informe o(s) usuário(s) e cole o PAT quando solicitado (entrada segura).

  Observações:
    - Não imprime o PAT em logs. Variáveis são limpas ao final.
    - Suporta armazenar PAT para múltiplos usuários (ex.: vpsmoju, kinhomoju).
#>

param(
  [string]$Host = 'github.com'
)

Write-Host "GitHub PAT storage helper (host: $Host)" -ForegroundColor Cyan

# Verifica dependência do Git Credential Manager
$gcm = git credential-manager version 2>$null
if (-not $?) {
  Write-Host "Git Credential Manager não encontrado. Instale-o antes de continuar:" -ForegroundColor Yellow
  Write-Host "https://github.com/GitCredentialManager/git-credential-manager/releases"
  exit 1
}

# Opcional: limpar credenciais/resíduos anteriores
$doClear = Read-Host "Deseja limpar credenciais anteriores para $Host? (s/N)"
if ($doClear -match '^(s|S|y|Y)') {
  Write-Host "Limpando credenciais e headers…" -ForegroundColor Yellow
  try { git config --global --unset-all "http.https://$Host/.extraheader" 2>$null } catch {}
  try {
    $erase = "protocol=https`nhost=$Host"
    $erase | git credential-manager erase | Out-Null
  } catch {}
  Write-Host "Limpeza concluída." -ForegroundColor Green
}

function Store-PAT([string]$Username) {
  if ([string]::IsNullOrWhiteSpace($Username)) { return }
  Write-Host "Armazenando PAT para usuário '$Username' em $Host…" -ForegroundColor Cyan
  $pat = Read-Host "Cole o PAT de $Username" -AsSecureString
  $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($pat)
  )
  if ([string]::IsNullOrWhiteSpace($plain)) {
    Write-Host "PAT vazio; ignorado." -ForegroundColor Yellow
    return
  }
  $cred = "protocol=https`nhost=$Host`nusername=$Username`npassword=$plain`n"
  $cred | git credential-manager store | Out-Null
  Write-Host "Credencial para '$Username' armazenada com sucesso." -ForegroundColor Green
  # Limpa variáveis sensíveis
  Clear-Variable pat, plain, cred -ErrorAction SilentlyContinue
}

# Entrada dos usuários a armazenar
$usersInput = Read-Host "Informe os usuários (separados por vírgula), ex.: vpsmoju,kinhomoju"
$users = @()
if (-not [string]::IsNullOrWhiteSpace($usersInput)) {
  $users = $usersInput.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
}
if ($users.Count -eq 0) {
  $fallback = Read-Host "Nenhum usuário informado. Deseja usar 'vpsmoju'? (s/N)"
  if ($fallback -match '^(s|S|y|Y)') { $users = @('vpsmoju') }
}

foreach ($u in $users) { Store-PAT -Username $u }

Write-Host "Concluído. Faça um 'git push' para validar que não há novos prompts." -ForegroundColor Cyan

