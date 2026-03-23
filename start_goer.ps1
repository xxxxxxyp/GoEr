$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    $repoRoot = (Get-Location).Path
}

$frontendDir = Join-Path $repoRoot 'frontend'
$condaEnvName = 'Goer'
$CondaPath = "D:\Anaconda\Scripts\conda.exe"

if (-not (Test-Path -LiteralPath $CondaPath)) {
    throw "Conda executable not found: $CondaPath"
}

function Start-CmdWindow {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDir,
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(Mandatory = $true)]
        [string]$CondaEnvName,
        [Parameter(Mandatory = $true)]
        [string]$CondaExePath
    )

    $effectiveCommand = "`"$CondaExePath`" run -n $CondaEnvName --no-capture-output $Command"

    $cmdLine = "title $Title && cd /d `"$WorkingDir`" && $effectiveCommand"
    Start-Process -FilePath 'cmd.exe' -ArgumentList '/k', $cmdLine -WorkingDirectory $WorkingDir | Out-Null
}

Write-Host "[GoEr] Repository root: $repoRoot"
Write-Host '[GoEr] Starting infrastructure (Postgres/Redis)...'

Push-Location $repoRoot
try {
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        docker-compose up -d
    }
    elseif (Get-Command docker -ErrorAction SilentlyContinue) {
        docker compose up -d
    }
    else {
        throw 'Neither docker-compose nor docker CLI was found in PATH.'
    }
}
finally {
    Pop-Location
}

Write-Host '[GoEr] Launching backend...'
Start-CmdWindow -Title 'GoEr - Backend (uvicorn)' -WorkingDir $repoRoot -Command 'uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4' -CondaEnvName $condaEnvName -CondaExePath $CondaPath
Start-Sleep -Seconds 2

Write-Host '[GoEr] Launching worker...'
Start-CmdWindow -Title 'GoEr - Celery Worker' -WorkingDir $repoRoot -Command 'celery -A app.worker.celery_app worker --loglevel=info --pool=solo' -CondaEnvName $condaEnvName -CondaExePath $CondaPath
Start-Sleep -Seconds 2

Write-Host '[GoEr] Launching beat...'
Start-CmdWindow -Title 'GoEr - Celery Beat' -WorkingDir $repoRoot -Command 'celery -A app.worker.celery_app beat --loglevel=info' -CondaEnvName $condaEnvName -CondaExePath $CondaPath
Start-Sleep -Seconds 2

if (Test-Path -LiteralPath $frontendDir) {
    Write-Host '[GoEr] Launching frontend...'

    Push-Location $frontendDir
    try {
        Set-Location $frontendDir
        Start-CmdWindow -Title 'GoEr - Frontend (Vite)' -WorkingDir $frontendDir -Command 'pnpm dev' -CondaEnvName $condaEnvName -CondaExePath $CondaPath
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Warning "Frontend directory not found: $frontendDir"
}

Write-Host '[GoEr] All startup commands dispatched in separate cmd windows.'
