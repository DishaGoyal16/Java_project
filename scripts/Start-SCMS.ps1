param([switch]$Demo, [switch]$NoDashboard, [switch]$Diagnostics)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root '.venv\Scripts\python.exe'
if(-not (Test-Path -LiteralPath $python)) {throw 'Create .venv and install code/backend/requirements.txt first. See java_docs/RUN_PROJECT_WINDOWS.md.'}
$local = Join-Path $root '.local'
New-Item -ItemType Directory -Force $local | Out-Null
$children = @()
$names = @('DATABASE_URL','SECRET_KEY','APP_ENV','SCMS_RULES_TOKEN','SCMS_RULES_ENGINE','SCMS_RULES_URL','SCMS_RULES_PORT','SCMS_RULES_DIAGNOSTICS','SCMS_DEMO_PASSWORD','SCMS_DEMO_DATABASE')
$old = @{}; foreach($name in $names) {$old[$name]=[Environment]::GetEnvironmentVariable($name,'Process')}
function Random-Secret {
    $bytes=New-Object byte[] 32; $rng=[Security.Cryptography.RandomNumberGenerator]::Create()
    try {$rng.GetBytes($bytes); return [Convert]::ToBase64String($bytes)} finally {$rng.Dispose()}
}
function Start-Child($exe,$arguments,$working,$label) {
    $p=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $working -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $local "$label.out.log") -RedirectStandardError (Join-Path $local "$label.err.log")
    return $p
}
function Wait-Health($url,$headers,$process) {
    for($i=0;$i -lt 100;$i++) {
        if($process.HasExited) {throw "Service exited before ready: $url. Check .local logs."}
        try {Invoke-WebRequest -UseBasicParsing -Uri $url -Headers $headers -TimeoutSec 1 | Out-Null;return} catch {Start-Sleep -Milliseconds 300}
    }
    throw "Service not ready: $url"
}
try {
    # Disable SQL parameter logging and detailed public internal errors.
    $env:APP_ENV='production'
    foreach($port in @(8000,8091)+$(if($NoDashboard){@()}else{@(5173)})) {
        if(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {throw "Port $port is already in use. Stop its owner first."}
    }
    if($Demo) {
        $db=(Join-Path $local 'demo.db').Replace('\','/')
        $env:DATABASE_URL="sqlite:///$db"; $env:SCMS_DEMO_DATABASE='1'
        $secure=Read-Host 'Choose a password for the local demo accounts (not saved in scripts)' -AsSecureString
        $env:SCMS_DEMO_PASSWORD=[Net.NetworkCredential]::new('', $secure).Password
        if($env:SCMS_DEMO_PASSWORD.Length -lt 8) {throw 'Use at least eight characters for the demo password.'}
        Push-Location (Join-Path $root 'code/backend')
        try {& $python (Join-Path $PSScriptRoot 'init_demo.py'); if($LASTEXITCODE -ne 0){throw 'Demo setup failed'}} finally {Pop-Location}
        Remove-Item Env:SCMS_DEMO_PASSWORD
    } elseif(-not $env:DATABASE_URL -and -not (Test-Path (Join-Path $root 'code/backend/.env'))) {
        throw 'Set DATABASE_URL for the existing database or use -Demo for a separate SQLite demo database.'
    }
    if(-not $env:SECRET_KEY) {
        if($Demo) {$env:SECRET_KEY=Random-Secret}
        elseif(Test-Path (Join-Path $root 'code/backend/.env')) {
            Push-Location (Join-Path $root 'code/backend')
            try {
                & $python -c "from dotenv import dotenv_values; import sys; sys.exit(0 if dotenv_values('.env').get('SECRET_KEY') else 1)"
                if($LASTEXITCODE -ne 0){throw 'Set SECRET_KEY in the environment or backend .env to preserve login tokens across restarts.'}
            } finally {Pop-Location}
        } else {throw 'Set SECRET_KEY for the existing database; it must remain stable across restarts.'}
    }
    $env:SCMS_RULES_TOKEN=Random-Secret; $env:SCMS_RULES_ENGINE='java'
    $env:SCMS_RULES_PORT='8091';$env:SCMS_RULES_URL='http://127.0.0.1:8091'
    $env:SCMS_RULES_DIAGNOSTICS=if($Diagnostics){'true'}else{'false'}
    & (Join-Path $root 'code/java-rules/build.ps1')
    $java=Start-Child 'java' @('-jar', ('"'+(Join-Path $root 'code/java-rules/build/scms-rules.jar')+'"')) $root 'java'
    $children+=$java;Wait-Health "$env:SCMS_RULES_URL/internal/health" @{Authorization="Bearer $env:SCMS_RULES_TOKEN"} $java
    $api=Start-Child $python @('-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8000') (Join-Path $root 'code/backend') 'api'
    $children+=$api;Wait-Health 'http://127.0.0.1:8000/api/health' @{} $api
    if(-not $NoDashboard) {
        $node=(Get-Command node).Source
        $web=Start-Child $node @('node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5173','--strictPort') (Join-Path $root 'code/web_dashboard') 'web'
        $children+=$web;Wait-Health 'http://127.0.0.1:5173' @{} $web
        Write-Host 'SCMS ready: http://127.0.0.1:5173'
    }
    Write-Host 'API: http://127.0.0.1:8000/docs | Java: loopback 8091 | Logs: .local'
    Write-Host 'Java mode is enabled. A Java outage returns 503; it never silently uses Python.'
    Read-Host 'Press Enter to stop the services started by this script' | Out-Null
} finally {
    foreach($p in $children) {if(-not $p.HasExited){& taskkill.exe /PID $p.Id /T /F 2>$null | Out-Null}}
    foreach($name in $names) {[Environment]::SetEnvironmentVariable($name,$old[$name],'Process')}
}
