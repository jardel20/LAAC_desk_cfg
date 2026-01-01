# calibracao.ps1 - SUPER SCRIPT COM MENU CLI (MEMÓRIA CORRIGIDA)

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

$VENV_PATH = "\.venv\Scripts\Activate.ps1"
$LOG_FILE = "streamlit.log"
$PID_FILE = "streamlit.pid"
$PORT = 8501

function Clear-Screen {
    Clear-Host
}

function Print-Banner {
    Clear-Screen
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "         CALIBRAÇÃO BANCADAS LED - CONTROLADOR" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "Diretório: $SCRIPT_DIR" -ForegroundColor White
    Write-Host "Porta:      $PORT" -ForegroundColor White
    Write-Host "URL:        http://localhost:$PORT" -ForegroundColor White
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host
}

function Print-Menu {
    Write-Host "📋 MENU PRINCIPAL:" -ForegroundColor Green
    Write-Host "─────────────────────────────" -ForegroundColor Gray
    Write-Host " 1. 🚀 Iniciar Streamlit" -ForegroundColor Yellow
    Write-Host " 2. 🛑 Parar Streamlit" -ForegroundColor Yellow
    Write-Host " 3. ℹ️  Status" -ForegroundColor Yellow
    Write-Host " 4. 📊 Ver Logs" -ForegroundColor Yellow
    Write-Host " 5. 🔄 Reiniciar" -ForegroundColor Yellow
    Write-Host " 6. 👀 Monitor (Auto-restart)" -ForegroundColor Yellow
    Write-Host " 7. 📁 Abrir Pasta Logs" -ForegroundColor Yellow
    Write-Host " 0. ❌ Sair" -ForegroundColor Yellow
    Write-Host "─────────────────────────────" -ForegroundColor Gray
    Write-Host -NoNewline "➤ Escolha uma opção [0-7]: " -ForegroundColor Cyan
}

# FUNÇÃO CORRIGIDA PARA MEMÓRIA
function Get-MemoryMB {
    param([int]$pid)
    
    try {
        $process = Get-Process -Id $pid -ErrorAction Stop
        [math]::Round($process.WorkingSet64 / 1MB, 1)
    }
    catch {
        "N/A"
    }
}

function Start-Server {
    Print-Banner
    Write-Host "🚀 Iniciando Streamlit..." -ForegroundColor Green
    
    if (-not (Test-Path $VENV_PATH)) {
        Write-Host "❌ Venv não encontrada!" -ForegroundColor Red
        Write-Host "Execute: python -m venv .venv && .venv\Scripts\Activate.ps1 && pip install -r requirements.txt" -ForegroundColor Yellow
        Read-Host "Pressione Enter para voltar..."
        return
    }
    
    Write-Host "🧹 Limpando processos antigos..." -ForegroundColor Yellow
    Stop-Process -Name "python" -ErrorAction SilentlyContinue | Out-Null
    
    try {
        # Ativar venv e iniciar Streamlit
        & $VENV_PATH
        $process = Start-Process powershell -ArgumentList "-NoExit -Command `"streamlit run main.py --server.headless true --server.port $PORT --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false`"" -PassThru -RedirectStandardOutput $LOG_FILE -RedirectStandardError "$LOG_FILE"
        
        $process.Id | Out-File $PID_FILE
        Start-Sleep -Seconds 3
        
        if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
            Write-Host "✅ Streamlit INICIADO! (PID: $($process.Id))" -ForegroundColor Green
            $ipAddress = (Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Dhcp | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"}).IPAddress | Select-Object -First 1
            Write-Host "📱 Acesse: http://localhost:$PORT | http://${ipAddress}:8501" -ForegroundColor Cyan
            Write-Host "📊 Logs salvos em: $LOG_FILE" -ForegroundColor Cyan
        }
        else {
            Write-Host "❌ FALHA ao iniciar! Verifique logs:" -ForegroundColor Red
            Get-Content $LOG_FILE -Tail 5
        }
    }
    catch {
        Write-Host "❌ Erro: $_" -ForegroundColor Red
    }
    
    Read-Host "`nPressione Enter para voltar..."
}

function Stop-Server {
    Print-Banner
    Write-Host "🛑 Parando Streamlit..." -ForegroundColor Yellow
    
    if (Test-Path $PID_FILE) {
        $pidValue = Get-Content $PID_FILE
        Write-Host "Finalizando PID $pidValue..." -ForegroundColor Yellow
        Stop-Process -Id $pidValue -ErrorAction SilentlyContinue
        Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
    }
    
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ Streamlit PARADO!" -ForegroundColor Green
    Read-Host "`nPressione Enter para voltar..."
}

function Status-Server {
    Print-Banner
    
    if (Test-Path $PID_FILE) {
        $pidValue = [int](Get-Content $PID_FILE)
        $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
        
        if ($process) {
            $memory = Get-MemoryMB -pid $pidValue
            Write-Host "🟢 RODANDO (PID: $pidValue)" -ForegroundColor Green
            Write-Host "Memória: $memory MB" -ForegroundColor Cyan
        }
        else {
            Write-Host "🔴 PARADO (PID antigo: $pidValue)" -ForegroundColor Red
            Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
        }
    }
    else {
        Write-Host "🔴 PARADO" -ForegroundColor Red
    }
    
    if (Test-Path $LOG_FILE) {
        $lineCount = (Get-Content $LOG_FILE | Measure-Object -Line).Lines
        Write-Host "Logs: $LOG_FILE $lineCount linhas" -ForegroundColor Cyan
    }
    else {
        Write-Host "Logs: $LOG_FILE (0 linhas)" -ForegroundColor Yellow
    }
    
    Read-Host "`nPressione Enter para voltar..."
}

function Show-Logs {
    Print-Banner
    
    if (Test-Path $LOG_FILE) {
        Write-Host "📊 ÚLTIMOS 20 LOGS:" -ForegroundColor Green
        Get-Content $LOG_FILE -Tail 20
        
        Write-Host "`n[q] Sair | [Enter] Atualizar" -ForegroundColor Gray
        
        do {
            $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown").Character
            
            if ($key -eq 'q') {
                break
            }
            elseif ([string]::IsNullOrEmpty($key)) {
                Clear-Host
                Print-Banner
                Write-Host "📊 ÚLTIMOS 20 LOGS (Atualizado):" -ForegroundColor Green
                Get-Content $LOG_FILE -Tail 20
                Write-Host "`n[q] Sair | [Enter] Atualizar" -ForegroundColor Gray
            }
            
            Start-Sleep -Milliseconds 100
        } while ($true)
    }
    else {
        Write-Host "Nenhum log encontrado." -ForegroundColor Yellow
    }
    
    Read-Host "`nPressione Enter para voltar..."
}

function Monitor-Server {
    Print-Banner
    Write-Host "🔄 MODO MONITOR ATIVO (Auto-restart)" -ForegroundColor Cyan
    Write-Host "⚠️  Pressione Ctrl+C para parar" -ForegroundColor Yellow
    Write-Host
    
    try {
        while ($true) {
            if (Test-Path $PID_FILE) {
                $pidValue = [int](Get-Content $PID_FILE)
                $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
                
                if (-not $process) {
                    Write-Host "$(Get-Date): ⚠️ Streamlit caiu! Reiniciando..." -ForegroundColor Red
                    Start-Server
                }
            }
            else {
                Write-Host "$(Get-Date): 🔄 Iniciando..." -ForegroundColor Yellow
                Start-Server
            }
            
            Start-Sleep -Seconds 30
            Clear-Host
            Print-Banner
            Write-Host "👀 MONITOR ATIVO - Verificando a cada 30s..." -ForegroundColor Cyan
        }
    }
    catch {
        Write-Host "`nMonitor interrompido." -ForegroundColor Yellow
    }
}

function Open-LogsDir {
    if (Test-Path $SCRIPT_DIR) {
        Invoke-Item $SCRIPT_DIR
    }
    else {
        Write-Host "📁 Pasta: $SCRIPT_DIR" -ForegroundColor Cyan
        Write-Host "Abra manualmente." -ForegroundColor Yellow
    }
    
    Read-Host "`nPressione Enter para voltar..."
}

# MAIN LOOP - MENU INTERATIVO
while ($true) {
    Print-Banner
    Print-Menu
    
    $choice = Read-Host
    
    switch ($choice) {
        {$_ -in @('1', 'start')} {
            Start-Server
        }
        {$_ -in @('2', 'stop')} {
            Stop-Server
        }
        {$_ -in @('3', 'status', 'st')} {
            Status-Server
        }
        {$_ -in @('4', 'logs', 'l', 'log')} {
            Show-Logs
        }
        {$_ -in @('5', 'restart', 'r')} {
            Stop-Server
            Start-Sleep -Seconds 2
            Start-Server
        }
        {$_ -in @('6', 'monitor', 'm', 'watch')} {
            Monitor-Server
        }
        {$_ -in @('7', 'dir', 'folder')} {
            Open-LogsDir
        }
        {$_ -in @('0', 'q', 'quit', 'exit')} {
            Print-Banner
            Write-Host "👋 Até logo!" -ForegroundColor Green
            exit 0
        }
        default {
            Write-Host "❌ Opção inválida!" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}