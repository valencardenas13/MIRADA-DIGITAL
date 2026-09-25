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

    alertas = [a for m in mercados for a in (bloque_arbitraje(e, m, con_titulo=False), bloque_valor(e, m, con_titulo=False)) if a]
    if alertas:
        partes.extend(alertas)
    if faltan:
        partes.append(f"⚠️ Sin cuotas de: {', '.join(faltan)}")
    partes.append(AVISO)
    return "\n\n".join(partes)


def bloque_valor(e: dict, m: Mercado, con_titulo: bool = True) -> str | None:
    if not m.valor:
        return None
    cab = f"💎 <b>Valor</b> — {escape(titulo_evento(e))} · {escape(m.titulo)}" if con_titulo else f"💎 <b>Valor en {escape(m.titulo)}</b>"
    filas = [f"• {escape(v['nombre'])} a <b>{v['cuota']:.2f}</b> en {casa(v['casa'])} "
             f"(justa {v['cuota_justa']:.2f}, ventaja +{pct(v['edge'])})" for v in m.valor]
    return cab + "\n" + "\n".join(filas)


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
