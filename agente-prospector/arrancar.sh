#!/bin/bash
# Arranca el scheduler de Mirada Digital.
# Cron lo ejecuta todos los días a las 07:00.

# ── Configurá tus credenciales acá ──────────────────────────────
export ANTHROPIC_API_KEY="sk-ant-REEMPLAZA_CON_TU_KEY"
export TELEGRAM_TOKEN="8676466499:AAGeJp7CjM9-aQBIPRzSpkUhInKhyHi0Yac"
export TELEGRAM_CHAT_ID="1565589249"
# ────────────────────────────────────────────────────────────────

DIRECTORIO="$HOME/MIRADA-DIGITAL/agente-prospector"
LOG="$DIRECTORIO/prospector.log"

cd "$DIRECTORIO" || exit 1

# Si ya hay un scheduler corriendo, no arranca otro
if pgrep -f "python.*scheduler.py" > /dev/null; then
    echo "[$(date)] Ya hay un scheduler activo, no se inicia otro." >> "$LOG"
    exit 0
fi

echo "[$(date)] Iniciando scheduler..." >> "$LOG"
python3 scheduler.py >> "$LOG" 2>&1 &

echo "[$(date)] Scheduler iniciado (PID $!)" >> "$LOG"
