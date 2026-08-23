[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$ProjectDir,
    [Parameter(Position = 1)]
    [string]$TargetIde = "all",
    [ValidateSet("Project", "User")]
    [string]$Scope,
    [string]$Item = "all",
    [ValidateSet("Link", "Copy")]
    [string]$Mode = "Link",
    [switch]$NoContext
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$installer = Join-Path $PSScriptRoot "install.py"
$python = Get-Command "python" -ErrorAction SilentlyContinue
$pyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
if ($null -eq $python -and $null -eq $pyLauncher) {
    throw "Python 3 is required to run the installer, but python and py were not found."
}

if ([string]::IsNullOrWhiteSpace($Scope)) {
    $Scope = if ([string]::IsNullOrWhiteSpace($ProjectDir)) { "User" } else { "Project" }
}

$installerArgs = @(
    $installer,
    "--scope", $Scope.ToLowerInvariant(),
    "--target", $TargetIde.ToLowerInvariant(),
    "--item", $Item,
    "--mode", $Mode.ToLowerInvariant()
)
if ($Scope -eq "Project") {
    if ([string]::IsNullOrWhiteSpace($ProjectDir)) {
        throw "ProjectDir is required when Scope is Project."
    }
    $installerArgs += @("--project-dir", $ProjectDir)
    if (-not $NoContext) {
        $installerArgs += "--include-context"
    }
}

if ($null -ne $python) {
    & $python.Source @installerArgs
}
else {
    & $pyLauncher.Source -3 @installerArgs
}
if ($LASTEXITCODE -ne 0) {
    throw "Agentkit installation failed with exit code $LASTEXITCODE."
}
