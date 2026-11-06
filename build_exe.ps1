# Rebuild dist\GlythMinis\ (folder build: GlythMinis.exe + _internal).
#
# One-file (--onefile) builds extract the bundled DLLs into %TEMP% at every
# start, which antivirus / ASR policies on some machines block with an empty
# "Error" dialog.  A folder build needs no extraction, so it just works.
param(
    [string]$Python = "$PSScriptRoot\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path $Python)) {
    $Python = "python"
}

$icon = (Resolve-Path "res\glythminis.ico").Path

& $Python -m PyInstaller --noconfirm --onedir --noconsole --clean `
    --name GlythMinis --icon "$icon" `
    --distpath dist --workpath build --specpath build main.py

Write-Host ""
Write-Host "Built: $PSScriptRoot\dist\GlythMinis\GlythMinis.exe"
