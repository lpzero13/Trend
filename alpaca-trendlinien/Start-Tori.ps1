param([ValidateRange(1024,65535)][int]$Port = 8765, [switch]$Worker)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Bitte zuerst die Einrichtung aus README.md ausführen (.venv und requirements.txt).'
}
$localUrl = "http://127.0.0.1:$Port"
try {
    $health = Invoke-RestMethod -Uri "$localUrl/api/health" -TimeoutSec 2
    if ($health.app -eq 'tori-alpaca-local') {
        Write-Output "Tori läuft bereits: $localUrl"
        return
    }
    throw "Port $Port wird bereits von einer anderen Anwendung verwendet."
} catch {
    if ($_.Exception.Message -like 'Port *') { throw }
}
if (-not $Worker) {
    # WMI starts outside the calling terminal's process job. The hidden worker keeps
    # the existing log/PID handling and leaves no persistent scheduler task behind.
    $startup = New-CimInstance -ClassName Win32_ProcessStartup -Property @{ShowWindow = [uint16]0} -ClientOnly
    $workerCommand = 'powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -File "' + $PSCommandPath + '" -Port ' + $Port + ' -Worker'
    $result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine = $workerCommand; CurrentDirectory = $projectRoot; ProcessStartupInformation = $startup
    }
    if ($result.ReturnValue -ne 0) { throw "Unabhängiger Serverstart fehlgeschlagen (Windows-Code $($result.ReturnValue))." }
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        Start-Sleep -Milliseconds 250
        try {
            $health = Invoke-RestMethod -Uri "$localUrl/api/health" -TimeoutSec 1
            if ($health.app -eq 'tori-alpaca-local') { Write-Output "Tori läuft unabhängig vom Terminal: $localUrl"; return }
        } catch { }
    }
    throw 'Serverstart noch nicht bestätigt. Siehe logs/server-error.log.'
}
$logPath = Join-Path $projectRoot 'logs'
$runtimePath = Join-Path $projectRoot '.runtime'
New-Item -ItemType Directory -Path $logPath,$runtimePath -Force | Out-Null
$process = Start-Process -FilePath $pythonPath -ArgumentList @('-u','server.py','--port',"$Port") -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logPath 'server.log') -RedirectStandardError (Join-Path $logPath 'server-error.log') -PassThru
Set-Content -LiteralPath (Join-Path $runtimePath 'server.pid') -Value $process.Id
$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Milliseconds 200
    if ($process.HasExited) { throw 'Der Server konnte nicht starten. Siehe logs/server-error.log.' }
    try {
        $health = Invoke-RestMethod -Uri "$localUrl/api/health" -TimeoutSec 1
        if ($health.app -eq 'tori-alpaca-local') { $ready = $true; break }
    } catch { }
}
if (-not $ready) { throw 'Serverstart noch nicht bestätigt. Siehe logs/server.log.' }
Write-Output "Tori läuft: $localUrl"
