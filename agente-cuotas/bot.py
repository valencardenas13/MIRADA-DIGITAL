#!/usr/bin/env python3
"""
Agente de Cuotas — Mirada Digital
Bot de Telegram para grupos que compara cuotas de Bet365, Betano y Stake,
detecta apuestas con valor y arbitrajes, y opcionalmente comenta con IA.

Uso:
  python bot.py            # corre el bot (long polling)
  python bot.py --prueba   # imprime un análisis de ejemplo en consola, sin Telegram
"""

import argparse
import os
import threading
import time

import httpx

import formato
import ia
from analisis import analizar_evento
from odds_client import OddsApiError, crear_cliente

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")   # grupo para alertas automáticas

CASAS          = [c.strip().lower() for c in os.environ.get("CASAS", "bet365,betano,stake").split(",") if c.strip()]
DEPORTE        = os.environ.get("DEPORTE", "soccer")
LIGAS_ALERTAS  = [l.strip() for l in os.environ.get("LIGAS_ALERTAS", "").split(",") if l.strip()]
EDGE_MIN       = float(os.environ.get("EDGE_MIN", "0.03"))     # 3% de ventaja mínima para "valor"
ESCANEO_MAX    = int(os.environ.get("ESCANEO_MAX", "15"))      # partidos por escaneo (cuida la cuota de la API)
ALERTAS_MIN    = int(os.environ.get("ALERTAS_MIN", "0"))       # cada cuántos minutos escanear; 0 = apagado

API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

AYUDA = f"""🤖 <b>Agente de Cuotas</b> — {', '.join(formato.casa(c) for c in CASAS)}

/partidos [deporte] [liga] — próximos partidos (48 hs)
/cuotas N — compara cuotas del partido N de la última lista
/valor [deporte] [liga] — busca cuotas por encima de la probabilidad justa
/arbitraje [deporte] [liga] — busca apuestas seguras entre casas
/analisis N — comentario del partido hecho con IA
/deportes · /ligas [deporte] · /casas

Ejemplos:
<code>/partidos soccer LaLiga</code>
<code>/cuotas 2</code>
<code>/valor soccer Copa Libertadores</code>

Deporte por defecto: <code>{DEPORTE}</code>"""

cliente, ES_MOCK = crear_cliente()
ultima_lista: dict[int, list[dict]] = {}   # chat_id -> eventos de la última /partidos


# ── Telegram ─────────────────────────────────────────────────────────────────

def enviar(chat_id, texto: str) -> None:
    for bloque in formato.partir(texto):
        try:
            r = httpx.post(f"{API}/sendMessage", json={
                "chat_id": chat_id, "text": bloque, "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }, timeout=15)
            if r.status_code != 200:
                print(f"[Telegram] Error {r.status_code}: {r.text[:200]}", flush=True)
        except httpx.HTTPError as e:
            print(f"[Telegram] Excepción: {e}", flush=True)


def escribiendo(chat_id) -> None:
    try:
        httpx.post(f"{API}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except httpx.HTTPError:
        pass


# ── Lógica de comandos ───────────────────────────────────────────────────────

def _deporte_y_liga(args: list[str]) -> tuple[str, str | None]:
    if not args:
        return DEPORTE, None
    return args[0].lower(), (" ".join(args[1:]) or None)


def _evento_por_arg(chat_id: int, args: list[str]) -> dict | None:
    if not args:
        return None
    ref = args[0]
    lista = ultima_lista.get(chat_id, [])
    if ref.isdigit() and len(ref) <= 3:   # número de la lista (los event_id reales son largos)
        return lista[int(ref) - 1] if 1 <= int(ref) <= len(lista) else None
    # también acepta un event_id directo
    return {"event_id": ref, "home_team": "Evento", "away_team": ref}


def escanear(deporte: str, liga: str | None) -> list[tuple[dict, list]]:
    resultados = []
    for e in cliente.events(deporte, liga, limit=ESCANEO_MAX):
        lineas = cliente.odds(e["event_id"], CASAS)
        resultados.append((e, analizar_evento(lineas, EDGE_MIN)))
    return resultados


def cmd_partidos(chat_id, args):
    deporte, liga = _deporte_y_liga(args)
    eventos = cliente.events(deporte, liga, limit=20)
    ultima_lista[chat_id] = eventos
    return formato.lista_partidos(eventos)


def cmd_cuotas(chat_id, args):
    e = _evento_por_arg(chat_id, args)
    if not e:
        return "No tengo ese partido. Primero <code>/partidos</code> y después <code>/cuotas N</code> con un número de la lista."
    mercados = analizar_evento(cliente.odds(e["event_id"], CASAS), EDGE_MIN)
    return formato.detalle_evento(e, mercados, CASAS)


def cmd_analisis(chat_id, args):
    if not ia.disponible():
        return "El análisis con IA no está activado (falta ANTHROPIC_API_KEY). Usá <code>/cuotas N</code>."
    e = _evento_por_arg(chat_id, args)
    if not e:
        return "No tengo ese partido. Primero <code>/partidos</code> y después <code>/analisis N</code> con un número de la lista."
    mercados = analizar_evento(cliente.odds(e["event_id"], CASAS), EDGE_MIN)
    if not mercados:
        return "No hay cuotas de estas casas para ese partido todavía."
    texto = ia.comentar(e, mercados)
    return f"🧠 <b>{formato.escape(formato.titulo_evento(e))}</b>\n\n{formato.escape(texto)}\n\n{formato.AVISO}"


def _cmd_escaneo(args, tipo: str):
    deporte, liga = _deporte_y_liga(args)
    bloques = []
    for e, mercados in escanear(deporte, liga):
        for m in mercados:
            b = formato.bloque_valor(e, m) if tipo == "valor" else formato.bloque_arbitraje(e, m)
            if b:
                bloques.append(b)
    donde = f"{deporte}{' / ' + liga if liga else ''}"
    if not bloques:
        nada = "cuotas con valor" if tipo == "valor" else "arbitrajes"
        return f"No encontré {nada} ahora en {formato.escape(donde)} (revisé hasta {ESCANEO_MAX} partidos)."
    titulo = "💎 <b>Cuotas con valor</b>" if tipo == "valor" else "🔒 <b>Arbitrajes</b>"
    return f"{titulo} — {formato.escape(donde)}\n\n" + "\n\n".join(bloques) + f"\n\n{formato.AVISO}"


def cmd_casas(chat_id, args):
    try:
        disponibles = set(cliente.bookmakers())
    except OddsApiError as e:
        return f"No pude consultar las casas: {formato.escape(str(e))}"
    filas = [f"{'✅' if c in disponibles else '❌'} {formato.casa(c)}" for c in CASAS]
    nota = "\n\n<i>Modo ejemplo: datos inventados, cargá ODDS_API_KEY para cuotas reales.</i>" if ES_MOCK else ""
    return "🏦 <b>Casas configuradas</b>\n" + "\n".join(filas) + nota


COMANDOS = {
    "start":     lambda c, a: AYUDA,
    "ayuda":     lambda c, a: AYUDA,
    "help":      lambda c, a: AYUDA,
    "partidos":  cmd_partidos,
    "cuotas":    cmd_cuotas,
    "analisis":  cmd_analisis,
    "valor":     lambda c, a: _cmd_escaneo(a, "valor"),
    "arbitraje": lambda c, a: _cmd_escaneo(a, "arbitraje"),
    "deportes":  lambda c, a: "🏟 <b>Deportes</b>\n" + "\n".join(f"• <code>{formato.escape(s)}</code>" for s in cliente.sports()),
    "ligas":     lambda c, a: "🏆 <b>Ligas</b>\n" + "\n".join(
        f"• {formato.escape(l)}" for l in cliente.leagues(a[0] if a else DEPORTE)),
    "casas":     cmd_casas,
}


def procesar(update: dict) -> None:
    msg = update.get("message") or update.get("channel_post")
    if not msg or not msg.get("text", "").startswith("/"):
        return
    chat_id = msg["chat"]["id"]
    partes = msg["text"].split()
    comando = partes[0][1:].split("@")[0].lower()   # en grupos llega como /cuotas@MiBot
    fn = COMANDOS.get(comando)
    if not fn:
        return
    escribiendo(chat_id)
    try:
        respuesta = fn(chat_id, partes[1:])
    except OddsApiError as e:
        respuesta = f"⚠️ {formato.escape(str(e))}"
    except Exception as e:  # que un comando roto no tire abajo el bot
        print(f"[Bot] Error en /{comando}: {e!r}", flush=True)
        respuesta = "⚠️ Algo falló procesando el comando."
    enviar(chat_id, respuesta)


# ── Alertas automáticas ──────────────────────────────────────────────────────

def loop_alertas() -> None:
    ya_avisado: set[str] = set()
    ligas = LIGAS_ALERTAS or [None]
    while True:
        try:
            nuevos = []
            for liga in ligas:
                resultados = escanear(DEPORTE, liga)
                for e, mercados in resultados:
                    for m in mercados:
                        for tipo, bloque in (("arb", formato.bloque_arbitraje(e, m)), ("valor", formato.bloque_valor(e, m))):
                            clave = f"{tipo}:{e['event_id']}:{m.key}"
                            if bloque and clave not in ya_avisado:
                                ya_avisado.add(clave)
                                nuevos.append(bloque)
            if nuevos:
                enviar(TELEGRAM_CHAT_ID, "🚨 <b>Nuevas oportunidades</b>\n\n" + "\n\n".join(nuevos) + f"\n\n{formato.AVISO}")
            print(f"[Alertas] Escaneo OK — {len(nuevos)} nuevas", flush=True)
        except Exception as e:
            print(f"[Alertas] Error: {e!r}", flush=True)
        time.sleep(ALERTAS_MIN * 60)


# ── Main ─────────────────────────────────────────────────────────────────────

def correr_bot() -> None:
    if not TELEGRAM_TOKEN:
        raise SystemExit("Falta TELEGRAM_TOKEN (pedíselo a @BotFather).")
    httpx.post(f"{API}/setMyCommands", json={"commands": [
        {"command": "partidos", "description": "Próximos partidos"},
        {"command": "cuotas", "description": "Comparar cuotas de un partido"},
        {"command": "valor", "description": "Buscar cuotas con valor"},
        {"command": "arbitraje", "description": "Buscar arbitrajes"},
        {"command": "analisis", "description": "Comentario con IA"},
        {"command": "casas", "description": "Casas configuradas"},
        {"command": "ayuda", "description": "Cómo usar el bot"},
    ]}, timeout=15)

    if ALERTAS_MIN > 0 and TELEGRAM_CHAT_ID:
        threading.Thread(target=loop_alertas, daemon=True).start()
        print(f"[Bot] Alertas cada {ALERTAS_MIN} min al chat {TELEGRAM_CHAT_ID}", flush=True)

    print(f"[Bot] Escuchando… casas={CASAS} deporte={DEPORTE} {'(MODO EJEMPLO)' if ES_MOCK else ''}", flush=True)
    offset = None
    while True:
        try:
            r = httpx.get(f"{API}/getUpdates", params={"timeout": 30, "offset": offset}, timeout=40)
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                threading.Thread(target=procesar, args=(upd,), daemon=True).start()
        except httpx.HTTPError as e:
            print(f"[Bot] Error de red: {e}. Reintento en 5 s", flush=True)
            time.sleep(5)


def prueba() -> None:
    """Imprime en consola lo que el bot mandaría, sin tocar Telegram."""
    import re
    limpiar = lambda t: re.sub(r"</?(b|i|pre|code)>", "", formato.unescape(t))
    print(limpiar(cmd_partidos(0, [])), "\n" + "─" * 60)
    print(limpiar(cmd_cuotas(0, ["1"])), "\n" + "─" * 60)
    print(limpiar(_cmd_escaneo([], "valor")), "\n" + "─" * 60)
    print(limpiar(_cmd_escaneo([], "arbitraje")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente de Cuotas — Mirada Digital")
    parser.add_argument("--prueba", action="store_true", help="muestra un análisis de ejemplo en consola")
    if parser.parse_args().prueba:
        prueba()
    else:
        correr_bot()
