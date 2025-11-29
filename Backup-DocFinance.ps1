$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$stamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$backupsDir = Join-Path $PSScriptRoot 'backups'
New-Item -ItemType Directory -Force $backupsDir | Out-Null

$dumpIn = "/tmp/docfinance_${stamp}.dump"
$sqlIn = "/tmp/docfinance_${stamp}.sql"
$dumpOut = Join-Path $backupsDir "docfinance_${stamp}.dump"
$sqlOut = Join-Path $backupsDir "docfinance_${stamp}.sql"
$fixtureOut = Join-Path $backupsDir "backup_fixture_${stamp}.json"

docker exec docfinance-postgres sh -lc "pg_dump -U docfinance -d docfinance -Fc -Z 9 -f $dumpIn && pg_dump -U docfinance -d docfinance -f $sqlIn"
docker cp docfinance-postgres:$dumpIn $dumpOut
docker cp docfinance-postgres:$sqlIn $sqlOut

$env:DATABASE_URL = 'postgresql://docfinance:docfinance@localhost:5432/docfinance'
$pyPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$python = if (Test-Path $pyPath) { $pyPath } else { 'python' }
& $python manage.py dumpdata --natural-foreign --natural-primary --indent 2 --output $fixtureOut

$t = Get-Content $fixtureOut -Encoding Default -Raw
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($fixtureOut, $t, $utf8NoBom)

$keep = 3
Get-ChildItem $backupsDir -Filter 'docfinance_*.dump' | Sort-Object LastWriteTime -Descending | Select-Object -Skip $keep | Remove-Item -Force
Get-ChildItem $backupsDir -Filter 'docfinance_*.sql' | Sort-Object LastWriteTime -Descending | Select-Object -Skip $keep | Remove-Item -Force
Get-ChildItem $backupsDir -Filter 'backup_fixture_*.json' | Sort-Object LastWriteTime -Descending | Select-Object -Skip $keep | Remove-Item -Force
