#!/usr/bin/env python3
"""
Agente Prospector — Mirada Digital
Encuentra empresas en un rubro/ubicación y genera mensajes de outreach personalizados.

Uso:
  python prospector.py --rubro "restaurantes" --ubicacion "Buenos Aires"
  python prospector.py --rubro "gimnasios" --ubicacion "Palermo, CABA"
"""

import argparse
import json
import os
import sys

import anthropic
import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── Tools ──────────────────────────────────────────────────────────────────────

def buscar_empresas(rubro: str, ubicacion: str, cantidad: int = 10) -> list[dict]:
    """DuckDuckGo search para encontrar empresas locales."""
    query = f"{rubro} {ubicacion} contacto sitio web"
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=cantidad * 2):
                results.append({
                    "nombre": r.get("title", ""),
                    "url": r.get("href", ""),
                    "descripcion": r.get("body", ""),
                })
                if len(results) >= cantidad:
                    break
    except Exception as e:
        return [{"error": str(e)}]
    return results


def analizar_sitio(url: str) -> dict:
    """Fetches a website and checks for tracking pixels and digital presence signals."""
    if not url or not url.startswith("http"):
        return {"error": "URL inválida"}
    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0"})
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        tiene_meta_pixel = "fbq(" in html or "connect.facebook.net" in html
        tiene_gtm = "googletagmanager.com" in html or "GTM-" in html
        tiene_tiktok_pixel = "analytics.tiktok.com" in html or "ttq.load" in html
        tiene_google_ads = "googleadservices.com" in html or "gtag(" in html

        tiene_formulario = bool(soup.find("form"))
        tiene_whatsapp = "wa.me" in html or "api.whatsapp" in html
        meta_desc = soup.find("meta", attrs={"name": "description"})
        descripcion = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""

        return {
            "url": url,
            "status": resp.status_code,
            "descripcion_meta": descripcion[:200],
            "tracking": {
                "meta_pixel": tiene_meta_pixel,
                "google_tag_manager": tiene_gtm,
                "tiktok_pixel": tiene_tiktok_pixel,
                "google_ads": tiene_google_ads,
            },
            "presencia": {
                "tiene_formulario": tiene_formulario,
                "tiene_whatsapp": tiene_whatsapp,
            },
        }
    except Exception as e:
        return {"url": url, "error": str(e)}


# ── Tool dispatcher ────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "buscar_empresas",
        "description": (
            "Busca empresas de un rubro en una ubicación usando DuckDuckGo. "
            "Devuelve nombre, URL y descripción de cada resultado."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "rubro": {"type": "string", "description": "Tipo de negocio, ej: restaurantes"},
                "ubicacion": {"type": "string", "description": "Ciudad o zona, ej: Palermo CABA"},
                "cantidad": {"type": "integer", "description": "Resultados a buscar (default 10)", "default": 10},
            },
            "required": ["rubro", "ubicacion"],
        },
    },
    {
        "name": "analizar_sitio",
        "description": (
            "Analiza el sitio web de una empresa: detecta Meta Pixel, GTM, TikTok Pixel, "
            "Google Ads, presencia de formularios y WhatsApp."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL completa del sitio a analizar"},
            },
            "required": ["url"],
        },
    },
]


def ejecutar_herramienta(nombre: str, inputs: dict):
    if nombre == "buscar_empresas":
        return buscar_empresas(**inputs)
    elif nombre == "analizar_sitio":
        return analizar_sitio(**inputs)
    return {"error": f"Herramienta desconocida: {nombre}"}


# ── Agent loop ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sos un agente de prospección para Mirada Digital, una agencia de performance digital argentina.

Tu misión: dado un rubro y ubicación, encontrá 10 empresas que podrían beneficiarse de publicidad digital y generá un mensaje de outreach personalizado para cada una.

Proceso:
1. Usá buscar_empresas para obtener candidatos
2. Para cada candidato que tenga URL, usá analizar_sitio para detectar su estado digital
3. Evaluá señales de oportunidad:
   - Sin Meta Pixel → no están midiendo su publicidad en Facebook/Instagram
   - Sin GTM → setup de tracking deficiente
   - Sin Google Ads → no están en búsquedas de Google
   - Sin TikTok Pixel → no aprovechan TikTok Ads
   - Sin formulario ni WhatsApp → no tienen captación de leads
4. Generá para cada empresa:
   - Nombre y URL
   - Score de oportunidad (1-10, mayor = más probable de necesitar ayuda)
   - Diagnóstico breve (2 líneas máximo)
   - Mensaje de outreach para WhatsApp o Instagram DM (máximo 3 párrafos, tono cercano y argentino, sin ser invasivo)

El mensaje debe:
- Mencionar algo específico de su negocio (no genérico)
- Señalar una brecha concreta que Mirada Digital puede resolver
- Terminar con una propuesta de auditoría gratuita
- Sonar natural, no como template

Presentá los resultados como una lista clara y accionable."""


def run_agent(rubro: str, ubicacion: str):
    print(f"\n🔍 Buscando prospectos: {rubro} en {ubicacion}\n")
    print("─" * 60)

    messages = [
        {
            "role": "user",
            "content": f"Buscá prospectos en el rubro '{rubro}' en '{ubicacion}'. Analizá al menos 8 empresas y generá mensajes de outreach para las 10 mejores oportunidades.",
        }
    ]

    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=8000,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Collect tool uses and text from this response
        tool_uses = []
        text_blocks = []

        for block in response.content:
            if block.type == "tool_use":
                tool_uses.append(block)
            elif block.type == "text":
                text_blocks.append(block.text)

        # Print any text output
        for text in text_blocks:
            if text.strip():
                print(text)

        # If no tool calls, we're done
        if response.stop_reason == "end_turn" or not tool_uses:
            break

        # Execute tools and build tool results
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for tool_use in tool_uses:
            tool_name = tool_use.name
            tool_input = tool_use.input
            print(f"\n⚙️  {tool_name}({json.dumps(tool_input, ensure_ascii=False)})")

            result = ejecutar_herramienta(tool_name, tool_input)
            result_text = json.dumps(result, ensure_ascii=False, indent=2)

            if tool_name == "buscar_empresas":
                count = len(result) if isinstance(result, list) else 0
                print(f"   → {count} resultados encontrados")
            elif tool_name == "analizar_sitio":
                if isinstance(result, dict) and "tracking" in result:
                    gaps = [k for k, v in result["tracking"].items() if not v]
                    print(f"   → Gaps detectados: {', '.join(gaps) if gaps else 'ninguno'}")
                elif "error" in (result or {}):
                    print(f"   → Error: {result['error']}")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result_text,
            })

        messages.append({"role": "user", "content": tool_results})

    print("\n" + "─" * 60)
    print("✅ Prospección completada")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agente Prospector — Mirada Digital")
    parser.add_argument("--rubro", required=True, help="Tipo de negocio a prospectar")
    parser.add_argument("--ubicacion", required=True, help="Ciudad o zona geográfica")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ Falta la variable ANTHROPIC_API_KEY")
        sys.exit(1)

    run_agent(args.rubro, args.ubicacion)


if __name__ == "__main__":
    main()
