# Builds TinyIDE.exe + TinyIDE-Setup.exe and copies them to Desktop\compiler
Set-Location $PSScriptRoot

Write-Host "[1/5] Installing PyInstaller..." -ForegroundColor Cyan
python -m pip install --quiet pyinstaller

Write-Host "[2/5] Creating the icon..." -ForegroundColor Cyan
python make_ico.py

Write-Host "[3/5] Building TinyIDE.exe (takes 1-2 minutes)..." -ForegroundColor Cyan
python -m PyInstaller --noconfirm --clean --onefile --windowed --name TinyIDE --icon assets\tiny.ico gui.py
if (-not (Test-Path "dist\TinyIDE.exe")) { Write-Host "Build failed - send me the red error above." -ForegroundColor Red; return }

function Find-Iscc {
    Get-ChildItem "C:\Program Files (x86)", "C:\Program Files", "$env:LOCALAPPDATA\Programs" -Recurse -Depth 2 -Filter ISCC.exe -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
}

Write-Host "[4/5] Making the installer (Setup.exe)..." -ForegroundColor Cyan
$iscc = Find-Iscc
if (-not $iscc -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    winget install -e --id JRSoftware.InnoSetup --accept-source-agreements --accept-package-agreements
    $iscc = Find-Iscc
}
if ($iscc) {
    & $iscc installer.iss
} else {
    Write-Host "Inno Setup could not be installed automatically. Install it from https://jrsoftware.org/isdl.php then run this script again." -ForegroundColor Yellow
}

Write-Host "[5/5] Copying to Desktop\compiler..." -ForegroundColor Cyan
$d = [Environment]::GetFolderPath('Desktop')
New-Item -ItemType Directory -Force -Path "$d\compiler" | Out-Null
Copy-Item "dist\TinyIDE.exe" "$d\compiler\TinyIDE.exe" -Force
if (Test-Path "installer_output\TinyIDE-Setup.exe") { Copy-Item "installer_output\TinyIDE-Setup.exe" "$d\compiler\TinyIDE-Setup.exe" -Force }
Copy-Item examples "$d\compiler\examples" -Recurse -Force
explorer "$d\compiler"
Write-Host "DONE. Your files are in Desktop\compiler" -ForegroundColor Green