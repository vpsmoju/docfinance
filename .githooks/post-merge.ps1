$ErrorActionPreference = 'Stop'

docker compose up -d postgres

$dbUrl = $env:DATABASE_URL
if (-not $dbUrl -or $dbUrl.Trim() -eq '') {
  $env:DATABASE_URL = "postgresql://docfinance:docfinance@localhost:5432/docfinance"
}

python manage.py migrate
