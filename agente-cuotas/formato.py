"""Arma los mensajes de Telegram (parse_mode HTML)."""

from datetime import datetime, timedelta, timezone
from html import escape, unescape

from analisis import Mercado

NOMBRE_CASA = {"bet365": "Bet365", "betano": "Betano", "stake": "Stake"}
TZ = timezone(timedelta(hours=-3))  # hora Argentina

AVISO = "<i>Info, no consejo. Las cuotas cambian, las casas limitan cuentas y ninguna apuesta es segura. Jugá con responsabilidad (+18).</i>"


def casa(nombre: str) -> str:
    return NOMBRE_CASA.get(nombre, nombre.capitalize())


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def hora(ts: int | None) -> str:
    if not ts:
        return "?"
    return datetime.fromtimestamp(ts, TZ).strftime("%d/%m %H:%M")


def titulo_evento(e: dict) -> str:
    return f"{e.get('home_team', '?')} vs {e.get('away_team', '?')}"


def lista_partidos(eventos: list[dict]) -> str:
    if not eventos:
        return "No encontré partidos en las próximas 48 hs para ese filtro."
    filas = [f"<b>{i}.</b> {escape(titulo_evento(e))}\n     {escape(e.get('league', ''))} · {hora(e.get('start_time'))}"
             for i, e in enumerate(eventos, 1)]
    return "📅 <b>Próximos partidos</b>\n\n" + "\n".join(filas) + "\n\nUsá <code>/cuotas N</code> para comparar un partido."


def _abreviar(texto: str, n: int = 12) -> str:
    return texto if len(texto) <= n else texto[: n - 1] + "…"


def tabla_mercado(m: Mercado, casas: list[str]) -> str:
    casas_ok = [c for c in casas if c in m.cuotas]
    ancho = 13
    head = f"{'':<{ancho}}" + "".join(f"{casa(c)[:7]:>8}" for c in casas_ok)
    filas = [head]
    for side in m.sides:
        mejor = m.mejor.get(side, (0, None))
        celdas = []
        for c in casas_ok:
            v = m.cuotas[c].get(side)
            if v is None:
                celdas.append(f"{'-':>8}")
            else:
                marca = "*" if v == mejor[0] else " "
                celdas.append(f"{v:>7.2f}{marca}")
        filas.append(f"{_abreviar(m.nombres[side]):<{ancho}}" + "".join(celdas))
    if m.margenes:
        filas.append(f"{'Margen':<{ancho}}" + "".join(
            f"{pct(m.margenes[c]):>8}" if c in m.margenes else f"{'-':>8}" for c in casas_ok))
    return f"<b>{escape(m.titulo)}</b>\n<pre>{escape(chr(10).join(filas))}</pre>"


def detalle_evento(e: dict, mercados: list[Mercado], casas: list[str], max_mercados: int = 4) -> str:
    partes = [f"⚽ <b>{escape(titulo_evento(e))}</b>\n{escape(e.get('league', ''))} · {hora(e.get('start_time'))}"]
    if not mercados:
        partes.append("No hay cuotas de estas casas para este partido todavía.")
        return "\n\n".join(partes)

    faltan = [casa(c) for c in casas if not any(c in m.cuotas for m in mercados)]
    for m in mercados[:max_mercados]:
        partes.append(tabla_mercado(m, casas))
    partes.append("<i>* = mejor cuota. Margen = comisión de la casa (más bajo, mejor).</i>")

    for m in mercados:
        if m.justa:
            partes.append(f"🎯 <b>Probabilidad sin margen ({escape(m.titulo)})</b>\n" + "\n".join(
                f"• {escape(m.nombres[s])}: {pct(m.justa[s])} (cuota justa {1 / m.justa[s]:.2f})" for s in m.sides))
            break

    partes.extend(a for m in mercados if (a := bloque_arbitraje(e, m, con_titulo=False)))
    if faltan:
        partes.append(f"⚠️ Sin cuotas de: {', '.join(faltan)}")
    return "\n\n".join(partes)


def bloque_arbitraje(e: dict, m: Mercado, con_titulo: bool = True, total: float = 100) -> str | None:
    if not m.arbitraje:
        return None
    a = m.arbitraje
    cab = (f"🔒 <b>Arbitraje +{pct(a['ganancia'])}</b> — {escape(titulo_evento(e))} · {escape(m.titulo)}"
           if con_titulo else f"🔒 <b>Arbitraje +{pct(a['ganancia'])} en {escape(m.titulo)}</b>")
    filas = [f"• {escape(m.nombres[s])} a {m.mejor[s][0]:.2f} en {casa(m.mejor[s][1])} → apostar {total * a['reparto'][s]:.2f}"
             for s in m.sides]
    return cab + "\n" + "\n".join(filas) + f"\n  (sobre {total:.0f} unidades, retorno ≈ {total * (1 + a['ganancia']):.2f})"


def partir(texto: str, limite: int = 4000) -> list[str]:
    """Corta en bloques respetando saltos de párrafo (no rompe etiquetas HTML)."""
    if len(texto) <= limite:
        return [texto]
    bloques, actual = [], ""
    for parrafo in texto.split("\n\n"):
        if actual and len(actual) + len(parrafo) + 2 > limite:
            bloques.append(actual)
            actual = parrafo
        else:
            actual = f"{actual}\n\n{parrafo}" if actual else parrafo
    if actual:
        bloques.append(actual)
    return bloques


# ── Picks respaldados por datos ───────────────────────────────────────────────

def _racha(forma: list[str]) -> str:
    return " ".join(f.split()[0] for f in forma) or "sin datos"


def _goles_prom(forma: list[str]) -> tuple[float, float] | None:
    if not forma:
        return None
    gf = [int(f.split()[1].split("-")[0]) for f in forma]
    gc = [int(f.split()[1].split("-")[1]) for f in forma]
    return sum(gf) / len(gf), sum(gc) / len(gc)


def _linea_bajas(ficha, equipo: str) -> str | None:
    bs = [b for b in ficha.bajas if b["equipo"] == equipo]
    if not bs:
        return None
    partes = []
    for b in bs[:3]:
        extra = f", {pct(b['parte'])} de sus goles" if b["parte"] else ""
        partes.append(f"{b['nombre']} ({'duda' if b['duda'] else b['motivo'] or 'baja'}{extra})")
    return f"Bajas {equipo}: " + "; ".join(partes)


def _linea_arbitro(ficha) -> str | None:
    a = ficha.arbitro
    if not a or not a.get("n"):
        return f"Árbitro {a['nombre']}: sin partidos en la base" if a else None
    txt = f"Árbitro {a['nombre']} ({a['n']} partidos): {a['goles']:.1f} goles/partido, local gana {pct(a['gana_local'])}"
    if a.get("amarillas") is not None:
        txt += f", {a['amarillas']:.1f} amarillas"
        if ficha.tarjetas_liga:
            txt += f" (liga {ficha.tarjetas_liga:.1f})"
    return txt


def _linea_clima(ficha) -> str | None:
    c = ficha.clima
    if not c:
        return None
    return f"Clima: {c['temperatura']:.0f}°C, lluvia {c['lluvia']:.1f} mm, viento {c['viento']:.0f} km/h"


def _linea_h2h(ficha) -> str | None:
    if not ficha.h2h:
        return None
    return "Últimos cara a cara: " + " · ".join(ficha.h2h[:3])


def razones(ficha, market_key: str, side: str) -> list[str]:
    """Datos que justifican (o matizan) el pick, según la selección."""
    out = []
    lh, la = ficha.goles_esperados
    if market_key == "moneyline":
        equipos = {"home": [ficha.local], "away": [ficha.visitante], "draw": [ficha.local, ficha.visitante]}[side]
        for eq in equipos:
            forma = ficha.forma_local if eq == ficha.local else ficha.forma_visitante
            gp = _goles_prom(forma)
            out.append(f"Forma {eq}: {_racha(forma)}" + (f" ({gp[0]:.1f} a favor, {gp[1]:.1f} en contra)" if gp else ""))
        rival = {"home": ficha.visitante, "away": ficha.local}.get(side)
        for eq in ([rival] if rival else []) + equipos:
            b = _linea_bajas(ficha, eq)
            if b and b not in out:
                out.append(b)
    else:
        for eq, forma, st in ((ficha.local, ficha.forma_local, ficha.stats_local),
                              (ficha.visitante, ficha.forma_visitante, ficha.stats_visitante)):
            gp = _goles_prom(forma)
            if gp:
                txt = f"{eq}: {gp[0] + gp[1]:.1f} goles por partido (últimos {len(forma)})"
                if st and st.get("xg") is not None:
                    txt += f", xG {st['xg']:.2f}"
                out.append(txt)
        for eq in (ficha.local, ficha.visitante):
            b = _linea_bajas(ficha, eq)
            if b:
                out.append(b)
    out.append(f"Goles esperados: {ficha.local} {lh:.2f} – {la:.2f} {ficha.visitante}")
    out.extend(x for x in (_linea_h2h(ficha), _linea_arbitro(ficha), _linea_clima(ficha)) if x)
    out.extend(ficha.ajustes)
    return out


def bloque_pick(e: dict, pick: dict, ficha) -> str:
    m = pick["mercado"]
    icono = "🟢" if pick["confianza"] == "alta" else "🟡"
    cab = (f"{icono} <b>{escape(pick['nombre'])} a {pick['cuota']:.2f}</b> en {casa(pick['casa'])}\n"
           f"{escape(titulo_evento(e))} · {escape(m.titulo)} · {hora(e.get('start_time'))}\n"
           f"Modelo {pct(pick['p_modelo'])} · Mercado {pct(pick['p_mercado'])} · "
           f"Ventaja +{pct(pick['edge_modelo'])} · Confianza {pick['confianza']}")
    porque = "\n".join(f"• {escape(r)}" for r in razones(ficha, m.market_key, pick["side"]))
    return f"{cab}\n<b>Por qué:</b>\n{porque}"


def resumen_descartes(descartes: list[dict], max_items: int = 5) -> str | None:
    if not descartes:
        return None
    filas = [f"• {escape(d['nombre'])} a {d['cuota']:.2f} ({casa(d['casa'])}): {escape(d['motivo'])}"
             for d in descartes[:max_items]]
    resto = f"\n… y {len(descartes) - max_items} más" if len(descartes) > max_items else ""
    return f"🚫 <b>Descartadas ({len(descartes)})</b> — parecían tentadoras pero los datos no acompañan:\n" + "\n".join(filas) + resto


def texto_ficha(e: dict, ficha) -> str:
    if ficha is None:
        return (f"📋 <b>{escape(titulo_evento(e))}</b>\n\nNo encontré este partido en la base de datos. "
                "Revisá que la liga esté en LIGAS y que el recolector haya corrido.")
    lh, la = ficha.goles_esperados
    partes = [f"📋 <b>Ficha: {escape(ficha.local)} vs {escape(ficha.visitante)}</b>\n{hora(ficha.fecha)}"]
    if ficha.matriz:
        p = {s: ficha.prob("moneyline", s) for s in ("home", "draw", "away")}
        o25 = ficha.prob("total", "over", "2.5")
        partes.append(f"🧮 <b>Modelo</b> (historial {ficha.n_local} / {ficha.n_visitante} partidos)\n"
                      f"Goles esperados {lh:.2f} – {la:.2f}\n"
                      f"Local {pct(p['home'])} · Empate {pct(p['draw'])} · Visitante {pct(p['away'])}\n"
                      f"Más de 2.5: {pct(o25)}")
    else:
        partes.append("🧮 Sin historial suficiente para el modelo.")
    for eq, forma, st in ((ficha.local, ficha.forma_local, ficha.stats_local),
                          (ficha.visitante, ficha.forma_visitante, ficha.stats_visitante)):
        txt = f"📈 <b>{escape(eq)}</b> — {_racha(forma)}\n" + "\n".join(f"   {escape(f)}" for f in forma)
        if st:
            txt += (f"\n   Promedio últimos {st['n']}: {st['tiros']:.1f} tiros ({st['tiros_arco']:.1f} al arco), "
                    f"{st['corners']:.1f} córners, {st['amarillas']:.1f} amarillas"
                    + (f", xG {st['xg']:.2f}" if st.get("xg") is not None else ""))
        partes.append(txt)
    extras = [x for x in (_linea_h2h(ficha), _linea_bajas(ficha, ficha.local), _linea_bajas(ficha, ficha.visitante),
                          _linea_arbitro(ficha), _linea_clima(ficha)) if x]
    extras += ficha.ajustes
    if extras:
        partes.append("\n".join(f"• {escape(x)}" for x in extras))
    return "\n\n".join(partes)
