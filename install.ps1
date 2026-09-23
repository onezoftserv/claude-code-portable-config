# Install or upgrade: this script clones on first run, `git pull`s on every
# run after that. Re-running it later IS the upgrade command.
#
#   irm https://raw.githubusercontent.com/onezoftserv/claude-code-portable-config/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/onezoftserv/claude-code-portable-config.git"
$Dest = if ($env:CLAUDE_PORTABLE_CONFIG_DIR) { $env:CLAUDE_PORTABLE_CONFIG_DIR } else { Join-Path $HOME ".claude-portable-config" }

if (Test-Path (Join-Path $Dest ".git")) {
    Write-Host "Updating existing clone at $Dest"
    git -C $Dest pull --ff-only
} else {
    Write-Host "Cloning into $Dest"
    git clone --depth 1 $RepoUrl $Dest
}

$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) { $PythonCmd = Get-Command py -ErrorAction SilentlyContinue }
if (-not $PythonCmd) {
    Write-Error "python (or py) not found on PATH — install Python first."
    exit 1
}

Write-Host "Running installer with $($PythonCmd.Source)"
& $PythonCmd.Source (Join-Path $Dest "scripts\install.py") @args
