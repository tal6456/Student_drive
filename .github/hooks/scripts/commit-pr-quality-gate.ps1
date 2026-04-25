$ErrorActionPreference = "Stop"

$rawInput = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($rawInput)) {
    exit 0
}

$normalized = $rawInput.ToLowerInvariant()
$matchesCommit = $normalized -match "\bgit\s+commit\b"
$matchesPush = $normalized -match "\bgit\s+push\b"
$matchesPRCreate = $normalized -match "\bgh\s+pr\s+create\b"

if (-not ($matchesCommit -or $matchesPush -or $matchesPRCreate)) {
    exit 0
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "../../..")
$venvPython = Join-Path $repoRoot "venv/Scripts/python.exe"
$pythonCommand = if (Test-Path $venvPython) { $venvPython } else { "python" }

$process = Start-Process -FilePath $pythonCommand -ArgumentList @("manage.py", "test", "core.tests") -WorkingDirectory $repoRoot -Wait -NoNewWindow -PassThru

if ($process.ExitCode -eq 0) {
    $allow = @{
        hookSpecificOutput = @{
            hookEventName = "PreToolUse"
            permissionDecision = "allow"
            permissionDecisionReason = "Test gate passed: manage.py test core.tests"
        }
    } | ConvertTo-Json -Depth 5 -Compress
    [Console]::Out.WriteLine($allow)
    exit 0
}

$deny = @{
    hookSpecificOutput = @{
        hookEventName = "PreToolUse"
        permissionDecision = "deny"
        permissionDecisionReason = "Blocked: tests failed (manage.py test core.tests). Fix tests before commit/push/PR create."
    }
} | ConvertTo-Json -Depth 5 -Compress
[Console]::Out.WriteLine($deny)
exit 0
