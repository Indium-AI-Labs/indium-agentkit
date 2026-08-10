[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$ProjectDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$SkillsDir = Join-Path $RepoRoot "skills"
$AgentsDir = Join-Path $RepoRoot "agents"
$TemplateAgentsFile = Join-Path (Join-Path $RepoRoot "templates") "AGENTS.md"
$HomeDir = $env:USERPROFILE

if ([string]::IsNullOrWhiteSpace($HomeDir)) {
    throw "USERPROFILE is not set; cannot determine the user installation directory."
}

function Test-IsAdministrator {
    try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = [Security.Principal.WindowsPrincipal]::new($identity)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }
    catch {
        return $false
    }
}

function Test-DeveloperMode {
    try {
        $value = Get-ItemPropertyValue `
            -LiteralPath "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" `
            -Name "AllowDevelopmentWithoutDevLicense" `
            -ErrorAction Stop
        return $value -eq 1
    }
    catch {
        return $false
    }
}

if (-not (Test-IsAdministrator) -and -not (Test-DeveloperMode)) {
    Write-Warning (
        "Symbolic links may fail because neither Developer Mode nor an " +
        "Administrator shell was detected. Enable Developer Mode or run " +
        "PowerShell as Administrator."
    )
}

function Get-ResolvedLinkTarget {
    param([string]$LinkPath, [string]$Target)

    $currentTarget = [string](@((Get-Item -LiteralPath $LinkPath -Force).Target)[0])
    if ([System.IO.Path]::IsPathRooted($currentTarget)) {
        return [System.IO.Path]::GetFullPath($currentTarget)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $LinkPath) $currentTarget))
}

function New-AgentKitLink {
    param(
        [Parameter(Mandatory = $true)] [string]$Target,
        [Parameter(Mandatory = $true)] [string]$LinkPath
    )

    $Target = [System.IO.Path]::GetFullPath($Target)
    $LinkPath = [System.IO.Path]::GetFullPath($LinkPath)
    $parent = Split-Path -Parent $LinkPath
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $existing = Get-Item -LiteralPath $LinkPath -Force -ErrorAction SilentlyContinue

    if ($null -ne $existing) {
        $isSymbolicLink = ($existing.PSObject.Properties.Name -contains "LinkType") -and
            $existing.LinkType -eq "SymbolicLink"
        if (-not $isSymbolicLink) {
            Write-Host "skipped:   $LinkPath exists and is not a symbolic link"
            return
        }
        if ([System.StringComparer]::OrdinalIgnoreCase.Equals((Get-ResolvedLinkTarget $LinkPath $Target), $Target)) {
            Write-Host "unchanged: $LinkPath -> $Target"
            return
        }
        Remove-Item -LiteralPath $LinkPath -Force
        $action = "updated"
    }
    else {
        $action = "linked"
    }

    try {
        New-Item -ItemType SymbolicLink -Path $LinkPath -Target $Target -ErrorAction Stop | Out-Null
        Write-Host ("{0,-10}{1} -> {2}" -f ("$action`:"), $LinkPath, $Target)
    }
    catch {
        throw "Failed to create symbolic link '$LinkPath' -> '$Target'. Enable Windows Developer Mode or run PowerShell as Administrator. Original error: $($_.Exception.Message)"
    }
}

function Ensure-AgentKitCollectionDirectory {
    param([string]$SourceDir, [string]$DestinationDir)

    $SourceDir = [System.IO.Path]::GetFullPath($SourceDir)
    $DestinationDir = [System.IO.Path]::GetFullPath($DestinationDir)
    $parent = Split-Path -Parent $DestinationDir
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $existing = Get-Item -LiteralPath $DestinationDir -Force -ErrorAction SilentlyContinue

    if ($null -ne $existing) {
        $isSymbolicLink = ($existing.PSObject.Properties.Name -contains "LinkType") -and
            $existing.LinkType -eq "SymbolicLink"
        if ($isSymbolicLink) {
            if ([System.StringComparer]::OrdinalIgnoreCase.Equals((Get-ResolvedLinkTarget $DestinationDir $SourceDir), $SourceDir)) {
                Remove-Item -LiteralPath $DestinationDir -Force
                New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
                Write-Host "migrated:  $DestinationDir from directory link to per-item links"
                return $true
            }
            Write-Host "skipped:   $DestinationDir is a symbolic link to another location"
            return $false
        }
        if (-not $existing.PSIsContainer) {
            Write-Host "skipped:   $DestinationDir exists and is not a directory"
            return $false
        }
    }

    New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
    return $true
}

function Add-AgentKitCollection {
    param([string]$SourceDir, [string]$DestinationDir, [ValidateSet("Skill", "Agent")][string]$Kind)

    if (-not (Ensure-AgentKitCollectionDirectory $SourceDir $DestinationDir)) {
        return
    }

    if ($Kind -eq "Skill") {
        $items = Get-ChildItem -LiteralPath $SourceDir -Directory
    }
    else {
        $items = Get-ChildItem -LiteralPath $SourceDir -File -Filter "*.md"
    }
    foreach ($item in $items) {
        New-AgentKitLink -Target $item.FullName -LinkPath (Join-Path $DestinationDir $item.Name)
    }
}

Add-AgentKitCollection -SourceDir $SkillsDir -DestinationDir (Join-Path (Join-Path $HomeDir ".claude") "skills") -Kind Skill
Add-AgentKitCollection -SourceDir $SkillsDir -DestinationDir (Join-Path (Join-Path $HomeDir ".codex") "skills") -Kind Skill
Add-AgentKitCollection -SourceDir $SkillsDir -DestinationDir (Join-Path (Join-Path $HomeDir ".gemini") "skills") -Kind Skill
Add-AgentKitCollection -SourceDir $SkillsDir -DestinationDir (Join-Path (Join-Path $HomeDir ".antigravity") "skills") -Kind Skill
Add-AgentKitCollection -SourceDir $AgentsDir -DestinationDir (Join-Path (Join-Path $HomeDir ".claude") "agents") -Kind Agent

if (-not [string]::IsNullOrWhiteSpace($ProjectDir)) {
    if (-not (Test-Path -LiteralPath $ProjectDir -PathType Container)) {
        throw "Project directory does not exist: $ProjectDir"
    }
    $ProjectDir = (Resolve-Path -LiteralPath $ProjectDir).Path
    New-AgentKitLink -Target $TemplateAgentsFile -LinkPath (Join-Path $ProjectDir "AGENTS.md")
    New-AgentKitLink -Target $TemplateAgentsFile -LinkPath (Join-Path $ProjectDir "CLAUDE.md")
    Add-AgentKitCollection -SourceDir $SkillsDir -DestinationDir (Join-Path (Join-Path $ProjectDir ".claude") "skills") -Kind Skill
    Add-AgentKitCollection -SourceDir $AgentsDir -DestinationDir (Join-Path (Join-Path $ProjectDir ".claude") "agents") -Kind Agent

    $builder = Join-Path $PSScriptRoot "build_cursor_rules.py"
    $rulesDir = Join-Path (Join-Path $ProjectDir ".cursor") "rules"
    $python = Get-Command "python" -ErrorAction SilentlyContinue
    $pyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
    if ($null -ne $python) { & $python.Source $builder --skills-dir $SkillsDir --out-dir $rulesDir }
    elseif ($null -ne $pyLauncher) { & $pyLauncher.Source -3 $builder --skills-dir $SkillsDir --out-dir $rulesDir }
    else { throw "Python 3 is required to build Cursor rules, but python and py were not found." }
    if ($LASTEXITCODE -ne 0) { throw "Cursor rule generation failed with exit code $LASTEXITCODE." }
}
