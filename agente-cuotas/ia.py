"""Comentario del partido escrito por Claude a partir de los números ya calculados."""

import json
import os

import anthropic

from analisis import Mercado

MODELO = os.environ.get("CLAUDE_MODEL", "claude-opus-5")

SISTEMA = """Sos el analista de cuotas de un grupo de Telegram en Argentina.
Recibís las cuotas de Bet365, Betano y Stake para un partido y métricas ya calculadas
(mejor cuota, margen de cada casa, probabilidad justa de consenso, apuestas con valor, arbitrajes).

Escribí un comentario breve (máximo 150 palabras), en español rioplatense, texto plano sin Markdown:
- qué dice el mercado (favorito, probabilidades)
- qué casa paga mejor y cuál tiene más margen
- si hay valor o arbitraje, explicalo en una línea, con sus riesgos
No inventes datos que no estén en el JSON (lesiones, forma, etc.). No prometas ganancias."""


def _resumen(evento: dict, mercados: list[Mercado]) -> dict:
    return {
        "partido": f"{evento.get('home_team')} vs {evento.get('away_team')}",
        "liga": evento.get("league"),
        "mercados": [{
            "mercado": m.titulo,
            "cuotas": m.cuotas,
            "resultados": m.nombres,
            "mejor": {s: {"cuota": c, "casa": k} for s, (c, k) in m.mejor.items()},
            "margen_por_casa": {k: round(v, 4) for k, v in m.margenes.items()},
            "prob_justa": {s: round(p, 4) for s, p in m.justa.items()},
            "valor": m.valor,
            "arbitraje": m.arbitraje,
        } for m in mercados[:6]],
    }


def disponible() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def comentar(evento: dict, mercados: list[Mercado]) -> str:
    client = anthropic.Anthropic()
    try:
        resp = client.beta.messages.create(
            model=MODELO,
            max_tokens=16000,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SISTEMA,
            messages=[{"role": "user", "content": json.dumps(_resumen(evento, mercados), ensure_ascii=False)}],
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
