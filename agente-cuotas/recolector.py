#!/usr/bin/env python3
"""
Recolector — Mirada Digital
Llena y actualiza la base histórica (datos.db) desde API-Football.

Uso:
  python recolector.py                 # sincroniza las ligas de LIGAS
  python recolector.py --temporadas 2  # además baja la temporada anterior (más historial)

El bot lo corre solo cada SYNC_HORAS. Respeta MAX_LLAMADAS por corrida para no
pasarse del plan (el gratuito de API-Football da 100 consultas por día).
"""

import config  # noqa: F401  (carga .env antes que el resto lea variables)

import argparse
import os
import time
import unicodedata
from difflib import SequenceMatcher

import db
import fuentes

LIGAS        = config.lista_numeros("LIGAS", "128,71,13,39,140")
MAX_LLAMADAS = config.numero("MAX_LLAMADAS", 80)
DIAS_BAJAS   = 2   # buscar lesionados/suspendidos de partidos de los próximos 2 días


def sincronizar(con, api: fuentes.ApiFootball, temporadas: int = 1, log=print) -> None:
    ahora = int(time.time())

    def queda() -> bool:
        return api.llamadas < MAX_LLAMADAS

    for liga_id in LIGAS:
        if not queda():
            break
        fila = con.execute("SELECT * FROM ligas WHERE id = ?", (liga_id,)).fetchone()
        if not fila or ahora - (fila["actualizado"] or 0) > 7 * 86400:
            info = api.temporada_actual(liga_id)
            if not info:
                log(f"[Sync] Liga {liga_id}: sin temporada actual, se saltea")
                continue
            con.execute("INSERT OR REPLACE INTO ligas VALUES (?,?,?,?,?)",
                        (liga_id, info["nombre"], info["pais"], info["temporada"], ahora))
            fila = con.execute("SELECT * FROM ligas WHERE id = ?", (liga_id,)).fetchone()

        for temporada in range(fila["temporada"], fila["temporada"] - temporadas, -1):
            if not queda():
                break
            ps = api.partidos(liga_id, temporada)
            for p in ps:
                db.guardar_partido(con, p)
            log(f"[Sync] {fila['nombre']} {temporada}: {len(ps)} partidos")

        if queda():
            gs = api.goleadores(liga_id, fila["temporada"])
            for g in gs:
                con.execute("INSERT OR REPLACE INTO jugadores VALUES (:id,:equipo_id,:liga_id,:temporada,:nombre,"
                            ":goles,:asistencias,:partidos,:minutos)", g)
        con.commit()

    # Estadísticas de partidos terminados (los más recientes primero), de a 20 por llamada
    pendientes = [r["id"] for r in con.execute(f"""
        SELECT id FROM partidos WHERE estado IN {db.FINALIZADOS} AND stats_ok = 0
        ORDER BY fecha DESC""").fetchall()]
    hechos = 0
    while pendientes and queda():
        lote, pendientes = pendientes[:20], pendientes[20:]
        for p, stats in api.partidos_con_estadisticas(lote):
            db.guardar_partido(con, p)
            for equipo_id, s in stats:
                db.guardar_estadisticas(con, p["id"], equipo_id, s)
            # sin estadísticas 3 días después = la liga no tiene cobertura: no reintentar siempre
            if not stats and ahora - p["fecha"] > 3 * 86400:
                con.execute("UPDATE partidos SET stats_ok = -1 WHERE id = ?", (p["id"],))
            hechos += 1
        con.commit()
    log(f"[Sync] Estadísticas: {hechos} partidos nuevos")

    # Bajas de los próximos partidos
    proximos = con.execute("SELECT id FROM partidos WHERE fecha BETWEEN ? AND ? ORDER BY fecha",
                           (ahora, ahora + DIAS_BAJAS * 86400)).fetchall()
    for r in proximos:
        if not queda():
            break
        bajas = api.bajas(r["id"])
        con.execute("DELETE FROM bajas WHERE partido_id = ?", (r["id"],))
        for b in bajas:
            con.execute("INSERT OR REPLACE INTO bajas VALUES (:partido_id,:jugador_id,:equipo_id,:nombre,:tipo,:motivo)", b)
    con.commit()

    liquidar_picks(con)
    log(f"[Sync] Listo — {api.llamadas} consultas usadas")


# ── Vincular un partido de la API de cuotas con uno de la base ────────────────

RUIDO = {"fc", "cf", "ca", "club", "cd", "sc", "ac", "afc", "de", "the", "se", "ec", "cr", "atletico"}


def _norm(nombre: str) -> str:
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    return " ".join(t for t in "".join(c if c.isalnum() else " " for c in s).split() if t not in RUIDO)


def _parecido(a: str, b: str) -> float:
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def vincular(con, evento: dict) -> int | None:
    """Busca en la base el partido que corresponde a un evento de la API de cuotas."""
    fila = con.execute("SELECT partido_id FROM vinculos WHERE event_id = ?", (evento["event_id"],)).fetchone()
    if fila:
        return fila["partido_id"]
    ts = evento.get("start_time") or 0
    candidatos = con.execute("""
        SELECT p.id, el.nombre local, ev.nombre visitante FROM partidos p
        JOIN equipos el ON el.id = p.local_id JOIN equipos ev ON ev.id = p.visitante_id
        WHERE p.fecha BETWEEN ? AND ?""", (ts - 6 * 3600, ts + 6 * 3600)).fetchall()
    mejor, puntaje = None, 0.0
    for c in candidatos:
        s = min(_parecido(evento.get("home_team", ""), c["local"]),
                _parecido(evento.get("away_team", ""), c["visitante"]))
        if s > puntaje:
            mejor, puntaje = c["id"], s
    if mejor and puntaje >= 0.6:
        con.execute("INSERT OR REPLACE INTO vinculos VALUES (?, ?)", (evento["event_id"], mejor))
        con.commit()
        return mejor
    return None


# ── Clima con caché ───────────────────────────────────────────────────────────

def clima(con, ciudad: str | None, ts: int) -> dict | None:
    if not ciudad or ts - time.time() > 15 * 86400:
        return None
    hora = ts - ts % 3600
    fila = con.execute("SELECT * FROM clima WHERE ciudad = ? AND hora = ?", (ciudad, hora)).fetchone()
    if fila:
        return dict(fila)
    coord = con.execute("SELECT lat, lon FROM coordenadas WHERE ciudad = ?", (ciudad,)).fetchone()
    if not coord:
        c = fuentes.coordenadas(ciudad)
        if not c:
            return None
        con.execute("INSERT OR REPLACE INTO coordenadas VALUES (?,?,?)", (ciudad, *c))
        coord = {"lat": c[0], "lon": c[1]}
    p = fuentes.pronostico(coord["lat"], coord["lon"], hora)
    if p:
        con.execute("INSERT OR REPLACE INTO clima VALUES (?,?,?,?,?)",
                    (ciudad, hora, p["temperatura"], p["lluvia"], p["viento"]))
        con.commit()
        return {"ciudad": ciudad, "hora": hora, **p}
    return None


# ── Resultado de los picks enviados ───────────────────────────────────────────

def _gano(pick, gl: int, gv: int) -> str:
    sel = pick["seleccion"]
    if pick["mercado"] == "moneyline":
        real = "home" if gl > gv else "away" if gv > gl else "draw"
        return "ganado" if sel == real else "perdido"
    if pick["mercado"] == "total" and pick["linea"]:
        total, linea = gl + gv, float(pick["linea"])
        if total == linea:
            return "anulado"
        return "ganado" if (total > linea) == (sel == "over") else "perdido"
    return "sin liquidar"


def liquidar_picks(con) -> None:
    for pk in con.execute(f"""
            SELECT k.*, p.goles_local gl, p.goles_visitante gv FROM picks k
            JOIN partidos p ON p.id = k.partido_id
            WHERE k.resultado IS NULL AND p.estado IN {db.FINALIZADOS}""").fetchall():
        con.execute("UPDATE picks SET resultado = ? WHERE id = ?", (_gano(pk, pk["gl"], pk["gv"]), pk["id"]))
    con.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Llena la base histórica desde API-Football")
    parser.add_argument("--temporadas", type=int, default=1, help="cuántas temporadas bajar (1 = actual)")
    args = parser.parse_args()
    key = os.environ.get("API_FOOTBALL_KEY", "").strip()
    if not key:
        raise SystemExit("Falta API_FOOTBALL_KEY (https://dashboard.api-football.com).")
    sincronizar(db.conectar(), fuentes.ApiFootball(key), args.temporadas)
