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

function New-AgentKitLink {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Target,

        [Parameter(Mandatory = $true)]
        [string]$LinkPath
    )

    $Target = [System.IO.Path]::GetFullPath($Target)
    $LinkPath = [System.IO.Path]::GetFullPath($LinkPath)
    $parent = Split-Path -Parent $LinkPath
    New-Item -ItemType Directory -Path $parent -Force | Out-Null

    $existing = Get-Item -LiteralPath $LinkPath -Force -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        $hasLinkType = $existing.PSObject.Properties.Name -contains "LinkType"
        $isSymbolicLink = $hasLinkType -and $existing.LinkType -eq "SymbolicLink"

        if (-not $isSymbolicLink) {
            Write-Host "skipped:   $LinkPath exists and is not a symbolic link"
            return
        }

        $currentTarget = [string](@($existing.Target)[0])
        if ([System.IO.Path]::IsPathRooted($currentTarget)) {
            $resolvedCurrentTarget = [System.IO.Path]::GetFullPath($currentTarget)
        }
        else {
            $resolvedCurrentTarget = [System.IO.Path]::GetFullPath(
                (Join-Path $parent $currentTarget)
            )
        }

        if ([System.StringComparer]::OrdinalIgnoreCase.Equals($resolvedCurrentTarget, $Target)) {
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
        New-Item -ItemType SymbolicLink -Path $LinkPath -Target $Target -ErrorAction Stop |
            Out-Null
        Write-Host ("{0,-10}{1} -> {2}" -f ("$action`:"), $LinkPath, $Target)
    }
    catch {
        throw (
            "Failed to create symbolic link '$LinkPath' -> '$Target'. " +
            "Enable Windows Developer Mode or run PowerShell as Administrator. " +
            "Original error: $($_.Exception.Message)"
        )
    }
}

New-AgentKitLink -Target $SkillsDir -LinkPath (Join-Path (Join-Path $HomeDir ".claude") "skills")
New-AgentKitLink -Target $SkillsDir -LinkPath (Join-Path (Join-Path $HomeDir ".codex") "skills")
New-AgentKitLink -Target $SkillsDir -LinkPath (Join-Path (Join-Path $HomeDir ".gemini") "skills")
New-AgentKitLink -Target $SkillsDir -LinkPath (Join-Path (Join-Path $HomeDir ".antigravity") "skills")
New-AgentKitLink -Target $AgentsDir -LinkPath (Join-Path (Join-Path $HomeDir ".claude") "agents")

if (-not [string]::IsNullOrWhiteSpace($ProjectDir)) {
    if (-not (Test-Path -LiteralPath $ProjectDir -PathType Container)) {
        throw "Project directory does not exist: $ProjectDir"
    }

    $ProjectDir = (Resolve-Path -LiteralPath $ProjectDir).Path
    New-AgentKitLink -Target $TemplateAgentsFile -LinkPath (Join-Path $ProjectDir "AGENTS.md")
    New-AgentKitLink -Target $TemplateAgentsFile -LinkPath (Join-Path $ProjectDir "CLAUDE.md")
    New-AgentKitLink -Target $SkillsDir -LinkPath (Join-Path (Join-Path $ProjectDir ".claude") "skills")
    New-AgentKitLink -Target $AgentsDir -LinkPath (Join-Path (Join-Path $ProjectDir ".claude") "agents")

    $builder = Join-Path $PSScriptRoot "build_cursor_rules.py"
    $rulesDir = Join-Path (Join-Path $ProjectDir ".cursor") "rules"
    $python = Get-Command "python" -ErrorAction SilentlyContinue
    $pyLauncher = Get-Command "py" -ErrorAction SilentlyContinue

    if ($null -ne $python) {
        & $python.Source $builder --skills-dir $SkillsDir --out-dir $rulesDir
    }
    elseif ($null -ne $pyLauncher) {
        & $pyLauncher.Source -3 $builder --skills-dir $SkillsDir --out-dir $rulesDir
    }
    else {
        throw "Python 3 is required to build Cursor rules, but python and py were not found."
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Cursor rule generation failed with exit code $LASTEXITCODE."
    }
}
