$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$mutex = New-Object System.Threading.Mutex($false, 'Local\OpsmithTelegramBot')
$locked = $false
try {
    $locked = $mutex.WaitOne(0)
} catch [System.Threading.AbandonedMutexException] {
    $locked = $true
}
if (-not $locked) {
    $mutex.Dispose()
    exit 0
}

try {
    if (-not (Test-Path '.env')) {
        throw 'Create bot/.env with BOT_TOKEN and ADMIN_CHAT_ID first.'
    }
    foreach ($line in Get-Content '.env') {
        if ($line -match '^\s*([^#=\s]+)\s*=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2].Trim(), 'Process')
        }
    }

    $python = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
    if (-not (Test-Path $python)) {
        throw 'Create bot/.venv and install requirements.txt first.'
    }
    $env:PYTHONUTF8 = '1'
    # pythonw не открывает консоль. Логи с ротацией ведёт сам Python.
    $process = Start-Process -FilePath $python -ArgumentList @('-u', 'bot.py') `
        -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -Wait
    $code = $process.ExitCode
} finally {
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
exit $code
