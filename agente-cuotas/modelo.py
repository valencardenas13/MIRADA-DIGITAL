"""
Modelo y ficha del partido — Mirada Digital

1. Fuerza de ataque/defensa de cada equipo (de local y de visitante) con los
   partidos de la base, dando más peso a los recientes (vida media 180 días) y
   tirando hacia el promedio cuando hay pocos partidos.
2. Goles esperados de cada lado → distribución de Poisson → probabilidad de
   1X2 y Más/Menos.
3. Ajustes: bajas de goleadores (lesión/suspensión) y clima extremo.
4. La ficha junta además forma, cara a cara, estadísticas y árbitro, para
   explicar cada pick.

evaluar() decide qué cuotas se mandan: solo las que el modelo respalda.
"""

import math
import os
import time
from dataclasses import dataclass, field

import db

VIDA_MEDIA_DIAS = 180
PRIOR = 5                 # peso de "partidos promedio" que se suman a cada equipo
MIN_PARTIDOS = int(os.environ.get("MIN_PARTIDOS", "8"))
EDGE_MODELO = float(os.environ.get("EDGE_MODELO", "0.04"))
MAX_DESVIO = float(os.environ.get("MAX_DESVIO", "0.15"))


@dataclass
class Ficha:
    partido_id: int
    liga_id: int
    fecha: int
    local: str
    visitante: str
    local_id: int
    visitante_id: int
    n_local: int = 0
    n_visitante: int = 0
    goles_esperados: tuple[float, float] = (0.0, 0.0)
    matriz: list[list[float]] = field(default_factory=list)
    forma_local: list[str] = field(default_factory=list)
    forma_visitante: list[str] = field(default_factory=list)
    h2h: list[str] = field(default_factory=list)
    stats_local: dict | None = None
    stats_visitante: dict | None = None
    arbitro: dict | None = None
    tarjetas_liga: float | None = None
    bajas: list[dict] = field(default_factory=list)
    clima: dict | None = None
    ajustes: list[str] = field(default_factory=list)

    @property
    def suficiente(self) -> bool:
        return min(self.n_local, self.n_visitante) >= MIN_PARTIDOS

    def prob(self, market_key: str, side: str, line: str | None = None) -> float | None:
        if not self.matriz:
            return None
        m = self.matriz
        rango = range(len(m))
        if market_key == "moneyline":
            ph = sum(m[i][j] for i in rango for j in rango if i > j)
            pd = sum(m[i][i] for i in rango)
            pa = 1 - ph - pd
            return {"home": ph, "draw": pd, "away": pa}.get(side)
        if market_key == "total" and line:
            l = float(line)
            if l != math.floor(l) + 0.5:   # solo líneas .5 (sin empate posible)
                return None
            over = sum(m[i][j] for i in rango for j in rango if i + j > l)
            return {"over": over, "under": 1 - over}.get(side)
        return None


# ── Fuerzas ───────────────────────────────────────────────────────────────────

def _peso(fecha: int, ahora: int) -> float:
    return 0.5 ** ((ahora - fecha) / (VIDA_MEDIA_DIAS * 86400))


def fuerzas(con, antes: int) -> tuple[dict, dict]:
    """Devuelve (promedios por liga, fuerzas por equipo). Todo relativo al promedio de cada liga."""
    partidos = con.execute(f"""SELECT * FROM partidos WHERE fecha < ? AND fecha > ?
                               AND estado IN {db.FINALIZADOS}""", (antes, antes - 2 * 365 * 86400)).fetchall()
    ligas: dict[int, list[float]] = {}
    for p in partidos:
        w = _peso(p["fecha"], antes)
        l = ligas.setdefault(p["liga_id"], [0.0, 0.0, 0.0])
        l[0] += w * p["goles_local"]
        l[1] += w * p["goles_visitante"]
        l[2] += w
    prom = {k: (v[0] / v[2], v[1] / v[2]) for k, v in ligas.items() if v[2] > 0}

    acc: dict[int, dict] = {}
    for p in partidos:
        ph, pa = prom[p["liga_id"]]
        if ph <= 0 or pa <= 0:
            continue
        w = _peso(p["fecha"], antes)
        L = acc.setdefault(p["local_id"], {"ah": 0, "dh": 0, "wh": 0, "aa": 0, "da": 0, "wa": 0, "n": 0})
        V = acc.setdefault(p["visitante_id"], {"ah": 0, "dh": 0, "wh": 0, "aa": 0, "da": 0, "wa": 0, "n": 0})
        L["ah"] += w * p["goles_local"] / ph
        L["dh"] += w * p["goles_visitante"] / pa
        L["wh"] += w
        L["n"] += 1
        V["aa"] += w * p["goles_visitante"] / pa
        V["da"] += w * p["goles_local"] / ph
        V["wa"] += w
        V["n"] += 1

    equipos = {}
    for t, a in acc.items():
        equipos[t] = {
            "ataque_local": (a["ah"] + PRIOR) / (a["wh"] + PRIOR),
            "defensa_local": (a["dh"] + PRIOR) / (a["wh"] + PRIOR),
            "ataque_visit": (a["aa"] + PRIOR) / (a["wa"] + PRIOR),
            "defensa_visit": (a["da"] + PRIOR) / (a["wa"] + PRIOR),
            "n": a["n"],
        }
    return prom, equipos


def matriz_poisson(lh: float, la: float, max_goles: int = 10) -> list[list[float]]:
    ph = [math.exp(-lh) * lh ** k / math.factorial(k) for k in range(max_goles + 1)]
    pa = [math.exp(-la) * la ** k / math.factorial(k) for k in range(max_goles + 1)]
    m = [[ph[i] * pa[j] for j in range(max_goles + 1)] for i in range(max_goles + 1)]
    total = sum(map(sum, m))
    return [[x / total for x in fila] for fila in m]


# ── Ajustes ───────────────────────────────────────────────────────────────────

def _impacto_bajas(con, ficha: Ficha) -> tuple[float, float]:
    factores = {ficha.local_id: 1.0, ficha.visitante_id: 1.0}
    for b in db.bajas_partido(con, ficha.partido_id):
        if b["equipo_id"] not in factores:
            continue
        g = next((j for j in db.goleadores(con, b["equipo_id"]) if j["id"] == b["jugador_id"]), None)
        peso = 0.5 if (b["tipo"] or "").lower().startswith("question") else 1.0
        info = {"equipo": ficha.local if b["equipo_id"] == ficha.local_id else ficha.visitante,
                "nombre": b["nombre"], "motivo": b["motivo"], "duda": peso < 1, "goles": 0, "parte": 0.0}
        if g and g["goles"]:
            total = db.goles_equipo_temporada(con, b["equipo_id"], g["liga_id"], g["temporada"]) or g["goles"]
            parte = min(g["goles"] / total, 0.6)
            info.update(goles=g["goles"], parte=parte)
            # el reemplazante recupera la mitad de lo que aportaba
            factores[b["equipo_id"]] *= 1 - 0.5 * parte * peso
        ficha.bajas.append(info)
    fl = max(factores[ficha.local_id], 0.75)
    fv = max(factores[ficha.visitante_id], 0.75)
    if fl < 0.99:
        ficha.ajustes.append(f"Bajas en {ficha.local}: goles esperados −{(1 - fl) * 100:.0f}%")
    if fv < 0.99:
        ficha.ajustes.append(f"Bajas en {ficha.visitante}: goles esperados −{(1 - fv) * 100:.0f}%")
    return fl, fv


def _impacto_clima(ficha: Ficha) -> float:
    c = ficha.clima
    if not c:
        return 1.0
    f = 1.0
    if (c.get("lluvia") or 0) >= 4 or (c.get("viento") or 0) >= 35:
        f *= 0.93
        ficha.ajustes.append("Lluvia fuerte o viento: goles esperados −7%")
    if (c.get("temperatura") or 0) >= 32:
        f *= 0.95
        ficha.ajustes.append("Calor extremo: goles esperados −5%")
    return f


def _forma(filas, equipo_id: int) -> list[str]:
    out = []
    for p in filas:
        local = p["local_id"] == equipo_id
        gf, gc = (p["goles_local"], p["goles_visitante"]) if local else (p["goles_visitante"], p["goles_local"])
        res = "G" if gf > gc else "E" if gf == gc else "P"
        rival = p["visitante"] if local else p["local"]
        out.append(f"{res} {gf}-{gc} {'vs' if local else 'en'} {rival}")
    return out


# ── Ficha completa ────────────────────────────────────────────────────────────

def armar_ficha(con, partido_id: int, clima: dict | None = None, cache_fuerzas=None) -> Ficha | None:
    p = con.execute("""SELECT p.*, el.nombre local, ev.nombre visitante FROM partidos p
                       JOIN equipos el ON el.id = p.local_id JOIN equipos ev ON ev.id = p.visitante_id
                       WHERE p.id = ?""", (partido_id,)).fetchone()
    if not p:
        return None
    antes = min(p["fecha"], int(time.time()))
    f = Ficha(partido_id=p["id"], liga_id=p["liga_id"], fecha=p["fecha"], local=p["local"],
              visitante=p["visitante"], local_id=p["local_id"], visitante_id=p["visitante_id"], clima=clima)

    prom, eq = cache_fuerzas or fuerzas(con, antes)
    L, V = eq.get(p["local_id"]), eq.get(p["visitante_id"])
    f.n_local, f.n_visitante = (L or {}).get("n", 0), (V or {}).get("n", 0)
    if L and V:
        ph, pa = prom.get(p["liga_id"]) or (sum(x[0] for x in prom.values()) / len(prom),
                                            sum(x[1] for x in prom.values()) / len(prom))
        lh = ph * L["ataque_local"] * V["defensa_visit"]
        la = pa * V["ataque_visit"] * L["defensa_local"]
        fl, fv = _impacto_bajas(con, f)
        fc = _impacto_clima(f)
        lh, la = lh * fl * fc, la * fv * fc
        f.goles_esperados = (lh, la)
        f.matriz = matriz_poisson(lh, la)
    else:
        f.bajas = []

    f.forma_local = _forma(db.ultimos_partidos(con, p["local_id"], antes), p["local_id"])
    f.forma_visitante = _forma(db.ultimos_partidos(con, p["visitante_id"], antes), p["visitante_id"])
    f.h2h = [f"{r['local']} {r['goles_local']}-{r['goles_visitante']} {r['visitante']}"
             for r in db.cara_a_cara(con, p["local_id"], p["visitante_id"], antes)]
    f.stats_local = db.promedio_stats(con, p["local_id"], antes)
    f.stats_visitante = db.promedio_stats(con, p["visitante_id"], antes)
    f.arbitro = db.stats_arbitro(con, p["arbitro"], antes)
    f.tarjetas_liga = db.promedio_liga_tarjetas(con, p["liga_id"], antes - 365 * 86400)
    return f


# ── Decisión: qué se manda y qué no ───────────────────────────────────────────

def evaluar(mercados, ficha: Ficha | None, edge_mercado: float) -> tuple[list[dict], list[dict]]:
    """
    Una cuota se manda solo si:
      1. hay historial suficiente de los dos equipos (MIN_PARTIDOS)
      2. el modelo le da ventaja ≥ EDGE_MODELO (cuota × prob_modelo − 1)
      3. no está por debajo de la probabilidad justa del mercado
      4. modelo y mercado no están tan lejos (≤ MAX_DESVIO) como para sospechar info que falta
    Devuelve (picks, descartes). Solo se listan como descartes las cuotas que parecían tentadoras.
    """
    picks, descartes = [], []
    for m in mercados:
        if m.market_key not in ("moneyline", "total"):
            continue
        if m.market_key == "moneyline" and "draw" not in m.sides:
            continue
        for side in m.sides:
            if side not in m.mejor or side not in m.justa:
                continue
            cuota, casa = m.mejor[side]
            p_mkt = m.justa[side]
            edge_mkt = cuota * p_mkt - 1
            p_mod = ficha.prob(m.market_key, side, m.line) if ficha else None
            edge_mod = cuota * p_mod - 1 if p_mod is not None else None
            tentadora = edge_mkt >= edge_mercado or (edge_mod is not None and edge_mod >= EDGE_MODELO)
            if not tentadora:
                continue
            base = {"mercado": m, "side": side, "nombre": m.nombres[side], "cuota": cuota, "casa": casa,
                    "p_mercado": p_mkt, "edge_mercado": edge_mkt, "p_modelo": p_mod, "edge_modelo": edge_mod}

            if ficha is None:
                descartes.append({**base, "motivo": "el partido no está en la base de datos"})
            elif not ficha.suficiente:
                descartes.append({**base, "motivo": f"poco historial ({ficha.n_local} y {ficha.n_visitante} partidos)"})
            elif p_mod is None:
                descartes.append({**base, "motivo": "el modelo no cubre este mercado"})
            elif edge_mod < EDGE_MODELO:
                descartes.append({**base, "motivo": f"el historial no la respalda (modelo {p_mod * 100:.1f}%, "
                                                    f"la cuota necesita {100 * (1 + EDGE_MODELO) / cuota:.1f}%)"})
            elif len(m.margenes) < 2:
                # con una sola casa la "probabilidad justa" es la de esa misma casa: no hay contra qué comparar
                descartes.append({**base, "motivo": "una sola casa cotiza este mercado: falta una casa de "
                                                    "referencia para comparar (REFERENCIA)"})
            elif edge_mkt < 0:
                descartes.append({**base, "motivo": "la cuota está por debajo del consenso de las casas"})
            elif abs(p_mod - p_mkt) > MAX_DESVIO:
                descartes.append({**base, "motivo": f"modelo ({p_mod * 100:.0f}%) y mercado ({p_mkt * 100:.0f}%) "
                                                    "muy lejos: puede faltar info (lesión, rotación)"})
            else:
                alta = edge_mkt >= edge_mercado and min(ficha.n_local, ficha.n_visitante) >= 2 * MIN_PARTIDOS
                picks.append({**base, "confianza": "alta" if alta else "media"})
    picks.sort(key=lambda p: -p["edge_modelo"])
    return picks, descartes
