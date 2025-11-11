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
  [string]$Host = 'github.com',
  [string]$DefaultRepoOwner = 'vpsmoju',
  [string]$DefaultRepoName = 'docfinance'
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
  
  # Validação opcional: identidade e acesso ao repositório
  if ($Global:DoValidate) {
    try {
      $headers = @{ Authorization = "token $plain"; 'User-Agent' = 'PAT-Validator' }
      $me = Invoke-RestMethod -Method GET -Uri 'https://api.github.com/user' -Headers $headers -ErrorAction Stop
      Write-Host ("Usuário do token: {0}" -f $me.login) -ForegroundColor Green
    } catch {
      Write-Host "Falha ao consultar /user com esse PAT." -ForegroundColor Yellow
    }
    if ($Global:RepoOwner -and $Global:RepoName) {
      try {
        $repoUri = "https://api.github.com/repos/$($Global:RepoOwner)/$($Global:RepoName)"
        $resp = Invoke-WebRequest -Method GET -Uri $repoUri -Headers $headers -ErrorAction SilentlyContinue
        $status = $resp.StatusCode
        Write-Host "Acesso a $($Global:RepoOwner)/$($Global:RepoName): HTTP $status" -ForegroundColor Cyan
        if ($status -eq 200) {
          Write-Host "OK: o PAT tem acesso ao repositório." -ForegroundColor Green
        } else {
          Write-Host "Aviso: acesso não validado (HTTP $status)." -ForegroundColor Yellow
        }
      } catch {
        Write-Host "Falha ao consultar o repositório alvo." -ForegroundColor Yellow
      }
    }
  }
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

# Pergunta se deve validar acesso ao repositório alvo
$validateInput = Read-Host "Deseja validar acesso via API ao repositório alvo? (s/N)"
if ($validateInput -match '^(s|S|y|Y)') {
  $Global:DoValidate = $true
  $owner = Read-Host "Owner do repositório (Enter para '$DefaultRepoOwner')"
  $name = Read-Host "Nome do repositório (Enter para '$DefaultRepoName')"
  if ([string]::IsNullOrWhiteSpace($owner)) { $owner = $DefaultRepoOwner }
  if ([string]::IsNullOrWhiteSpace($name)) { $name = $DefaultRepoName }
  $Global:RepoOwner = $owner
  $Global:RepoName = $name
  Write-Host "Validação configurada para $owner/$name. Re-execute o script para validar com cada usuário, se necessário." -ForegroundColor Cyan
}

Write-Host "Concluído. Faça um 'git push' para validar que não há novos prompts." -ForegroundColor Cyan
