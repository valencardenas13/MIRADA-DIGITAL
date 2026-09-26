"""
Base histórica de EJEMPLO para el modo sin API keys.
Genera 2 temporadas inventadas (resultados, árbitros, estadísticas, goleadores)
y carga bajas y clima para los partidos de MockOddsClient.
"""

import random
import time

import db

EQUIPOS = {  # id: (nombre, ataque, defensa, ciudad)
    1: ("River Plate", 1.35, 0.80, "Buenos Aires"), 2: ("Boca Juniors", 1.10, 0.85, "Buenos Aires"),
    3: ("Racing Club", 1.05, 0.95, "Avellaneda"), 4: ("Independiente", 0.90, 1.05, "Avellaneda"),
    5: ("San Lorenzo", 0.85, 1.00, "Buenos Aires"), 6: ("Estudiantes", 1.00, 0.95, "La Plata"),
    7: ("Real Madrid", 1.45, 0.75, "Madrid"), 8: ("Barcelona", 1.50, 0.85, "Barcelona"),
    9: ("Atletico Madrid", 1.10, 0.75, "Madrid"), 10: ("Sevilla", 0.95, 1.05, "Sevilla"),
    11: ("Flamengo", 1.30, 0.85, "Rio de Janeiro"), 12: ("Palmeiras", 1.20, 0.80, "Sao Paulo"),
}
LIGAS = {128: [1, 2, 3, 4, 5, 6], 140: [7, 8, 9, 10], 71: [11, 12]}
ARBITROS = ["Facundo Tello", "Darío Herrera", "Yael Falcón Pérez", "Nicolás Ramírez"]
ARBITRO_TARJETERO = "Darío Herrera"


def _poisson(rng, lam):
    k, p, l = 0, 1.0, pow(2.718281828, -lam)
    while True:
        p *= rng.random()
        if p <= l:
            return k
        k += 1


def cargar_demo(con, eventos: list[dict]) -> None:
    if con.execute("SELECT COUNT(*) FROM partidos").fetchone()[0]:
        return
    rng = random.Random(7)
    ahora = int(time.time())
    pid = 1000
    goles_temporada: dict[int, int] = {}
    for liga, equipos in LIGAS.items():
        con.execute("INSERT OR REPLACE INTO ligas VALUES (?,?,?,?,?)", (liga, f"Liga {liga}", "", 2026, ahora))
        pares = [(a, b) for a in equipos for b in equipos if a != b]
        # Brasil tiene solo 2 equipos acá: completo con rivales "genéricos" para que haya historial
        vueltas = 6 if liga == 71 else (3 if liga == 140 else 2)
        partidos_liga = pares * vueltas
        rng.shuffle(partidos_liga)
        for i, (h, a) in enumerate(partidos_liga):
            fecha = ahora - (len(partidos_liga) - i) * 4 * 86400 // max(1, len(partidos_liga) // 60)
            nh, ah, dh, ch = EQUIPOS[h]
            na, aa, da, _ = EQUIPOS[a]
            gl = _poisson(rng, 1.45 * ah * da)
            gv = _poisson(rng, 1.10 * aa * dh)
            arb = rng.choice(ARBITROS)
            db.guardar_partido(con, {
                "id": pid, "liga_id": liga, "temporada": 2026 if fecha > ahora - 200 * 86400 else 2025,
                "fecha": fecha, "estado": "FT", "local_id": h, "local": nh, "visitante_id": a, "visitante": na,
                "goles_local": gl, "goles_visitante": gv, "arbitro": arb, "estadio": f"Estadio {nh}", "ciudad": ch})
            for eq, gf, atk in ((h, gl, ah), (a, gv, aa)):
                extra = 1.6 if arb == ARBITRO_TARJETERO else 1.0
                db.guardar_estadisticas(con, pid, eq, {
                    "tiros": 8 + gf * 2 + rng.randint(0, 6), "tiros_arco": 2 + gf + rng.randint(0, 3),
                    "corners": rng.randint(2, 9), "faltas": rng.randint(9, 17),
                    "amarillas": round(rng.randint(1, 3) * extra), "rojas": 1 if rng.random() < 0.05 * extra else 0,
                    "posesion": 50.0, "xg": round(gf * 0.7 + atk * 0.5 + rng.random() * 0.4, 2)})
            if fecha > ahora - 200 * 86400:
                goles_temporada[h] = goles_temporada.get(h, 0) + gl
                goles_temporada[a] = goles_temporada.get(a, 0) + gv
            pid += 1

    # Goleadores: el principal hace ~35% de los goles del equipo
    for eq, (nombre, *_r) in EQUIPOS.items():
        liga = next(l for l, eqs in LIGAS.items() if eq in eqs)
        g = goles_temporada.get(eq, 10)
        for k, parte in enumerate((0.35, 0.15)):
            con.execute("INSERT OR REPLACE INTO jugadores VALUES (?,?,?,?,?,?,?,?,?)",
                        (eq * 100 + k, eq, liga, 2026, f"Delantero {k + 1} ({nombre})",
                         round(g * parte), 3, 20, 1600))

    # Partidos próximos = los de la API de cuotas de ejemplo
    nombre_a_id = {v[0]: k for k, v in EQUIPOS.items()}
    for n, e in enumerate(eventos):
        h, a = nombre_a_id[e["home_team"]], nombre_a_id[e["away_team"]]
        liga = next(l for l, eqs in LIGAS.items() if h in eqs)
        db.guardar_partido(con, {
            "id": 9000 + n, "liga_id": liga, "temporada": 2026, "fecha": e["start_time"], "estado": "NS",
            "local_id": h, "local": e["home_team"], "visitante_id": a, "visitante": e["away_team"],
            "goles_local": None, "goles_visitante": None, "arbitro": ARBITRO_TARJETERO if n == 0 else ARBITROS[0],
            "estadio": f"Estadio {e['home_team']}", "ciudad": EQUIPOS[h][3]})
        hora = e["start_time"] - e["start_time"] % 3600
        con.execute("INSERT OR REPLACE INTO clima VALUES (?,?,?,?,?)",
                    (EQUIPOS[h][3], hora, 14.0, 6.5 if n == 0 else 0.0, 22.0))
    # Boca pierde a su goleador para el superclásico
    con.execute("INSERT OR REPLACE INTO bajas VALUES (?,?,?,?,?,?)",
                (9000, 200, 2, "Delantero 1 (Boca Juniors)", "Missing Fixture", "Lesión muscular"))
    con.commit()
