# install.ps1 - daddyshome installer
# Run: powershell -ExecutionPolicy Bypass -File .\install.ps1

$ErrorActionPreference = "Stop"

$ZipPath    = Join-Path $PSScriptRoot "files.zip"
$ToolsDir   = "$env:USERPROFILE\tools"
$InstallDir = "$ToolsDir\daddyshome"
$SkillsDir  = "$env:USERPROFILE\.claude\skills\daddyshome"
$ClaudeDir  = "$env:USERPROFILE\.claude"

$ConfigCandidates = @(
    "$env:APPDATA\Claude\claude_desktop_config.json",
    "$env:USERPROFILE\.claude\claude_desktop_config.json",
    "$env:APPDATA\Anthropic\Claude\claude_desktop_config.json"
)

function Write-Step($msg) { Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "   OK: $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "   WARN: $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "   FAIL: $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "daddyshome installer" -ForegroundColor Magenta
Write-Host "-----------------------------------------"

# Step 1: Unzip
Write-Step "Extracting files.zip"

if (-not (Test-Path $ZipPath)) {
    Write-Fail "Zip not found at $ZipPath"
}

if (-not (Test-Path $ToolsDir)) {
    New-Item -ItemType Directory -Path $ToolsDir | Out-Null
    Write-OK "Created $ToolsDir"
}

$TempExtract = "$env:TEMP\daddyshome_install"
if (Test-Path $TempExtract) {
    Remove-Item $TempExtract -Recurse -Force
}
Expand-Archive -Path $ZipPath -DestinationPath $TempExtract -Force

# Step 2: Scaffold install dir with correct structure
Write-Step "Building project structure"

if (Test-Path $InstallDir) {
    Write-Warn "Existing install found - overwriting"
    Remove-Item $InstallDir -Recurse -Force
}

New-Item -ItemType Directory -Path "$InstallDir\src"  | Out-Null
New-Item -ItemType Directory -Path "$InstallDir\skill" | Out-Null

# Source Python files -> src/
$PyFiles = @("server.py", "scanner.py", "mvp.py", "settings.py", "memory.py", "briefing.py")
foreach ($f in $PyFiles) {
    $src = "$TempExtract\$f"
    if (Test-Path $src) {
        Copy-Item $src "$InstallDir\src\$f"
        Write-OK "Placed src\$f"
    } else {
        Write-Warn "Not found in zip: $f (may be optional)"
    }
}

# SKILL.md -> skill/
if (Test-Path "$TempExtract\SKILL.md") {
    Copy-Item "$TempExtract\SKILL.md" "$InstallDir\skill\SKILL.md"
    Write-OK "Placed skill\SKILL.md"
} else {
    Write-Fail "SKILL.md missing from zip"
}

# Other root files
foreach ($f in @("pyproject.toml", "README.md")) {
    if (Test-Path "$TempExtract\$f") {
        Copy-Item "$TempExtract\$f" "$InstallDir\$f"
    }
}

Write-OK "Project structure built at $InstallDir"
Remove-Item $TempExtract -Recurse -Force

# Step 3: Verify
Write-Step "Verifying file structure"

$RequiredFiles = @(
    "$InstallDir\src\server.py",
    "$InstallDir\src\scanner.py",
    "$InstallDir\src\mvp.py",
    "$InstallDir\src\settings.py",
    "$InstallDir\src\memory.py",
    "$InstallDir\skill\SKILL.md"
)

foreach ($f in $RequiredFiles) {
    if (-not (Test-Path $f)) {
        Write-Fail "Missing: $f"
    }
}
Write-OK "All required files present"

# Step 4: Python check
Write-Step "Checking Python"

try {
    $PyVersion = python --version 2>&1
    Write-OK "Found $PyVersion"
} catch {
    Write-Fail "Python not found. Install from https://python.org then re-run."
}

# Step 5: Install MCP
Write-Step "Installing Python dependencies"

python -m pip install mcp --quiet
$MCPCheck = python -c "import mcp; print('ok')" 2>&1
if ($MCPCheck -eq "ok") {
    Write-OK "mcp package installed"
} else {
    Write-Fail "mcp install failed: $MCPCheck"
}

# Step 6: Find Claude config
Write-Step "Locating Claude Code config"

$ConfigPath = $null
foreach ($candidate in $ConfigCandidates) {
    if (Test-Path $candidate) {
        $ConfigPath = $candidate
        Write-OK "Found config at $ConfigPath"
        break
    }
}

if (-not $ConfigPath) {
    $ConfigPath = "$env:APPDATA\Claude\claude_desktop_config.json"
    $ConfigDir  = Split-Path $ConfigPath
    if (-not (Test-Path $ConfigDir)) {
        New-Item -ItemType Directory -Path $ConfigDir | Out-Null
    }
    "{}" | Set-Content -Path $ConfigPath
    Write-OK "Created new config at $ConfigPath"
}

# Step 7: Patch config
Write-Step "Registering MCP server in Claude Code config"

try {
    $ConfigRaw = Get-Content $ConfigPath -Raw
    if ([string]::IsNullOrWhiteSpace($ConfigRaw)) {
        $ConfigRaw = "{}"
    }
    $Config = $ConfigRaw | ConvertFrom-Json -AsHashtable
} catch {
    Write-Warn "Could not parse existing config - creating fresh one"
    $Config = @{}
}

$McpEntry = @{
    command = "python"
    args    = @("$InstallDir\src\server.py")
    type    = "stdio"
}

if (-not $Config.ContainsKey("mcpServers")) {
    $Config["mcpServers"] = @{}
}
$Config["mcpServers"]["daddyshome"] = $McpEntry
$Config | ConvertTo-Json -Depth 10 | Set-Content -Path $ConfigPath
Write-OK "MCP server registered"

# Step 8: Install skill
Write-Step "Installing daddyshome skill"

if (-not (Test-Path $SkillsDir)) {
    New-Item -ItemType Directory -Path $SkillsDir | Out-Null
}

Copy-Item -Path "$InstallDir\skill\SKILL.md" -Destination "$SkillsDir\SKILL.md" -Force
Write-OK "Skill installed to $SkillsDir\SKILL.md"

# Step 9: Global MEMORY.md
Write-Step "Setting up global MEMORY.md"

if (-not (Test-Path $ClaudeDir)) {
    New-Item -ItemType Directory -Path $ClaudeDir | Out-Null
}

$GlobalMemory = "$ClaudeDir\MEMORY.md"
if (-not (Test-Path $GlobalMemory)) {
    $MemContent = "# Global MEMORY.md`n`nTracks cross-project learnings and session history.`n`n---`n`n## Project History`n`n## Cross-Project Learnings`n"
    $MemContent | Set-Content -Path $GlobalMemory
    Write-OK "Created global MEMORY.md"
} else {
    Write-OK "Global MEMORY.md already exists - skipped"
}

# Step 10: Verify server loads
Write-Step "Verifying server loads correctly"

$TestScript = "import sys; sys.path.insert(0, r'$InstallDir\src'); from scanner import scan_for_prd; from mvp import generate_mvp_structure; from mcp.server import Server; print('ok')"
$TestResult = python -c $TestScript 2>&1

if ($TestResult -eq "ok") {
    Write-OK "Server modules load cleanly"
} else {
    Write-Warn "Server check returned: $TestResult"
}

# Done
Write-Host ""
Write-Host "-----------------------------------------"
Write-Host "Installation complete" -ForegroundColor Magenta
Write-Host ""
Write-Host "  Install dir : $InstallDir"
Write-Host "  Config      : $ConfigPath"
Write-Host "  Skill       : $SkillsDir\SKILL.md"
Write-Host "  Global mem  : $GlobalMemory"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Restart Claude Code completely"
Write-Host "  2. Open any project folder"
Write-Host "  3. Type: daddyshome"
Write-Host ""
