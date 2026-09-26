"""
Base de datos histórica — Mirada Digital

SQLite local con todo lo que el bot consulta antes de mandar una cuota:
partidos (con árbitro y estadio), estadísticas por partido, goleadores,
bajas (lesiones/suspensiones), clima y el registro de picks enviados.
"""

import os
import sqlite3
from pathlib import Path

DB_PATH = os.environ.get("DB_PATH", str(Path(__file__).parent / "datos.db"))

ESQUEMA = """
CREATE TABLE IF NOT EXISTS ligas(
    id INTEGER PRIMARY KEY, nombre TEXT, pais TEXT, temporada INTEGER, actualizado INTEGER);

CREATE TABLE IF NOT EXISTS equipos(id INTEGER PRIMARY KEY, nombre TEXT);

CREATE TABLE IF NOT EXISTS partidos(
    id INTEGER PRIMARY KEY, liga_id INTEGER, temporada INTEGER, fecha INTEGER, estado TEXT,
    local_id INTEGER, visitante_id INTEGER, goles_local INTEGER, goles_visitante INTEGER,
    arbitro TEXT, estadio TEXT, ciudad TEXT, stats_ok INTEGER DEFAULT 0);
CREATE INDEX IF NOT EXISTS ix_partidos_local ON partidos(local_id, fecha);
CREATE INDEX IF NOT EXISTS ix_partidos_visit ON partidos(visitante_id, fecha);
CREATE INDEX IF NOT EXISTS ix_partidos_fecha ON partidos(fecha);

CREATE TABLE IF NOT EXISTS estadisticas(
    partido_id INTEGER, equipo_id INTEGER, tiros INTEGER, tiros_arco INTEGER, corners INTEGER,
    faltas INTEGER, amarillas INTEGER, rojas INTEGER, posesion REAL, xg REAL,
    PRIMARY KEY(partido_id, equipo_id));

CREATE TABLE IF NOT EXISTS jugadores(
    id INTEGER, equipo_id INTEGER, liga_id INTEGER, temporada INTEGER, nombre TEXT,
    goles INTEGER, asistencias INTEGER, partidos INTEGER, minutos INTEGER,
    PRIMARY KEY(id, equipo_id, liga_id, temporada));

CREATE TABLE IF NOT EXISTS bajas(
    partido_id INTEGER, jugador_id INTEGER, equipo_id INTEGER, nombre TEXT, tipo TEXT, motivo TEXT,
    PRIMARY KEY(partido_id, jugador_id));

CREATE TABLE IF NOT EXISTS coordenadas(ciudad TEXT PRIMARY KEY, lat REAL, lon REAL);

CREATE TABLE IF NOT EXISTS clima(
    ciudad TEXT, hora INTEGER, temperatura REAL, lluvia REAL, viento REAL,
    PRIMARY KEY(ciudad, hora));

CREATE TABLE IF NOT EXISTS vinculos(event_id TEXT PRIMARY KEY, partido_id INTEGER);

CREATE TABLE IF NOT EXISTS picks(
    id INTEGER PRIMARY KEY AUTOINCREMENT, creado INTEGER, event_id TEXT, partido_id INTEGER,
    partido TEXT, mercado TEXT, linea TEXT, seleccion TEXT, cuota REAL, casa TEXT,
    prob_modelo REAL, prob_mercado REAL, confianza TEXT, resultado TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS ux_picks ON picks(event_id, mercado, linea, seleccion);
"""


def conectar(path: str | None = None) -> sqlite3.Connection:
    con = sqlite3.connect(path or DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    return con


# ── Escritura ─────────────────────────────────────────────────────────────────

def guardar_partido(con, p: dict) -> None:
    con.execute("INSERT OR REPLACE INTO equipos VALUES (?, ?)", (p["local_id"], p["local"]))
    con.execute("INSERT OR REPLACE INTO equipos VALUES (?, ?)", (p["visitante_id"], p["visitante"]))
    con.execute("""
        INSERT INTO partidos(id, liga_id, temporada, fecha, estado, local_id, visitante_id,
                             goles_local, goles_visitante, arbitro, estadio, ciudad)
        VALUES (:id, :liga_id, :temporada, :fecha, :estado, :local_id, :visitante_id,
                :goles_local, :goles_visitante, :arbitro, :estadio, :ciudad)
        ON CONFLICT(id) DO UPDATE SET
            fecha=excluded.fecha, estado=excluded.estado, goles_local=excluded.goles_local,
            goles_visitante=excluded.goles_visitante, arbitro=COALESCE(excluded.arbitro, arbitro),
            estadio=excluded.estadio, ciudad=excluded.ciudad""", p)


def guardar_estadisticas(con, partido_id: int, equipo_id: int, s: dict) -> None:
    con.execute("""INSERT OR REPLACE INTO estadisticas VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (partido_id, equipo_id, s.get("tiros"), s.get("tiros_arco"), s.get("corners"),
                 s.get("faltas"), s.get("amarillas"), s.get("rojas"), s.get("posesion"), s.get("xg")))
    con.execute("UPDATE partidos SET stats_ok = 1 WHERE id = ?", (partido_id,))


# ── Lectura ───────────────────────────────────────────────────────────────────

FINALIZADOS = ("FT", "AET", "PEN")


def partidos_liga(con, liga_id: int, desde: int) -> list[sqlite3.Row]:
    return con.execute(f"""
        SELECT * FROM partidos WHERE liga_id = ? AND fecha >= ? AND estado IN {FINALIZADOS}
        ORDER BY fecha""", (liga_id, desde)).fetchall()


def ultimos_partidos(con, equipo_id: int, antes: int, n: int = 5) -> list[sqlite3.Row]:
    return con.execute(f"""
        SELECT p.*, el.nombre AS local, ev.nombre AS visitante FROM partidos p
        JOIN equipos el ON el.id = p.local_id JOIN equipos ev ON ev.id = p.visitante_id
        WHERE (p.local_id = ? OR p.visitante_id = ?) AND p.fecha < ? AND p.estado IN {FINALIZADOS}
        ORDER BY p.fecha DESC LIMIT ?""", (equipo_id, equipo_id, antes, n)).fetchall()


def cara_a_cara(con, a: int, b: int, antes: int, n: int = 5) -> list[sqlite3.Row]:
    return con.execute(f"""
        SELECT p.*, el.nombre AS local, ev.nombre AS visitante FROM partidos p
        JOIN equipos el ON el.id = p.local_id JOIN equipos ev ON ev.id = p.visitante_id
        WHERE ((p.local_id = ? AND p.visitante_id = ?) OR (p.local_id = ? AND p.visitante_id = ?))
          AND p.fecha < ? AND p.estado IN {FINALIZADOS}
        ORDER BY p.fecha DESC LIMIT ?""", (a, b, b, a, antes, n)).fetchall()


def promedio_stats(con, equipo_id: int, antes: int, n: int = 10) -> dict | None:
    r = con.execute(f"""
        SELECT COUNT(*) n, AVG(s.tiros) tiros, AVG(s.tiros_arco) tiros_arco, AVG(s.corners) corners,
               AVG(s.amarillas) amarillas, AVG(s.xg) xg, AVG(s.posesion) posesion
        FROM (SELECT id FROM partidos WHERE (local_id = ? OR visitante_id = ?) AND fecha < ?
              AND estado IN {FINALIZADOS} AND stats_ok = 1 ORDER BY fecha DESC LIMIT ?) ult
        JOIN estadisticas s ON s.partido_id = ult.id AND s.equipo_id = ?""",
                    (equipo_id, equipo_id, antes, n, equipo_id)).fetchone()
    return dict(r) if r and r["n"] else None


def stats_arbitro(con, arbitro: str, antes: int) -> dict | None:
    if not arbitro:
        return None
    nombre = arbitro.split(",")[0].strip()   # API-Football a veces agrega ", País"
    r = con.execute(f"""
        SELECT COUNT(DISTINCT p.id) n,
               AVG(p.goles_local + p.goles_visitante) goles,
               AVG(CASE WHEN p.goles_local > p.goles_visitante THEN 1.0 ELSE 0 END) gana_local,
               (SELECT AVG(t.amarillas) FROM (
                    SELECT SUM(s.amarillas) amarillas FROM estadisticas s JOIN partidos q ON q.id = s.partido_id
                    WHERE q.arbitro LIKE ? AND q.fecha < ? AND q.stats_ok = 1 GROUP BY q.id) t) amarillas,
               (SELECT AVG(t.rojas) FROM (
                    SELECT SUM(s.rojas) rojas FROM estadisticas s JOIN partidos q ON q.id = s.partido_id
                    WHERE q.arbitro LIKE ? AND q.fecha < ? AND q.stats_ok = 1 GROUP BY q.id) t) rojas
        FROM partidos p WHERE p.arbitro LIKE ? AND p.fecha < ? AND p.estado IN {FINALIZADOS}""",
                    (nombre + "%", antes, nombre + "%", antes, nombre + "%", antes)).fetchone()
    return {"nombre": nombre, **dict(r)} if r and r["n"] else {"nombre": nombre, "n": 0}


def promedio_liga_tarjetas(con, liga_id: int, desde: int) -> float | None:
    r = con.execute("""
        SELECT AVG(t.am) FROM (SELECT SUM(s.amarillas) am FROM estadisticas s
        JOIN partidos p ON p.id = s.partido_id WHERE p.liga_id = ? AND p.fecha >= ? GROUP BY p.id) t""",
                    (liga_id, desde)).fetchone()
    return r[0] if r else None


def goleadores(con, equipo_id: int) -> list[sqlite3.Row]:
    return con.execute("""SELECT * FROM jugadores WHERE equipo_id = ?
                          ORDER BY temporada DESC, goles DESC""", (equipo_id,)).fetchall()


def bajas_partido(con, partido_id: int) -> list[sqlite3.Row]:
    return con.execute("SELECT * FROM bajas WHERE partido_id = ?", (partido_id,)).fetchall()


def goles_equipo_temporada(con, equipo_id: int, liga_id: int, temporada: int) -> int:
    r = con.execute(f"""
        SELECT COALESCE(SUM(CASE WHEN local_id = ? THEN goles_local ELSE goles_visitante END), 0)
        FROM partidos WHERE (local_id = ? OR visitante_id = ?) AND liga_id = ? AND temporada = ?
          AND estado IN {FINALIZADOS}""", (equipo_id, equipo_id, equipo_id, liga_id, temporada)).fetchone()
    return r[0] or 0
