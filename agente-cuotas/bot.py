#!/usr/bin/env python3
"""
Agente de Cuotas — Mirada Digital
Bot de Telegram para grupos que compara cuotas de Bet365, Betano y Stake y solo
recomienda las que respalda el historial (equipos, jugadores, árbitro, clima)
guardado en la base de datos local.

Uso:
  python bot.py            # corre el bot (long polling)
  python bot.py --prueba   # imprime un análisis de ejemplo en consola, sin Telegram
"""

import argparse
import os
import sqlite3
import threading
import time
from pathlib import Path

import httpx

import db
import formato
import fuentes
import ia
import modelo
import recolector
from analisis import analizar_evento
from odds_client import OddsApiError, crear_cliente

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")   # grupo para alertas automáticas
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()

CASAS          = [c.strip().lower() for c in os.environ.get("CASAS", "bet365,betano,stake").split(",") if c.strip()]
# Casas que no se recomiendan pero sirven de referencia para la probabilidad justa (ej. pinnacle)
REFERENCIA     = [c.strip().lower() for c in os.environ.get("REFERENCIA", "").split(",")
                  if c.strip() and c.strip().lower() not in CASAS]
TODAS          = CASAS + REFERENCIA
DEPORTE        = os.environ.get("DEPORTE", "soccer")
LIGAS_ALERTAS  = [l.strip() for l in os.environ.get("LIGAS_ALERTAS", "").split(",") if l.strip()]
EDGE_MIN       = float(os.environ.get("EDGE_MIN", "0.03"))     # ventaja mínima contra el consenso del mercado
ESCANEO_MAX    = int(os.environ.get("ESCANEO_MAX", "15"))      # partidos por escaneo (cuida la cuota de la API)
ALERTAS_MIN    = int(os.environ.get("ALERTAS_MIN", "0"))       # cada cuántos minutos escanear; 0 = apagado
SYNC_HORAS     = int(os.environ.get("SYNC_HORAS", "12"))       # cada cuántas horas actualizar la base

API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

AYUDA = f"""🤖 <b>Agente de Cuotas</b> — {', '.join(formato.casa(c) for c in CASAS)}

Solo recomiendo cuotas que el historial respalda: forma, goles, cara a cara, bajas, árbitro y clima.

/partidos [deporte] [liga] — próximos partidos (48 hs)
/cuotas N — compara cuotas del partido N + lo que dice el modelo
/ficha N — todos los datos del partido N
/valor [deporte] [liga] — picks respaldados por datos (y los descartados)
/arbitraje [deporte] [liga] — apuestas seguras entre casas
/rendimiento — cómo les fue a los picks enviados
/analisis N — comentario del partido hecho con IA
/deportes · /ligas [deporte] · /casas

Ejemplos:
<code>/partidos soccer LaLiga</code>
<code>/cuotas 2</code>
<code>/valor soccer Copa Libertadores</code>"""

cliente, ES_MOCK = crear_cliente()
ultima_lista: dict[int, list[dict]] = {}   # chat_id -> eventos de la última /partidos

if ES_MOCK and not API_FOOTBALL_KEY:
    DB_PATH = os.environ.get("DB_PATH", str(Path(__file__).parent / "datos_demo.db"))
else:
    DB_PATH = db.DB_PATH


def conexion() -> sqlite3.Connection:
    """Una conexión por hilo/comando: SQLite no comparte bien conexiones entre hilos."""
    return db.conectar(DB_PATH)


def preparar_base() -> None:
    con = conexion()
    if ES_MOCK and not API_FOOTBALL_KEY:
        import demo_datos
        demo_datos.cargar_demo(con, cliente.events(DEPORTE))
        print("[Base] Usando base histórica de EJEMPLO", flush=True)
    elif not API_FOOTBALL_KEY:
        print("[Base] Sin API_FOOTBALL_KEY: no hay datos históricos, ninguna cuota va a pasar el filtro", flush=True)
    n = con.execute("SELECT COUNT(*) FROM partidos").fetchone()[0]
    print(f"[Base] {DB_PATH}: {n} partidos", flush=True)
    con.close()


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


# ── Examen de un partido: cuotas + base de datos + modelo ────────────────────

def examinar(con, e: dict, cache_fuerzas=None):
    mercados = analizar_evento(cliente.odds(e["event_id"], TODAS), EDGE_MIN, CASAS)
    ficha = None
    partido_id = recolector.vincular(con, e)
    if partido_id:
        p = con.execute("SELECT ciudad, fecha FROM partidos WHERE id = ?", (partido_id,)).fetchone()
        clima = recolector.clima(con, p["ciudad"], p["fecha"])
        ficha = modelo.armar_ficha(con, partido_id, clima, cache_fuerzas)
    picks, descartes = modelo.evaluar(mercados, ficha, EDGE_MIN)
    return mercados, ficha, picks, descartes


def registrar(con, e: dict, ficha, pick: dict) -> bool:
    """Guarda el pick enviado. Devuelve False si ya se había mandado antes."""
    m = pick["mercado"]
    cur = con.execute("""INSERT OR IGNORE INTO picks(creado, event_id, partido_id, partido, mercado, linea,
                         seleccion, cuota, casa, prob_modelo, prob_mercado, confianza)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (int(time.time()), e["event_id"], ficha.partido_id, formato.titulo_evento(e), m.market_key,
                       m.line or "", pick["side"], pick["cuota"], pick["casa"], pick["p_modelo"],
                       pick["p_mercado"], pick["confianza"]))
    con.commit()
    return cur.rowcount > 0


def escanear(con, deporte: str, liga: str | None):
    fz = modelo.fuerzas(con, int(time.time()))   # una sola vez por escaneo
    for e in cliente.events(deporte, liga, limit=ESCANEO_MAX):
        yield e, *examinar(con, e, fz)


# ── Comandos ─────────────────────────────────────────────────────────────────

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
    return {"event_id": ref, "home_team": "Evento", "away_team": ref}


NO_ENCONTRADO = "No tengo ese partido. Primero <code>/partidos</code> y después <code>/{cmd} N</code> con un número de la lista."


def cmd_partidos(chat_id, args):
    deporte, liga = _deporte_y_liga(args)
    eventos = cliente.events(deporte, liga, limit=20)
    ultima_lista[chat_id] = eventos
    return formato.lista_partidos(eventos)


def cmd_cuotas(chat_id, args):
    e = _evento_por_arg(chat_id, args)
    if not e:
        return NO_ENCONTRADO.format(cmd="cuotas")
    con = conexion()
    mercados, ficha, picks, descartes = examinar(con, e)
    partes = [formato.detalle_evento(e, mercados, TODAS)]
    if ficha and ficha.matriz:
        p = {s: ficha.prob("moneyline", s) for s in ("home", "draw", "away")}
        partes.append(f"🧮 <b>Modelo con historial</b>: Local {formato.pct(p['home'])} · "
                      f"Empate {formato.pct(p['draw'])} · Visitante {formato.pct(p['away'])}  "
                      f"(<code>/ficha {args[0]}</code> para ver todos los datos)")
    partes += [formato.bloque_pick(e, pk, ficha) for pk in picks]
    if not picks:
        partes.append("Ninguna cuota de este partido pasa el filtro del historial.")
    d = formato.resumen_descartes(descartes)
    if d:
        partes.append(d)
    partes.append(formato.AVISO)
    return "\n\n".join(partes)


def cmd_ficha(chat_id, args):
    e = _evento_por_arg(chat_id, args)
    if not e:
        return NO_ENCONTRADO.format(cmd="ficha")
    con = conexion()
    _, ficha, _, _ = examinar(con, e)
    return formato.texto_ficha(e, ficha)


def cmd_valor(chat_id, args):
    deporte, liga = _deporte_y_liga(args)
    con = conexion()
    bloques, descartes, revisados = [], [], 0
    for e, _, ficha, picks, desc in escanear(con, deporte, liga):
        revisados += 1
        for pk in picks:
            registrar(con, e, ficha, pk)
            bloques.append(formato.bloque_pick(e, pk, ficha))
        descartes += [{**d, "nombre": f"{d['nombre']} ({formato.titulo_evento(e)})"} for d in desc]
    donde = formato.escape(f"{deporte}{' / ' + liga if liga else ''}")
    partes = [f"💎 <b>Picks respaldados por datos</b> — {donde} ({revisados} partidos revisados)"]
    partes += bloques or ["Ninguna cuota pasa el filtro ahora. Mejor no apostar por apostar."]
    d = formato.resumen_descartes(descartes)
    if d:
        partes.append(d)
    partes.append(formato.AVISO)
    return "\n\n".join(partes)


def cmd_arbitraje(chat_id, args):
    deporte, liga = _deporte_y_liga(args)
    bloques = []
    for e in cliente.events(deporte, liga, limit=ESCANEO_MAX):
        for m in analizar_evento(cliente.odds(e["event_id"], TODAS), EDGE_MIN, CASAS):
            b = formato.bloque_arbitraje(e, m)
            if b:
                bloques.append(b)
    donde = formato.escape(f"{deporte}{' / ' + liga if liga else ''}")
    if not bloques:
        return f"No encontré arbitrajes ahora en {donde} (revisé hasta {ESCANEO_MAX} partidos)."
    return f"🔒 <b>Arbitrajes</b> — {donde}\n\n" + "\n\n".join(bloques) + f"\n\n{formato.AVISO}"


def cmd_rendimiento(chat_id, args):
    con = conexion()
    filas = con.execute("SELECT * FROM picks").fetchall()
    if not filas:
        return "Todavía no se mandó ningún pick."
    cerrados = [f for f in filas if f["resultado"] in ("ganado", "perdido", "anulado")]
    ganados = [f for f in cerrados if f["resultado"] == "ganado"]
    perdidos = [f for f in cerrados if f["resultado"] == "perdido"]
    # 1 unidad por pick: ganancia = cuota − 1 si gana, −1 si pierde, 0 si se anula
    neto = sum(f["cuota"] - 1 for f in ganados) - len(perdidos)
    apostado = len(ganados) + len(perdidos)
    txt = (f"📊 <b>Rendimiento de los picks</b>\n"
           f"Enviados: {len(filas)} · Terminados: {len(cerrados)} · Pendientes: {len(filas) - len(cerrados)}\n"
           f"Ganados: {len(ganados)} · Perdidos: {len(perdidos)}")
    if apostado:
        txt += (f"\nAcierto: {formato.pct(len(ganados) / apostado)} · "
                f"Resultado: {neto:+.2f} u · ROI {formato.pct(neto / apostado)}")
        esperado = sum(f["prob_modelo"] for f in cerrados if f["resultado"] != "anulado")
        txt += f"\nEl modelo esperaba {esperado:.1f} aciertos de {apostado}."
    txt += "\n\n<i>1 unidad por pick. Con pocos picks el resultado es mayormente suerte: mirar después de 100+.</i>"
    return txt


def cmd_analisis(chat_id, args):
    if not ia.disponible():
        return "El análisis con IA no está activado (falta ANTHROPIC_API_KEY). Usá <code>/cuotas N</code>."
    e = _evento_por_arg(chat_id, args)
    if not e:
        return NO_ENCONTRADO.format(cmd="analisis")
    con = conexion()
    mercados, ficha, picks, descartes = examinar(con, e)
    if not mercados:
        return "No hay cuotas de estas casas para ese partido todavía."
    texto = ia.comentar(e, mercados, ficha, picks, descartes)
    return f"🧠 <b>{formato.escape(formato.titulo_evento(e))}</b>\n\n{formato.escape(texto)}\n\n{formato.AVISO}"


def cmd_casas(chat_id, args):
    try:
        disponibles = set(cliente.bookmakers())
    except OddsApiError as e:
        return f"No pude consultar las casas: {formato.escape(str(e))}"
    filas = [f"{'✅' if c in disponibles else '❌'} {formato.casa(c)}" for c in CASAS]
    filas += [f"{'✅' if c in disponibles else '❌'} {formato.casa(c)} (solo referencia)" for c in REFERENCIA]
    if len([c for c in TODAS if c in disponibles]) < 2:
        filas.append("\n⚠️ Con una sola casa no hay contra qué comparar: agregá casas de referencia en REFERENCIA "
                     "(ej. pinnacle). Mientras tanto no se van a mandar picks.")
    con = conexion()
    n = con.execute("SELECT COUNT(*) FROM partidos").fetchone()[0]
    filas.append(f"\n🗄 Base histórica: {n} partidos")
    nota = "\n\n<i>Modo ejemplo: datos inventados. Cargá ODDS_API_KEY y API_FOOTBALL_KEY para datos reales.</i>" if ES_MOCK else ""
    return "🏦 <b>Casas configuradas</b>\n" + "\n".join(filas) + nota


COMANDOS = {
    "start":       lambda c, a: AYUDA,
    "ayuda":       lambda c, a: AYUDA,
    "help":        lambda c, a: AYUDA,
    "partidos":    cmd_partidos,
    "cuotas":      cmd_cuotas,
    "ficha":       cmd_ficha,
    "analisis":    cmd_analisis,
    "valor":       cmd_valor,
    "arbitraje":   cmd_arbitraje,
    "rendimiento": cmd_rendimiento,
    "deportes":    lambda c, a: "🏟 <b>Deportes</b>\n" + "\n".join(f"• <code>{formato.escape(s)}</code>" for s in cliente.sports()),
    "ligas":       lambda c, a: "🏆 <b>Ligas</b>\n" + "\n".join(
        f"• {formato.escape(l)}" for l in cliente.leagues(a[0] if a else DEPORTE)),
    "casas":       cmd_casas,
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


# ── Tareas de fondo ──────────────────────────────────────────────────────────

arbitrajes_avisados: set[tuple] = set()


def loop_alertas() -> None:
    ligas = LIGAS_ALERTAS or [None]
    while True:
        try:
            con = conexion()
            nuevos = []
            for liga in ligas:
                for e, mercados, ficha, picks, _ in escanear(con, DEPORTE, liga):
                    for pk in picks:
                        if registrar(con, e, ficha, pk):   # solo lo que no se mandó antes
                            nuevos.append(formato.bloque_pick(e, pk, ficha))
                    for m in mercados:
                        b = formato.bloque_arbitraje(e, m)
                        clave = ("arb", e["event_id"], m.key)
                        if b and clave not in arbitrajes_avisados:
                            arbitrajes_avisados.add(clave)
                            nuevos.append(b)
            if nuevos:
                enviar(TELEGRAM_CHAT_ID, "🚨 <b>Nuevas oportunidades respaldadas por datos</b>\n\n"
                       + "\n\n".join(nuevos) + f"\n\n{formato.AVISO}")
            print(f"[Alertas] Escaneo OK — {len(nuevos)} nuevas", flush=True)
            con.close()
        except Exception as e:
            print(f"[Alertas] Error: {e!r}", flush=True)
        time.sleep(ALERTAS_MIN * 60)



def loop_sync() -> None:
    while True:
        try:
            con = conexion()
            recolector.sincronizar(con, fuentes.ApiFootball(API_FOOTBALL_KEY),
                                   log=lambda m: print(m, flush=True))
            con.close()
        except Exception as e:
            print(f"[Sync] Error: {e!r}", flush=True)
        time.sleep(SYNC_HORAS * 3600)


# ── Main ─────────────────────────────────────────────────────────────────────

def correr_bot() -> None:
    if not TELEGRAM_TOKEN:
        raise SystemExit("Falta TELEGRAM_TOKEN (pedíselo a @BotFather).")
    preparar_base()
    httpx.post(f"{API}/setMyCommands", json={"commands": [
        {"command": "partidos", "description": "Próximos partidos"},
        {"command": "cuotas", "description": "Cuotas + modelo de un partido"},
        {"command": "ficha", "description": "Datos históricos del partido"},
        {"command": "valor", "description": "Picks respaldados por datos"},
        {"command": "arbitraje", "description": "Buscar arbitrajes"},
        {"command": "rendimiento", "description": "Resultados de los picks"},
        {"command": "analisis", "description": "Comentario con IA"},
        {"command": "casas", "description": "Casas y base de datos"},
        {"command": "ayuda", "description": "Cómo usar el bot"},
    ]}, timeout=15)

    if API_FOOTBALL_KEY:
        threading.Thread(target=loop_sync, daemon=True).start()
        print(f"[Bot] Base histórica: se actualiza cada {SYNC_HORAS} hs", flush=True)
    if ALERTAS_MIN > 0 and TELEGRAM_CHAT_ID:
        threading.Thread(target=loop_alertas, daemon=True).start()
        print(f"[Bot] Alertas cada {ALERTAS_MIN} min al chat {TELEGRAM_CHAT_ID}", flush=True)

    print(f"[Bot] Escuchando… casas={CASAS} referencia={REFERENCIA} deporte={DEPORTE} {'(MODO EJEMPLO)' if ES_MOCK else ''}", flush=True)
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
    preparar_base()
    limpiar = lambda t: re.sub(r"</?(b|i|pre|code)>", "", formato.unescape(t))
    for texto in (cmd_partidos(0, []), cmd_cuotas(0, ["1"]), cmd_ficha(0, ["1"]),
                  cmd_valor(0, []), cmd_arbitraje(0, []), cmd_rendimiento(0, [])):
        print(limpiar(texto), "\n" + "─" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente de Cuotas — Mirada Digital")
    parser.add_argument("--prueba", action="store_true", help="muestra un análisis de ejemplo en consola")
    if parser.parse_args().prueba:
        prueba()
    else:
        correr_bot()
