# Install or upgrade: this script sets up on first run, re-fetches on every
# run after that. Re-running it later IS the upgrade command.
#
#   irm https://raw.githubusercontent.com/onezoftserv/claude-code-portable-config/main/install.ps1 | iex
#
# Pin to a branch, tag, or FULL (not abbreviated) commit SHA instead of
# main (set before piping, since `iex` can't take arguments):
#   $env:CLAUDE_PORTABLE_CONFIG_REF = "v1.0.0"; irm .../install.ps1 | iex
$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/onezoftserv/claude-code-portable-config.git"
$Dest = if ($env:CLAUDE_PORTABLE_CONFIG_DIR) { $env:CLAUDE_PORTABLE_CONFIG_DIR } else { Join-Path $HOME ".claude-portable-config" }
$Ref = if ($env:CLAUDE_PORTABLE_CONFIG_REF) { $env:CLAUDE_PORTABLE_CONFIG_REF } else { "main" }

if (-not (Test-Path (Join-Path $Dest ".git"))) {
    Write-Host "Setting up $Dest"
    git init -q $Dest
    if ($LASTEXITCODE -ne 0) { throw "git init failed" }
    git -C $Dest remote add origin $RepoUrl
    if ($LASTEXITCODE -ne 0) { throw "git remote add failed" }
}

Write-Host "Fetching $Ref into $Dest"
git -C $Dest fetch --depth 1 origin $Ref
if ($LASTEXITCODE -ne 0) { throw "git fetch failed" }
git -C $Dest checkout --quiet --detach FETCH_HEAD
if ($LASTEXITCODE -ne 0) { throw "git checkout failed" }

$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) { $PythonCmd = Get-Command py -ErrorAction SilentlyContinue }
if (-not $PythonCmd) {
    throw "python (or py) not found on PATH — install Python first."
}

Write-Host "Running installer with $($PythonCmd.Source)"
& $PythonCmd.Source (Join-Path $Dest "scripts\install.py") @args
if ($LASTEXITCODE -ne 0) { throw "installer failed (exit $LASTEXITCODE)" }
