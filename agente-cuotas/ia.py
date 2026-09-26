"""Comentario del partido escrito por Claude a partir de los números ya calculados."""

import json
import os

import anthropic

from analisis import Mercado

MODELO = os.environ.get("CLAUDE_MODEL", "claude-opus-5")

SISTEMA = """Sos el analista de cuotas de un grupo de Telegram en Argentina.
Recibís un JSON con las cuotas de Bet365, Betano y Stake para un partido, métricas del mercado
(mejor cuota, margen, probabilidad justa, arbitrajes) y una ficha armada desde nuestra base histórica:
modelo de goles esperados, forma, cara a cara, estadísticas, bajas, árbitro y clima. También trae los
picks que pasaron el filtro de datos y los que se descartaron, con el motivo.

Escribí un comentario breve (máximo 180 palabras), en español rioplatense, texto plano sin Markdown:
- qué dice el mercado y en qué coincide o difiere el modelo con historial
- los 2 o 3 datos de la ficha que más pesan (forma, bajas, árbitro, clima…)
- si hay pick, por qué los datos lo respaldan y cuál es el riesgo principal; si no hay, decí que conviene no apostar
Usá solo lo que está en el JSON: si la ficha falta o es pobre, decilo. No prometas ganancias."""


def _ficha(ficha) -> dict | None:
    if ficha is None:
        return None
    probs = {s: round(ficha.prob("moneyline", s), 3) for s in ("home", "draw", "away")} if ficha.matriz else None
    return {
        "partidos_en_base": {"local": ficha.n_local, "visitante": ficha.n_visitante},
        "goles_esperados": [round(x, 2) for x in ficha.goles_esperados],
        "prob_modelo_1x2": probs,
        "prob_modelo_mas_2_5": round(ficha.prob("total", "over", "2.5"), 3) if ficha.matriz else None,
        "forma_local": ficha.forma_local, "forma_visitante": ficha.forma_visitante,
        "cara_a_cara": ficha.h2h,
        "stats_local": ficha.stats_local, "stats_visitante": ficha.stats_visitante,
        "arbitro": ficha.arbitro, "amarillas_promedio_liga": ficha.tarjetas_liga,
        "bajas": ficha.bajas, "clima": ficha.clima, "ajustes_del_modelo": ficha.ajustes,
    }


def _pick(p: dict) -> dict:
    return {"mercado": p["mercado"].titulo, "seleccion": p["nombre"], "cuota": p["cuota"], "casa": p["casa"],
            "prob_modelo": p["p_modelo"] and round(p["p_modelo"], 3), "prob_mercado": round(p["p_mercado"], 3),
            **({"confianza": p["confianza"]} if "confianza" in p else {}),
            **({"motivo_descarte": p["motivo"]} if "motivo" in p else {})}


def _resumen(evento: dict, mercados: list[Mercado], ficha=None, picks=(), descartes=()) -> dict:
    return {
        "ficha_historica": _ficha(ficha),
        "picks_aprobados": [_pick(p) for p in picks],
        "descartados": [_pick(p) for p in descartes],
        "partido": f"{evento.get('home_team')} vs {evento.get('away_team')}",
        "liga": evento.get("league"),
        "mercados": [{
            "mercado": m.titulo,
            "cuotas": m.cuotas,
            "resultados": m.nombres,
            "mejor": {s: {"cuota": c, "casa": k} for s, (c, k) in m.mejor.items()},
            "margen_por_casa": {k: round(v, 4) for k, v in m.margenes.items()},
            "prob_justa": {s: round(p, 4) for s, p in m.justa.items()},
            "valor_solo_mercado": m.valor,
            "arbitraje": m.arbitraje,
        } for m in mercados[:6]],
    }


def disponible() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def comentar(evento: dict, mercados: list[Mercado], ficha=None, picks=(), descartes=()) -> str:
    client = anthropic.Anthropic()
    try:
        resp = client.beta.messages.create(
            model=MODELO,
            max_tokens=16000,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SISTEMA,
            messages=[{"role": "user", "content": json.dumps(_resumen(evento, mercados, ficha, picks, descartes),
                                                                  ensure_ascii=False, default=str)}],
        )
    except anthropic.RateLimitError:
        return "La IA está saturada, probá en un minuto."
    except anthropic.APIStatusError as e:
        print(f"[Claude] Error {e.status_code}: {e.message}", flush=True)
        return "No pude generar el análisis con IA ahora."
    except anthropic.APIConnectionError as e:
        print(f"[Claude] Sin conexión: {e}", flush=True)
        return "No pude conectar con la IA ahora."

    if resp.stop_reason == "refusal":
        return "La IA no quiso comentar este partido."
    return "".join(b.text for b in resp.content if b.type == "text").strip()
