#!/usr/bin/env python3
"""
Agente Prospector — Mirada Digital
Encuentra negocios high-ticket, ecommerce y servicios premium para prospectar.

Uso:
  python prospector.py --rubro "coaches de negocios"   --ubicacion "Argentina"
  python prospector.py --rubro "ropa premium"          --ubicacion "Buenos Aires" --tipo ecommerce
  python prospector.py --rubro "consultoras"           --ubicacion "CABA"         --tipo high-ticket
"""

import argparse
import json
import os
import sys

import anthropic
import httpx
from bs4 import BeautifulSoup
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def telegram_send(text: str) -> None:
    """Manda un mensaje a Telegram. Silencioso si no hay credenciales."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        # Telegram limita a 4096 chars por mensaje; cortamos si hace falta
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            httpx.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"},
                timeout=10,
            )
    except Exception:
        pass  # Telegram es best-effort, no corta el agente si falla

# ── Señales de ecommerce y high-ticket ────────────────────────────────────────

ECOMMERCE_SIGNALS = {
    "shopify":      ["cdn.shopify.com", "myshopify.com", "shopify.com/s/files"],
    "tiendanube":   ["tiendanube.com", "nuvemshop.com.br", "d26lpennugtm8s.cloudfront"],
    "woocommerce":  ["woocommerce", "/wp-content/plugins/woocommerce"],
    "mercadoshops": ["mercadoshops.com.ar", "mlstatic.com"],
    "vtex":         ["vtex.com", "vteximg.com.br"],
    "magento":      ["mage/", "Magento_"],
    "prestashop":   ["prestashop", "/modules/"],
}

HIGH_TICKET_SIGNALS = [
    "consultoría", "consultoria", "mentoring", "mentoría", "coaching",
    "programa", "masterclass", "curso intensivo", "retainer",
    "agencia", "estrategia", "transformación", "transformacion",
    "exclusivo", "premium", "vip", "elite", "luxury", "lujo",
    "inversión", "inversion", "desde USD", "desde u$s", "desde $",
    "sesión estratégica", "sesion estrategica", "diagnóstico", "diagnostico",
    "resultado garantizado", "triplicar", "escalar", "multiplicar",
    "inmobiliaria", "propiedades", "real estate",
    "cirugía", "cirugia", "clínica estética", "clinica estetica",
    "odontología", "odontologia", "implantes", "ortodoncia",
    "arquitecto", "interiorismo", "diseño de interiores",
    "abogado", "estudio jurídico", "jurídico",
    "contador", "asesoría contable",
    "financiero", "inversiones", "fondo",
]

AD_PLATFORMS = {
    "meta_pixel":      ["fbq(", "connect.facebook.net", "facebook.net/tr"],
    "google_tag_manager": ["googletagmanager.com", "GTM-"],
    "google_ads":      ["googleadservices.com", "gtag(", "google_conversion"],
    "tiktok_pixel":    ["analytics.tiktok.com", "ttq.load", "tiktok.com/i18n/pixel"],
    "linkedin_insight": ["snap.licdn.com", "linkedin.com/px"],
    "hotjar":          ["hotjar.com", "hjid"],
    "clarity":         ["clarity.ms", "microsoft.com/clarity"],
}


# ── Tools ──────────────────────────────────────────────────────────────────────

def buscar_empresas(rubro: str, ubicacion: str, estrategia: str = "general", cantidad: int = 12) -> list[dict]:
    """
    Busca prospectos en DuckDuckGo con múltiples estrategias de búsqueda.
    estrategia: "general" | "ecommerce" | "high-ticket" | "instagram" | "decision-maker"
    """
    queries = {
        "general":        f"{rubro} {ubicacion} sitio web",
        "ecommerce":      f"tienda online {rubro} {ubicacion} comprar",
        "high-ticket":    f"{rubro} {ubicacion} precio consulta servicio premium",
        "instagram":      f"{rubro} {ubicacion} instagram dueño fundador",
        "decision-maker": f"dueño fundador CEO {rubro} {ubicacion}",
    }
    query = queries.get(estrategia, queries["general"])
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=cantidad * 2):
                results.append({
                    "nombre": r.get("title", ""),
                    "url": r.get("href", ""),
                    "descripcion": r.get("body", ""),
                    "estrategia": estrategia,
                })
                if len(results) >= cantidad:
                    break
    except Exception as e:
        return [{"error": str(e)}]
    return results


def analizar_sitio(url: str) -> dict:
    """
    Analiza el sitio web de un prospecto:
    - Plataforma de ecommerce (Shopify, TiendaNube, WooCommerce, etc.)
    - Señales high-ticket (precios, keywords de servicios premium)
    - Todos los píxeles de tracking instalados
    - Captación de leads (formulario, WhatsApp, chatbot)
    - Indicios del responsable (nombre en el footer, about, team)
    """
    if not url or not url.startswith("http"):
        return {"error": "URL inválida"}
    try:
        resp = httpx.get(url, timeout=12, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"})
        html = resp.text.lower()
        html_original = resp.text
        soup = BeautifulSoup(html_original, "html.parser")

        # Plataforma ecommerce
        plataforma_ecommerce = None
        for plataforma, señales in ECOMMERCE_SIGNALS.items():
            if any(s.lower() in html for s in señales):
                plataforma_ecommerce = plataforma
                break

        # Señales high-ticket en el texto visible
        texto_visible = soup.get_text(" ", strip=True).lower()
        señales_ht = [s for s in HIGH_TICKET_SIGNALS if s in texto_visible]

        # Tracking pixels
        tracking = {}
        for plataforma, patrones in AD_PLATFORMS.items():
            tracking[plataforma] = any(p.lower() in html for p in patrones)

        # Captación
        tiene_formulario = bool(soup.find("form"))
        tiene_whatsapp = "wa.me" in html or "api.whatsapp" in html
        tiene_chatbot = any(k in html for k in ["tawk.to", "tidio", "crisp.chat", "intercom"])
        tiene_calendario = any(k in html for k in ["calendly", "cal.com", "tidycal", "acuityscheduling"])

        # Descripción meta
        meta_desc = soup.find("meta", attrs={"name": "description"})
        descripcion = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""

        # Responsable (buscar en about, equipo, footer)
        responsable_hint = ""
        for tag in soup.find_all(["title", "h1", "h2", "p"])[:30]:
            text = tag.get_text(strip=True)
            if any(k in text.lower() for k in ["fundad", "ceo", "director", "co-founder", "dueñ", "creado por"]):
                responsable_hint = text[:120]
                break

        gaps_tracking = [k for k, v in tracking.items() if not v]

        return {
            "url": resp.url.__str__(),
            "status": resp.status_code,
            "descripcion_meta": descripcion[:250],
            "tipo_negocio": {
                "es_ecommerce": plataforma_ecommerce is not None,
                "plataforma_ecommerce": plataforma_ecommerce,
                "señales_high_ticket": señales_ht[:6],
            },
            "tracking": tracking,
            "gaps_tracking": gaps_tracking,
            "captacion": {
                "formulario": tiene_formulario,
                "whatsapp": tiene_whatsapp,
                "chatbot": tiene_chatbot,
                "calendario": tiene_calendario,
            },
            "responsable_hint": responsable_hint,
        }
    except Exception as e:
        return {"url": url, "error": str(e)}


# ── Tool definitions ───────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "buscar_empresas",
        "description": (
            "Busca prospectos usando DuckDuckGo con distintas estrategias. "
            "Usar múltiples estrategias para el mismo rubro da mejores resultados: "
            "'general', 'ecommerce', 'high-ticket', 'instagram', 'decision-maker'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "rubro": {"type": "string", "description": "Tipo de negocio, ej: coaches de negocios"},
                "ubicacion": {"type": "string", "description": "País, ciudad o zona"},
                "estrategia": {
                    "type": "string",
                    "enum": ["general", "ecommerce", "high-ticket", "instagram", "decision-maker"],
                    "description": "Estrategia de búsqueda",
                },
                "cantidad": {"type": "integer", "description": "Resultados a buscar (default 12)"},
            },
            "required": ["rubro", "ubicacion"],
        },
    },
    {
        "name": "analizar_sitio",
        "description": (
            "Analiza el sitio web de un prospecto: detecta plataforma de ecommerce "
            "(Shopify, TiendaNube, etc.), señales high-ticket, píxeles de tracking instalados, "
            "herramientas de captación de leads, e indicios del responsable del negocio."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL completa del sitio"},
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


# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sos un agente de prospección para Mirada Digital, agencia de performance digital argentina.
Tu especialidad: encontrar negocios que facturan bien pero invierten mal (o nada) en publicidad digital.

═══════════════════════════════════════════════════════
PERFILES QUE MÁS CONVIERTEN PARA MIRADA DIGITAL
═══════════════════════════════════════════════════════

1. ECOMMERCE activo (tiene tienda online)
   → Prioridad máxima si NO tiene Meta Pixel o Google Ads
   → Oportunidad: "estás vendiendo a ciegas, no sabés qué anuncio te trae cada venta"
   → Detectar: Shopify, TiendaNube, WooCommerce, MercadoShops

2. SERVICIOS HIGH-TICKET (coaching, consultoría, clínicas, inmobiliarias, abogados, arquitectos)
   → Alta facturación por cliente → ROI publicitario muy alto
   → Prioridad si no tienen Meta Pixel ni Google Ads
   → Oportunidad: "con un solo cliente nuevo la pauta se paga sola"

3. NEGOCIOS CON INSTAGRAM ACTIVO pero sin pauta
   → Ya tienen audiencia, falta convertirla en ventas
   → Oportunidad: "tenés comunidad, te falta el sistema para monetizarla"

4. NEGOCIOS SIN SITIO WEB O CON SITIO DESACTUALIZADO
   → Oportunidad: "en 2025 tu web es tu vendedor 24/7"

═══════════════════════════════════════════════════════
PROCESO OBLIGATORIO
═══════════════════════════════════════════════════════

Paso 1 — Búsqueda múltiple:
  Llamá buscar_empresas al menos 2 veces con estrategias distintas (ej: "high-ticket" + "ecommerce")
  para el mismo rubro. Así obtenés diversidad de prospectos.

Paso 2 — Análisis de sitios:
  Analizá todos los candidatos que tengan URL válida.

Paso 3 — Scoring y selección:
  Seleccioná la cantidad de prospectos que te pidieron (indicado en el mensaje del usuario) usando esta lógica:

  Score base (suma):
  +3 → es ecommerce activo
  +2 → servicios high-ticket detectados
  +2 → NO tiene Meta Pixel (máxima brecha en Argentina)
  +2 → NO tiene Google Ads
  +1 → NO tiene GTM
  +1 → NO tiene formulario ni WhatsApp (sin captación de leads)
  -1 → tiene todos los píxeles (ya está bien configurado, baja oportunidad)

Paso 4 — Output por prospecto:
  Para cada prospecto de la lista final:

  ┌─────────────────────────────────────────────────┐
  │ #N  NOMBRE DEL NEGOCIO                          │
  │ URL: https://...                                │
  │ Tipo: Ecommerce (TiendaNube) / High-ticket / ... │
  │ Score: X/10                                     │
  │                                                 │
  │ DIAGNÓSTICO (2 líneas):                         │
  │ Tiene/No tiene: [lista de píxeles]              │
  │ Brecha principal: [1 línea]                     │
  │                                                 │
  │ MENSAJE DE OUTREACH:                            │
  │ [Texto listo para copiar a WhatsApp o IG DM]    │
  └─────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════
CÓMO ESCRIBIR EL MENSAJE DE OUTREACH
═══════════════════════════════════════════════════════

- Máximo 3 párrafos
- Tono: cercano, argentino, directo. NO corporativo.
- Primer párrafo: mostrá que investigaste su negocio (mencioná algo concreto)
- Segundo párrafo: señalá UNA brecha específica que detectaste (usar los datos reales del análisis)
- Tercer párrafo: propuesta de auditoría gratuita sin compromiso
- NO uses plantillas genéricas. Cada mensaje tiene que sonar escrito a mano.
- NO menciones que sos un bot o que usás IA.
- Firmá como: "Valencia — Mirada Digital"

═══════════════════════════════════════════════════════
CERRAR CON TABLA RESUMEN
═══════════════════════════════════════════════════════

Al final mostrá una tabla con los 10 prospectos ordenados por score:
| # | Nombre | Tipo | Score | Brecha principal |
"""


# ── Agent loop ─────────────────────────────────────────────────────────────────

def run_agent(rubro: str, ubicacion: str, tipo: str = "auto", cantidad: int = 10):
    print(f"\n🔍  Prospectando: {rubro}  |  {ubicacion}  |  modo: {tipo}  |  cantidad: {cantidad}\n")
    print("─" * 60)
    telegram_send(
        f"🔍 *Mirada Digital — Agente Prospector*\n"
        f"Buscando: *{rubro}* en *{ubicacion}*\n"
        f"Modo: {tipo} | Prospectos: {cantidad}\n"
        f"_Esto puede tardar {2 + cantidad // 10}-{4 + cantidad // 10} minutos..._"
    )

    tipo_hint = ""
    if tipo == "ecommerce":
        tipo_hint = (
            " Modo ECOMMERCE: el rubro es secundario, lo que importa es el ESTADO DIGITAL."
            " Buscá tiendas online de cualquier categoría: indumentaria, calzado, cosmética, mascotas,"
            " hogar, deportes, electrónica, alimentos, juguetes, librería — lo que sea."
            " El criterio de selección es: tiene tienda online activa (Shopify, TiendaNube, WooCommerce, etc.)"
            " pero le faltan píxeles de tracking o publicidad paga. Eso es todo lo que necesitás para priorizarlo."
            " Usá estrategias de búsqueda variadas: 'ecommerce', 'general', 'decision-maker'."
        )
    elif tipo == "high-ticket":
        tipo_hint = " Enfocate en servicios de alto valor: coaches, consultores, clínicas, inmobiliarias."

    messages = [
        {
            "role": "user",
            "content": (
                f"Prospectá el rubro '{rubro}' en '{ubicacion}'.{tipo_hint} "
                f"Usá al menos 3 estrategias de búsqueda distintas, analizá todos los sitios que puedas "
                f"y entregame los {cantidad} mejores prospectos con su mensaje de outreach personalizado."
            ),
        }
    ]

    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        tool_uses = []
        text_blocks = []
        for block in response.content:
            if block.type == "tool_use":
                tool_uses.append(block)
            elif block.type == "text":
                text_blocks.append(block.text)

        for text in text_blocks:
            if text.strip():
                print(text)
                telegram_send(text)

        if response.stop_reason == "end_turn" or not tool_uses:
            break

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for tool_use in tool_uses:
            tool_name = tool_use.name
            tool_input = tool_use.input
            print(f"\n⚙️  {tool_name}({json.dumps(tool_input, ensure_ascii=False, separators=(',',':'))})")

            result = ejecutar_herramienta(tool_name, tool_input)

            if tool_name == "buscar_empresas":
                count = len(result) if isinstance(result, list) else 0
                print(f"   → {count} candidatos")
            elif tool_name == "analizar_sitio":
                if isinstance(result, dict) and "tracking" in result:
                    es_ec = result.get("tipo_negocio", {}).get("es_ecommerce")
                    plat = result.get("tipo_negocio", {}).get("plataforma_ecommerce", "")
                    gaps = result.get("gaps_tracking", [])
                    tipo_tag = f"[ecommerce:{plat}]" if es_ec else "[servicio]"
                    print(f"   → {tipo_tag}  gaps: {', '.join(gaps) if gaps else 'ninguno'}")
                elif isinstance(result, dict) and "error" in result:
                    print(f"   → ⚠ {result['error'][:60]}")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(result, ensure_ascii=False, indent=2),
            })

        messages.append({"role": "user", "content": tool_results})

    print("\n" + "─" * 60)
    print("✅ Prospección completada\n")
    telegram_send("✅ *Prospección completada.* Copiá el mensaje del prospecto que más te guste y mandáselo.")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Agente Prospector — Mirada Digital",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python prospector.py --rubro "coaches de negocios" --ubicacion "Argentina"
  python prospector.py --rubro "ropa de mujer" --ubicacion "Buenos Aires" --tipo ecommerce
  python prospector.py --rubro "clínicas estéticas" --ubicacion "CABA" --tipo high-ticket
  python prospector.py --rubro "inmobiliarias" --ubicacion "Rosario"
        """,
    )
    parser.add_argument("--rubro", required=True, help="Tipo de negocio a prospectar")
    parser.add_argument("--ubicacion", required=True, help="País, ciudad o zona")
    parser.add_argument(
        "--tipo",
        choices=["auto", "ecommerce", "high-ticket"],
        default="auto",
        help="Foco de prospección (default: auto)",
    )
    parser.add_argument(
        "--cantidad",
        type=int,
        default=10,
        help="Cantidad de prospectos a generar (default: 10)",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ Falta la variable de entorno ANTHROPIC_API_KEY")
        sys.exit(1)

    run_agent(args.rubro, args.ubicacion, args.tipo, args.cantidad)


if __name__ == "__main__":
    main()
