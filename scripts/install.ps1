# Windows counterpart of install.sh. Links skill\report-decision-framework
# into %USERPROFILE%\.claude\skills\ with a directory junction, which needs
# neither administrator rights nor Developer Mode and, like a symlink, makes
# the repo the single source of truth (no copy, no drift).
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SkillSrc = Join-Path $RepoRoot "skill\report-decision-framework"
$SkillsDir = Join-Path $env:USERPROFILE ".claude\skills"
$SkillDest = Join-Path $SkillsDir "report-decision-framework"

New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null

if (Test-Path -LiteralPath $SkillDest) {
    $Existing = Get-Item -LiteralPath $SkillDest -Force
    if ($Existing.LinkType -in @("Junction", "SymbolicLink")) {
        Write-Host "Replacing existing link $SkillDest"
        # Removes only the link itself, never the target's contents
        $Existing.Delete()
    }
    else {
        Write-Error "$SkillDest exists and is not a link. Move or delete it manually, then re-run this script."
    }
}

New-Item -ItemType Junction -Path $SkillDest -Target $SkillSrc | Out-Null
Write-Host "Linked $SkillDest -> $SkillSrc"
