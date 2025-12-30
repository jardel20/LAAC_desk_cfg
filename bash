#!/bin/bash
# calibracao.sh - SUPER SCRIPT COM MENU CLI (MEMÓRIA CORRIGIDA)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PATH="./.venv/bin/activate"
LOG_FILE="streamlit.log"
PID_FILE="streamlit.pid"
PORT=8501

clear_screen() { clear; }

print_banner() {
    clear_screen
    echo "═══════════════════════════════════════════════════════"
    echo "🧬  CALIBRAÇÃO BANCADAS LED - CONTROLADOR"
    echo "═══════════════════════════════════════════════════════"
    echo "Diretório: $SCRIPT_DIR"
    echo "Porta:      $PORT"
    echo "URL:        http://localhost:$PORT"
    echo "═══════════════════════════════════════════════════════"
    echo
}

print_menu() {
    echo "📋 MENU PRINCIPAL:"
    echo "─────────────────────────────"
    echo " 1. 🚀 Iniciar Streamlit"
    echo " 2. 🛑 Parar Streamlit"
    echo " 3. ℹ️  Status"
    echo " 4. 📊 Ver Logs"
    echo " 5. 🔄 Reiniciar"
    echo " 6. 👀 Monitor (Auto-restart)"
    echo " 7. 📁 Abrir Pasta Logs"
    echo " 0. ❌ Sair"
    echo "─────────────────────────────"
    echo -n "➤ Escolha uma opção [0-7]: "
}

# FUNÇÃO CORRIGIDA PARA MEMÓRIA
get_memory_mb() {
    local pid=$1
    local rss_bytes
    rss_bytes=$(ps -p $pid -o rss= 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$rss_bytes" ]; then
        echo "scale=1; $rss_bytes / 1024" | bc -l 2>/dev/null | cut -d. -f1
    else
        echo "N/A"
    fi
}

start_server() {
    print_banner
    echo "🚀 Iniciando Streamlit..."
    
    if [ ! -f "$VENV_PATH" ]; then
        echo "❌ Venv não encontrada!"
        echo "Execute: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
        read -p "Pressione Enter para voltar..."
        return
    fi
    
    echo "🧹 Limpando processos antigos..."
    pkill -f "streamlit run main.py" 2>/dev/null || true
    
    source "$VENV_PATH"
    nohup streamlit run main.py \
        --server.headless true \
        --server.port "$PORT" \
        --server.address 0.0.0.0 \
        --server.enableCORS false \
        --server.enableXsrfProtection false > "$LOG_FILE" 2>&1 &
    
    STREAMLIT_PID=$!
    echo $STREAMLIT_PID > "$PID_FILE"
    
    sleep 3
    if ps -p $STREAMLIT_PID > /dev/null 2>&1; then
        echo "✅ Streamlit INICIADO! (PID: $STREAMLIT_PID)"
        echo "📱 Acesse: http://localhost:$PORT | http://$(hostname -I | awk '{print $1}'):8501"
        echo "📊 Logs salvos em: $LOG_FILE"
    else
        echo "❌ FALHA ao iniciar! Verifique logs:"
        tail -5 "$LOG_FILE"
    fi
    read -p "
Pressione Enter para voltar..."
}

stop_server() {
    print_banner
    echo "🛑 Parando Streamlit..."
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "Finalizando PID $PID..."
        kill $PID 2>/dev/null && rm -f "$PID_FILE" || echo "PID não encontrado"
    fi
    pkill -f "streamlit run main.py" 2>/dev/null || true
    echo "✅ Streamlit PARADO!"
    read -p "
Pressione Enter para voltar..."
}

status_server() {
    print_banner
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            MEMORIA=$(get_memory_mb $PID)
            echo "🟢 RODANDO (PID: $PID)"
            echo "Memória: $MEMORIA MB"
        else
            echo "🔴 PARADO (PID antigo: $PID)"
            rm -f "$PID_FILE"
        fi
    else
        echo "🔴 PARADO"
    fi
    if [ -f "$LOG_FILE" ]; then
        echo "Logs: $LOG_FILE $(wc -l < "$LOG_FILE") linhas"
    else
        echo "Logs: $LOG_FILE (0 linhas)"
    fi
    read -p "
Pressione Enter para voltar..."
}

show_logs() {
    print_banner
    if [ -f "$LOG_FILE" ]; then
        echo "📊 ÚLTIMOS 20 LOGS:"
        tail -20 "$LOG_FILE"
        echo
        echo "[q] Sair | [Enter] Atualizar"
        while true; do
            read -t 1 -n 1 key 2>/dev/null
            if [[ $key == "q" ]]; then
                break
            elif [[ -z $key ]]; then
                clear; print_banner
                echo "📊 ÚLTIMOS 20 LOGS (Atualizado):"
                tail -20 "$LOG_FILE"
                echo "[q] Sair | [Enter] Atualizar"
            fi
        done
    else
        echo "Nenhum log encontrado."
    fi
    read -p "
Pressione Enter para voltar..."
}

monitor_server() {
    print_banner
    echo "🔄 MODO MONITOR ATIVO (Auto-restart)"
    echo "⚠️  Pressione Ctrl+C para parar"
    echo
    while true; do
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ! ps -p $PID > /dev/null 2>&1; then
                echo "$(date): ⚠️ Streamlit caiu! Reiniciando..."
                start_server
            fi
        else
            echo "$(date): 🔄 Iniciando..."
            start_server
        fi
        sleep 30
        clear; print_banner
        echo "👀 MONITOR ATIVO - Verificando a cada 30s..."
    done
}

open_logs_dir() {
    if command -v xdg-open &> /dev/null; then
        xdg-open "$SCRIPT_DIR"
    elif command -v open &> /dev/null; then
        open "$SCRIPT_DIR"
    else
        echo "📁 Pasta: $SCRIPT_DIR"
        echo "Abra manualmente."
    fi
    read -p "
Pressione Enter para voltar..."
}

# MAIN LOOP - MENU INTERATIVO
while true; do
    print_banner
    print_menu
    read -r choice
    
    case $choice in
        1|start)
            start_server ;;
        2|stop)
            stop_server ;;
        3|status|st)
            status_server ;;
        4|logs|l|log)
            show_logs ;;
        5|restart|r)
            stop_server
            sleep 2
            start_server ;;
        6|monitor|m|watch)
            monitor_server ;;
        7|dir|folder)
            open_logs_dir ;;
        0|q|quit|exit)
            print_banner
            echo "👋 Até logo!"
            exit 0 ;;
        *)
            echo "❌ Opção inválida!"
            sleep 1 ;;
    esac
done
