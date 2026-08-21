$Root = Split-Path -Parent $PSScriptRoot

. "$PSScriptRoot\common.ps1"

Require-Administrator

Write-SystemLog "Starting NetworkMonitor installation."

# --------------------------------
# Python
# --------------------------------

if (!(Test-CommandExists "python")) {

    Write-SystemLog `
        "Python is not installed." `
        "ERROR"

    exit 1
}

Write-SystemLog `
    "Python: $(python --version)"


# --------------------------------
# Node
# --------------------------------

if (!(Test-CommandExists "node")) {

    Write-SystemLog `
        "Node.js is not installed." `
        "ERROR"

    exit 1
}

Write-SystemLog `
    "Node.js: $(node --version)"


# --------------------------------
# NPM
# --------------------------------

if (!(Test-CommandExists "npm")) {

    Write-SystemLog `
        "NPM is not installed." `
        "ERROR"

    exit 1
}


# --------------------------------
# Python Virtual Environment
# --------------------------------

$VenvPython = Join-Path `
    $Root `
    "network-engine\.venv\Scripts\python.exe"


if (!(Test-Path $VenvPython)) {

    Write-SystemLog `
        "Creating Python virtual environment."

    Push-Location "$Root\network-engine"

    python -m venv .venv

    Pop-Location
}


# --------------------------------
# Python Dependencies
# --------------------------------

Write-SystemLog `
    "Installing Python dependencies."

Push-Location "$Root\network-engine"

& $VenvPython `
    -m pip install `
    -r requirements.txt

Pop-Location


# --------------------------------
# Dashboard
# --------------------------------

Write-SystemLog `
    "Installing dashboard dependencies."

Push-Location "$Root\dashboard"

npm install

Pop-Location


# --------------------------------
# Dashboard Build
# --------------------------------

Write-SystemLog `
    "Building dashboard."

Push-Location "$Root\dashboard"

npm run build

Pop-Location


# --------------------------------
# Directories
# --------------------------------

$Directories = @(
    "logs",
    "backups",
    "data",
    "config",
    "data\runtime"
)

foreach ($Directory in $Directories) {

    $Path = Join-Path $Root $Directory

    if (!(Test-Path $Path)) {

        New-Item `
            -ItemType Directory `
            -Path $Path `
            -Force | Out-Null
    }
}


Write-SystemLog `
    "Installation completed successfully."

Write-Host ""
Write-Host "===================================="
Write-Host " NetworkMonitor Installation Done"
Write-Host "===================================="
Write-Host ""
Write-Host "Run START.ps1 to start the system."