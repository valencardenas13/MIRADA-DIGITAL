#!/usr/bin/env python3
"""
Diagnóstico de la API de cuotas — Mirada Digital
Resume cómo vienen nombrados los mercados reales de odds-api.net (sin mostrar claves)
y lo guarda en diagnostico.txt para revisarlo.

Uso:
  python diagnostico.py        # primer partido de fútbol de las próximas 48 hs
  python diagnostico.py 3      # el partido 3 de la lista de /partidos
"""

import config  # noqa: F401  (carga .env y tapa claves)

import json
import sys
from collections import Counter
from pathlib import Path

from odds_client import OddsApiClient, crear_cliente

CAMPOS = ("market_key", "type", "bet_type", "period", "period_str", "metric", "line", "side")


def main() -> None:
    cliente, es_mock = crear_cliente()
    if es_mock or not isinstance(cliente, OddsApiClient):
        raise SystemExit("Falta ODDS_API_KEY en .env: el diagnóstico necesita la API real.")
    casas = [c.strip() for c in config.os.environ.get("CASAS", "bet365,betano,stake").split(",") if c.strip()]
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    eventos = cliente.events(config.os.environ.get("DEPORTE", "soccer"), limit=20)
    if not eventos:
        raise SystemExit("La API no devolvió partidos en las próximas 48 hs.")
    e = eventos[min(n, len(eventos)) - 1]
    lineas = cliente.odds(e["event_id"], casas)

    out = [f"Partido: {e.get('home_team')} vs {e.get('away_team')} ({e.get('league')})",
           f"Campos del evento: {sorted(e.keys())}",
           f"Líneas de cuotas: {len(lineas)}",
           f"Casas: {dict(Counter(l.get('bookmaker') for l in lineas))}",
           f"Campos de cada línea: {sorted(set().union(*(l.keys() for l in lineas))) if lineas else []}", ""]
    for campo in CAMPOS:
        out.append(f"── {campo}: {dict(Counter(str(l.get(campo)) for l in lineas).most_common(25))}")
    out.append("\n── Combinaciones market_key | period | side | line (las 40 más comunes):")
    combos = Counter((l.get("market_key"), l.get("period"), l.get("side"), l.get("line")) for l in lineas)
    out += [f"{c}: {k}" for k, c in combos.most_common(40)]
    out.append("\n── Ejemplos de líneas completas:")
    vistos = set()
    for l in lineas:
        clave = (l.get("market_key"), l.get("period"))
        if clave not in vistos and len(vistos) < 12:
            vistos.add(clave)
            out.append(json.dumps(l, ensure_ascii=False, default=str))

    texto = "\n".join(out)
    Path(__file__).with_name("diagnostico.txt").write_text(texto, encoding="utf-8")
    print(texto)
    print("\nGuardado en diagnostico.txt")


if __name__ == "__main__":
    main()
