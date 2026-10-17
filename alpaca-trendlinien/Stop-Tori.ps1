$ErrorActionPreference = 'Stop'
$pidFile = Join-Path $PSScriptRoot '.runtime\server.pid'
if (-not (Test-Path -LiteralPath $pidFile)) { Write-Output 'Kein von diesem Projekt gestarteter Prozess vermerkt.'; return }
$toriPid = [int](Get-Content -LiteralPath $pidFile)
$process = Get-CimInstance Win32_Process -Filter "ProcessId = $toriPid" -ErrorAction SilentlyContinue
if ($process) {
    $expectedPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if ($process.ExecutablePath -ne $expectedPython -or $process.CommandLine -notmatch 'server\.py') {
        throw 'Die gespeicherte Prozess-ID gehört nicht zum erwarteten Tori-Server.'
    }
    Stop-Process -Id $toriPid
    Write-Output 'Tori-Server gestoppt.'
}
Remove-Item -LiteralPath $pidFile -Force
