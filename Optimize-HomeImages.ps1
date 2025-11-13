<#
Optimiza imagens para o slideshow da tela de login
 - Converte PNG/JPG grandes para JPG com qualidade controlada
 - Redimensiona mantendo proporção (largura máxima padrão: 1920)
 - Salva em static/img/home/optimized mantendo o nome-base e extensão .jpg

Uso:
  powershell -ExecutionPolicy Bypass -File .\Optimize-HomeImages.ps1 -SourceDir "static/img/home" -TargetDir "static/img/home/optimized" -MaxWidth 1920 -Quality 82

Parâmetros:
  -SourceDir  Diretório de origem das imagens
  -TargetDir  Diretório de destino para imagens otimizadas
  -MaxWidth   Largura máxima (default 1920)
  -Quality    Qualidade JPEG (default 82)
  -Overwrite  Sobrescreve arquivos existentes no destino
#>
param(
  [string]$SourceDir = "static/img/home",
  [string]$TargetDir = "static/img/home/optimized",
  [int]$MaxWidth = 1920,
  [int]$Quality = 82,
  [switch]$Overwrite
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (!(Test-Path -Path $SourceDir -PathType Container)) {
  throw "Diretório de origem não encontrado: $SourceDir"
}
if (!(Test-Path -Path $TargetDir -PathType Container)) {
  New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
}

# Carregar System.Drawing
Add-Type -AssemblyName System.Drawing

function Save-Jpeg([System.Drawing.Bitmap]$bitmap, [string]$outPath, [int]$quality) {
  $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
  $encParams = New-Object System.Drawing.Imaging.EncoderParameters(1)
  $encParams.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [int]$quality)
  $bitmap.Save($outPath, $codec, $encParams)
}

function Optimize-ImageFile([string]$inPath, [string]$outPath, [int]$maxWidth, [int]$quality) {
  $img = [System.Drawing.Image]::FromFile($inPath)
  try {
    $origW = [int]$img.Width
    $origH = [int]$img.Height
    $newW = $origW
    $newH = $origH
    if ($origW -gt $maxWidth) {
      $ratio = $origH / [double]$origW
      $newW = $maxWidth
      $newH = [int][Math]::Round($newW * $ratio)
    }
    $bmp = New-Object System.Drawing.Bitmap($newW, $newH)
    try {
      $g = [System.Drawing.Graphics]::FromImage($bmp)
      try {
        $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
        $g.InterpolationMode  = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $g.SmoothingMode      = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
        $g.DrawImage($img, 0, 0, $newW, $newH)
      } finally { $g.Dispose() }
      Save-Jpeg -bitmap $bmp -outPath $outPath -quality $quality
    } finally { $bmp.Dispose() }
  } finally { $img.Dispose() }
}

$supported = @('*.png','*.jpg','*.jpeg','*.JPG','*.JPEG','*.PNG')
$files = foreach ($pat in $supported) { Get-ChildItem -Path $SourceDir -Filter $pat -File }
if (!$files -or $files.Count -eq 0) {
  Write-Host "Nenhum arquivo suportado encontrado em $SourceDir" -ForegroundColor Yellow
  exit 0
}

Write-Host "Otimizando imagens de '$SourceDir' para '$TargetDir' (MaxWidth=$MaxWidth, Quality=$Quality)" -ForegroundColor Cyan

$processed = 0
foreach ($f in $files) {
  $baseName = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
  $destName = "$baseName.jpg"  # força .jpg
  $destPath = Join-Path $TargetDir $destName

  if ((Test-Path $destPath) -and -not $Overwrite) {
    Write-Host "Skip (existe): $destName" -ForegroundColor DarkYellow
    continue
  }
  try {
    Optimize-ImageFile -inPath $f.FullName -outPath $destPath -maxWidth $MaxWidth -quality $Quality
    $origSize = (Get-Item $f.FullName).Length
    $newSize  = (Get-Item $destPath).Length
    Write-Host ("OK: {0} -> {1} ({2:N1} MB -> {3:N1} MB)" -f $f.Name, $destName, ($origSize/1MB), ($newSize/1MB))
    $processed++
  } catch {
    Write-Warning "Falha ao otimizar '$($f.Name)': $($_.Exception.Message)"
  }
}

Write-Host "Concluído. Processados: $processed arquivos." -ForegroundColor Green
