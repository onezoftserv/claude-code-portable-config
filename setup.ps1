<#
.SYNOPSIS
  Set up the workshop on Windows: tools, Python packages, libraries, self-test.

.DESCRIPTION
  Safe to rerun. Installs with winget only what is missing.
  Does not touch the printer or the laser, and stores no credentials.

.EXAMPLE
  .\setup.ps1
  .\setup.ps1 -AllLibs -WithBambuStudio
  .\setup.ps1 -SkipInstall
#>
[CmdletBinding()]
param(
    [switch]$SkipInstall,      # do not install anything with winget
    [switch]$WithBambuStudio,  # also install Bambu Studio
    [switch]$AllLibs           # fetch optional libraries too
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
Set-Location $Root
$problems = New-Object System.Collections.Generic.List[string]

function Step($text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Note($text) { Write-Host "   $text" }
function Problem($text) { Write-Host "   ! $text" -ForegroundColor Yellow; $problems.Add($text) }

function Update-SessionPath {
    # pick up PATH changes made by installers without reopening the terminal
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Find-Tool([string[]]$Names, [string[]]$Paths) {
    foreach ($n in $Names) {
        $cmd = Get-Command $n -ErrorAction SilentlyContinue
        # the Microsoft Store 'python' stub lives in WindowsApps and is not a real install
        if ($cmd -and $cmd.Source -notmatch '\\WindowsApps\\') { return $cmd.Source }
    }
    foreach ($p in $Paths) {
        if ($p -and (Test-Path $p)) { return $p }
    }
    return $null
}

function Install-WithWinget([string]$Id, [string]$Label) {
    if ($SkipInstall) { Problem "$Label is missing (skipped: -SkipInstall)"; return }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Problem "$Label is missing and winget is not available; install it by hand"
        return
    }
    Note "installing $Label ($Id)"
    winget install --id $Id --exact --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { Problem "winget could not install $Label (id $Id, exit $LASTEXITCODE)" }
    Update-SessionPath
}

# ---- tools ------------------------------------------------------------------
Step 'Tools'

$pf = $env:ProgramFiles
$tools = @(
    @{ Label = 'Git';      Id = 'Git.Git';            Names = @('git');
       Paths = @("$pf\Git\cmd\git.exe") },
    @{ Label = 'Python';   Id = 'Python.Python.3.12'; Names = @('py', 'python');
       Paths = @("$env:LOCALAPPDATA\Programs\Python\Python312\python.exe") },
    @{ Label = 'OpenSCAD'; Id = 'OpenSCAD.OpenSCAD';  Names = @('openscad');
       Paths = @("$pf\OpenSCAD\openscad.com", "$pf\OpenSCAD\openscad.exe") },
    @{ Label = 'Inkscape'; Id = 'Inkscape.Inkscape';  Names = @('inkscape');
       Paths = @("$pf\Inkscape\bin\inkscape.exe") }
)
if ($WithBambuStudio) {
    $tools += @{ Label = 'Bambu Studio'; Id = 'Bambulab.Bambustudio'; Names = @('bambu-studio');
                 Paths = @("$pf\Bambu Studio\bambu-studio.exe") }
}

$found = @{}
foreach ($t in $tools) {
    $path = Find-Tool $t.Names $t.Paths
    if (-not $path) {
        Install-WithWinget $t.Id $t.Label
        $path = Find-Tool $t.Names $t.Paths
    }
    if ($path) { Note "$($t.Label): $path"; $found[$t.Label] = $path }
    elseif (-not ($problems -match [regex]::Escape($t.Label))) { Problem "$($t.Label) not found after install; open a new terminal and rerun" }
}

if (-not $WithBambuStudio) {
    $bambu = Find-Tool @('bambu-studio') @("$pf\Bambu Studio\bambu-studio.exe")
    if ($bambu) { Note "Bambu Studio: $bambu" }
    else { Note 'Bambu Studio: not found (rerun with -WithBambuStudio, or get it from bambulab.com/download)' }
}
Note 'xTool Studio: manual install from xtool.com (not available through winget)'

# OpenSCAD is not always on PATH; tell build_part.py where it is for this run
if ($found['OpenSCAD']) { $env:OPENSCAD = $found['OpenSCAD'] }

# ---- python -----------------------------------------------------------------
Step 'Python environment'

$venvPython = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    if (-not $found['Python']) {
        Problem 'Python is missing, so the rest of the setup cannot run'
    } else {
        $launcher = $found['Python']
        if ((Split-Path $launcher -Leaf) -ieq 'py.exe') { & $launcher -3 -m venv .venv }
        else { & $launcher -m venv .venv }
        if ($LASTEXITCODE -ne 0) { Problem 'could not create .venv' }
    }
}

if (Test-Path $venvPython) {
    & $venvPython -m pip install --quiet --upgrade pip
    & $venvPython -m pip install --quiet -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Problem 'pip install -r requirements.txt failed' }
    else { Note 'packages installed in .venv' }

    # ---- libraries ----------------------------------------------------------
    Step 'Libraries'
    if ($found['Git']) {
        $libArgs = @('scripts\fetch_libs.py')
        if ($AllLibs) { $libArgs += '--all' }
        & $venvPython @libArgs
        if ($LASTEXITCODE -ne 0) { Problem 'some libraries could not be fetched (see above)' }
        else { Note 'commit libs.lock.json so other machines get the same versions' }
    } else {
        Problem 'Git is missing, libraries were not fetched'
    }

    # ---- self-test ----------------------------------------------------------
    Step 'Self-test'
    & $venvPython -m unittest discover -s tests -q
    if ($LASTEXITCODE -ne 0) { Problem 'unit tests failed' }

    & $venvPython laser\name-tag\job.py | Out-Null
    & $venvPython scripts\check_svg.py laser\name-tag\build\job.svg
    if ($LASTEXITCODE -ne 0) { Problem 'example laser job did not validate' }

    if ($found['OpenSCAD']) {
        & $venvPython scripts\build_part.py printer\cable-clip
        if ($LASTEXITCODE -ne 0) { Problem 'example part did not build' }
    } else {
        Note 'skipped the example part build (no OpenSCAD)'
    }
}

elseif ($found['Python']) {
    Problem '.venv was not created correctly; delete the .venv folder and rerun'
}

# ---- summary ----------------------------------------------------------------
Step 'Summary'
if ($problems.Count -eq 0) {
    Write-Host '   Ready.' -ForegroundColor Green
    Note 'Activate the environment:  .\.venv\Scripts\Activate.ps1'
    Note 'Next: import laser\_import-test\test.svg into xTool Studio and fill in laser\NOTES.md'
    exit 0
}
Write-Host "   $($problems.Count) thing(s) need attention:" -ForegroundColor Yellow
$problems | ForEach-Object { Write-Host "    - $_" }
exit 1
