param(
  [string]$Version = "0.1.1",
  [string]$ArtifactName = "MisikkkiBot-0.1.1-win-x64"
)

$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
  throw "Windows packaging must be run on Windows so the PyInstaller output contains Windows executables."
}

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$DistDir = Join-Path $RepoRoot "dist"
$BundleDir = Join-Path $DistDir $ArtifactName
$ZipPath = Join-Path $DistDir "$ArtifactName.zip"
$ChecksumPath = Join-Path $DistDir "SHA256SUMS.txt"

Set-Location $RepoRoot

uv sync --group dev
uv run pytest
uv run python -m compileall apps packages tests
uv build
uv run pyinstaller --clean --noconfirm packaging\windows\MisikkkiBot.spec

Copy-Item -Path LICENSE -Destination (Join-Path $BundleDir "LICENSE") -Force
Copy-Item -Path NOTICE -Destination (Join-Path $BundleDir "NOTICE") -Force
Copy-Item -Path README.md -Destination (Join-Path $BundleDir "README.md") -Force
Copy-Item -Path packaging\windows\FIRST_RUN.txt -Destination (Join-Path $BundleDir "FIRST_RUN.txt") -Force

if (Test-Path $ZipPath) {
  Remove-Item -LiteralPath $ZipPath -Force
}

Compress-Archive -Path (Join-Path $BundleDir "*") -DestinationPath $ZipPath -CompressionLevel Optimal

$Artifacts = @(
  $ZipPath,
  (Join-Path $DistDir "misikkkibot_oss-$Version-py3-none-any.whl"),
  (Join-Path $DistDir "misikkkibot_oss-$Version.tar.gz")
)

$Lines = foreach ($Artifact in $Artifacts) {
  $Hash = Get-FileHash -Algorithm SHA256 -Path $Artifact
  "$($Hash.Hash.ToLowerInvariant())  $(Split-Path -Leaf $Artifact)"
}

$Lines | Set-Content -Path $ChecksumPath -Encoding ascii
Write-Host "Created $ZipPath"
Write-Host "Created $ChecksumPath"
