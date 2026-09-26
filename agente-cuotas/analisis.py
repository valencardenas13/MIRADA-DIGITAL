"""
Análisis de cuotas — Mirada Digital

Funciones puras (sin red) que, para cada mercado de un partido, calculan:
  - mejor cuota por resultado y en qué casa está
  - margen (overround) de cada casa
  - probabilidad "justa" de consenso, sacando el margen de cada casa
  - apuestas con valor: mejor cuota × probabilidad justa − 1 ≥ umbral
  - arbitraje: suma de 1/mejor_cuota < 1  → ganancia asegurada (en teoría)
"""

from dataclasses import dataclass, field

SIDE_ORDER = ["home", "draw", "away", "over", "under", "yes", "no"]


@dataclass
class Mercado:
    key: str                      # market_group_id, ej. "moneyline::0" o "total::0::2.5"
    market_key: str               # moneyline / total / handicap / ...
    line: str | None
    sides: list[str]
    nombres: dict[str, str]       # side -> nombre a mostrar
    cuotas: dict[str, dict[str, float]]          # casa -> side -> cuota
    mejor: dict[str, tuple[float, str]] = field(default_factory=dict)  # side -> (cuota, casa)
    margenes: dict[str, float] = field(default_factory=dict)           # casa -> margen
    justa: dict[str, float] = field(default_factory=dict)              # side -> prob. justa
    valor: list[dict] = field(default_factory=list)
    arbitraje: dict | None = None

    @property
    def titulo(self) -> str:
        if self.market_key == "moneyline":
            return "1X2" if "draw" in self.sides else "Ganador"
        if self.market_key == "total":
            return f"Más/Menos {self.line}"
        if self.market_key == "handicap":
            return f"Hándicap {self.line}"
        return f"{self.market_key} {self.line or ''}".strip()


def agrupar_mercados(lines: list[dict]) -> list[Mercado]:
    grupos: dict[str, dict] = {}
    for l in lines:
        odds = l.get("odds")
        side = l.get("side")
        if not l.get("is_available", True) or not odds or odds <= 1 or not side:
            continue
        if l.get("player_name"):  # props de jugadores: fuera de alcance
            continue
        key = l.get("market_group_id") or f"{l['market_key']}::{l.get('period')}::{l.get('line') or ''}"
        g = grupos.setdefault(key, {"market_key": l["market_key"], "line": l.get("line"),
                                    "cuotas": {}, "nombres": {}})
        g["cuotas"].setdefault(l["bookmaker"], {})[side] = float(odds)
        g["nombres"].setdefault(side, l.get("selection_name") or side)

    mercados = []
    for key, g in grupos.items():
        sides = sorted({s for c in g["cuotas"].values() for s in c},
                       key=lambda s: SIDE_ORDER.index(s) if s in SIDE_ORDER else 99)
        if len(sides) < 2:
            continue
        mercados.append(Mercado(key=key, market_key=g["market_key"], line=g["line"], sides=sides,
                                nombres=g["nombres"], cuotas=g["cuotas"]))
    mercados.sort(key=lambda m: (m.market_key != "moneyline", m.market_key, m.line or ""))
    return mercados


def analizar_mercado(m: Mercado, edge_min: float = 0.03, casas_apuesta: set[str] | None = None) -> Mercado:
    """
    casas_apuesta: casas donde el grupo apuesta. Las demás (referencia, ej. Pinnacle) solo
    se usan para calcular la probabilidad justa; nunca se recomiendan ni entran en arbitrajes.
    """
    # Mejor cuota por resultado, solo entre las casas donde se apuesta
    for side in m.sides:
        ofertas = [(c[side], casa) for casa, c in m.cuotas.items()
                   if side in c and (casas_apuesta is None or casa in casas_apuesta)]
        if ofertas:
            m.mejor[side] = max(ofertas)

    # Margen y probabilidades sin margen, solo con casas que cotizan todos los resultados
    completas = {casa: c for casa, c in m.cuotas.items() if all(s in c for s in m.sides)}
    probs_por_casa = []
    for casa, c in completas.items():
        implicita = sum(1 / c[s] for s in m.sides)
        m.margenes[casa] = implicita - 1
        probs_por_casa.append({s: (1 / c[s]) / implicita for s in m.sides})
    if probs_por_casa:
        m.justa = {s: sum(p[s] for p in probs_por_casa) / len(probs_por_casa) for s in m.sides}

    # Valor: hace falta más de una casa para que el consenso signifique algo
    if len(probs_por_casa) >= 2:
        for side in m.sides:
            if side not in m.mejor:
                continue
            cuota, casa = m.mejor[side]
            edge = cuota * m.justa[side] - 1
            if edge >= edge_min:
                m.valor.append({"side": side, "nombre": m.nombres[side], "cuota": cuota, "casa": casa,
                                "prob_justa": m.justa[side], "cuota_justa": 1 / m.justa[side], "edge": edge})

    # Arbitraje entre casas
    if len(m.mejor) == len(m.sides):
        suma = sum(1 / m.mejor[s][0] for s in m.sides)
        casas_usadas = {m.mejor[s][1] for s in m.sides}
        if suma < 1 and len(casas_usadas) > 1:
            m.arbitraje = {
                "ganancia": 1 / suma - 1,
                "reparto": {s: (1 / m.mejor[s][0]) / suma for s in m.sides},  # % del total a apostar
            }
    return m


def analizar_evento(lines: list[dict], edge_min: float = 0.03, casas_apuesta=None) -> list[Mercado]:
    casas = set(casas_apuesta) if casas_apuesta else None
    return [analizar_mercado(m, edge_min, casas) for m in agrupar_mercados(lines)]
