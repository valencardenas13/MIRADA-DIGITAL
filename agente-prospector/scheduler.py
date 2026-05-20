#!/usr/bin/env python3
"""
Scheduler de Prospección — Mirada Digital
Corre el agente prospector automáticamente según los turnos definidos en rubros.json.

Uso:
  python scheduler.py            # corre según rubros.json
  python scheduler.py --ahora   # corre todos los turnos ahora (para probar)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import schedule

BASE_DIR = Path(__file__).parent
RUBROS_FILE = BASE_DIR / "rubros.json"

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def telegram_send(text: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            httpx.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"},
                timeout=10,
            )
    except Exception:
        pass


def cargar_config() -> dict:
    if not RUBROS_FILE.exists():
        print(f"❌ No encontré {RUBROS_FILE}")
        sys.exit(1)
    return json.loads(RUBROS_FILE.read_text(encoding="utf-8"))


def correr_turno(turno: dict, cantidad: int) -> None:
    rubro     = turno["rubro"]
    ubicacion = turno.get("ubicacion", "Argentina")
    tipo      = turno.get("tipo", "auto")
    hora      = datetime.now().strftime("%H:%M")

    print(f"\n[{hora}] ▶ Iniciando turno: {rubro} | {ubicacion} | {tipo}")

    # Importamos aquí para que cada llamada use el estado actual de las env vars
    from prospector import run_agent
    try:
        run_agent(rubro, ubicacion, tipo, cantidad=cantidad)
    except Exception as e:
        msg = f"⚠️ Error en turno *{rubro}*:\n`{e}`"
        print(msg)
        telegram_send(msg)


def programar_turnos(config: dict) -> None:
    cantidad = config.get("prospectos_por_corrida", 20)
    turnos   = config.get("turnos", [])

    if not turnos:
        print("❌ No hay turnos definidos en rubros.json")
        sys.exit(1)

    for turno in turnos:
        hora  = turno["hora"]
        rubro = turno["rubro"]
        schedule.every().day.at(hora).do(correr_turno, turno=turno, cantidad=cantidad)
        print(f"  ✓ {hora}  →  {rubro}")

    print(f"\n🗓  {len(turnos)} turnos programados. Esperando...\n")
    print("   (Dejá esta ventana abierta. Ctrl+C para detener)\n")
    print("─" * 60)

    telegram_send(
        f"🗓 *Scheduler de Prospección activo*\n"
        f"{len(turnos)} turnos programados hoy:\n"
        + "\n".join(f"• {t['hora']} — {t['rubro']}" for t in turnos)
    )

    while True:
        schedule.run_pending()
        time.sleep(30)


def correr_ahora(config: dict) -> None:
    """Modo prueba: corre todos los turnos uno tras otro sin esperar."""
    cantidad = config.get("prospectos_por_corrida", 20)
    turnos   = config.get("turnos", [])
    print(f"\n⚡ Modo --ahora: corriendo {len(turnos)} turnos seguidos\n")
    for turno in turnos:
        correr_turno(turno, cantidad)
        print("\n⏳ Pausa de 30 segundos entre turnos...\n")
        time.sleep(30)
    print("\n✅ Todos los turnos completados.")


def main():
    parser = argparse.ArgumentParser(description="Scheduler — Mirada Digital")
    parser.add_argument(
        "--ahora", action="store_true",
        help="Corre todos los turnos ahora (modo prueba)"
    )
    args = parser.parse_args()

    for var in ["ANTHROPIC_API_KEY", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID"]:
        if not os.environ.get(var):
            print(f"❌ Falta la variable de entorno: {var}")
            sys.exit(1)

    config = cargar_config()

    print("\n📋 Mirada Digital — Scheduler de Prospección")
    print(f"   Prospectos por corrida: {config.get('prospectos_por_corrida', 20)}")
    print(f"   Turnos configurados:    {len(config.get('turnos', []))}")
    print()

    if args.ahora:
        correr_ahora(config)
    else:
        programar_turnos(config)


if __name__ == "__main__":
    main()
