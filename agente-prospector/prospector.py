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
import time

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
    """Manda un mensaje a Telegram. Loguea errores en vez de ignorarlos."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] Sin credenciales — mensaje no enviado", flush=True)
        return
    try:
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            # Markdown puede romper si el texto tiene caracteres especiales — fallback a texto plano
            for parse_mode in ["Markdown", None]:
                payload = {"chat_id": TELEGRAM_CHAT_ID, "text": chunk}
                if parse_mode:
                    payload["parse_mode"] = parse_mode
                r = httpx.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json=payload,
                    timeout=15,
                )
                if r.status_code == 200:
                    break
                if parse_mode:
                    continue  # reintentar sin Markdown
                print(f"[Telegram] Error {r.status_code}: {r.text[:200]}", flush=True)
    except Exception as e:
        print(f"[Telegram] Excepción: {e}", flush=True)

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
        # Extraer link real de WhatsApp si existe
        whatsapp_link = ""
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "wa.me" in href or "api.whatsapp.com" in href:
                whatsapp_link = href.split("?")[0]  # sin el mensaje pre-cargado
                break
        if not whatsapp_link and ("wa.me" in html or "api.whatsapp" in html):
            import re
            m = re.search(r'(https?://(?:wa\.me|api\.whatsapp\.com/send)[^\s"\'&>]+)', html_original)
            if m:
                whatsapp_link = m.group(1).split("?")[0]
        tiene_whatsapp = bool(whatsapp_link)
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
                "whatsapp_link": whatsapp_link,
                "chatbot": tiene_chatbot,
                "calendario": tiene_calendario,
            },
            "responsable_hint": responsable_hint,
        }
    except Exception as e:
        return {"url": url, "error": str(e)}


def _extraer_nombre_responsable_del_sitio(url: str) -> str:
    """
    Intenta extraer el nombre real del dueño/fundador desde páginas internas del sitio
    (about, equipo, nosotros, team, quienes-somos, blog author, etc.)
    Devuelve el nombre si lo encuentra, string vacío si no.
    """
    if not url or not url.startswith("http"):
        return ""
    base = url.rstrip("/")
    slugs = ["about", "nosotros", "quienes-somos", "quiénes-somos", "equipo",
             "team", "sobre-nosotros", "sobre-mi", "sobre-mí", "founder", "acerca"]
    keywords_nombre = ["fundad", "ceo", "director", "co-founder", "dueñ", "creado por",
                       "founder", "propietari", "socio", "presidente"]
    import re

    def _buscar_en_html(html_orig: str) -> str:
        soup2 = BeautifulSoup(html_orig, "html.parser")
        # Buscar en meta og:title, author, schema.org Person
        for meta in soup2.find_all("meta"):
            name_attr = (meta.get("name") or meta.get("property") or "").lower()
            if "author" in name_attr:
                val = meta.get("content", "").strip()
                if val and len(val.split()) <= 5:
                    return val
        # Buscar en JSON-LD schema.org
        for script in soup2.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    data = data[0]
                # Person schema
                if data.get("@type") == "Person":
                    return data.get("name", "")
                # founder dentro de Organization
                founder = data.get("founder") or data.get("author")
                if isinstance(founder, dict):
                    return founder.get("name", "")
                if isinstance(founder, str):
                    return founder
            except Exception:
                pass
        # Buscar en headings y párrafos con keywords
        for tag in soup2.find_all(["h1", "h2", "h3", "p", "span"])[:60]:
            text = tag.get_text(strip=True)
            if any(k in text.lower() for k in keywords_nombre) and len(text) < 150:
                # Intentar extraer solo el nombre (primeras 2-4 palabras tipo nombre propio)
                m = re.search(r'\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\b', text)
                if m:
                    return m.group(1)
        return ""

    # Primero intentar en la homepage
    try:
        resp = httpx.get(base, timeout=10, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"})
        nombre = _buscar_en_html(resp.text)
        if nombre:
            return nombre
    except Exception:
        pass

    # Luego intentar páginas internas
    for slug in slugs:
        try:
            r = httpx.get(f"{base}/{slug}", timeout=8, follow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"})
            if r.status_code == 200:
                nombre = _buscar_en_html(r.text)
                if nombre:
                    return nombre
        except Exception:
            continue
    return ""


def _validar_candidato_ig(handle: str, titulo: str, descripcion: str,
                           nombre_empresa: str, nombre_responsable: str) -> int:
    """
    Devuelve un score de validez (0-10) para un candidato de Instagram.
    Filtra falsos positivos: perfiles extranjeros, cuentas de empresa, nombres sin match.
    """
    score = 0
    texto = f"{titulo} {descripcion}".lower()
    nombre_emp_lower = nombre_empresa.lower()
    nombre_resp_lower = nombre_responsable.lower()

    # Señales positivas
    if nombre_resp_lower and any(p in texto for p in nombre_resp_lower.split()):
        score += 4  # el nombre del responsable aparece en el perfil
    if nombre_emp_lower[:8] in texto:
        score += 2  # el nombre del negocio aparece en el perfil
    if any(k in texto for k in ["argentina", "buenos aires", "caba", "arg", " ar "]):
        score += 2  # perfil argentino
    if any(k in texto for k in ["fundador", "founder", "ceo", "dueño", "director", "emprendedor"]):
        score += 2  # el perfil se identifica como responsable

    # Señales negativas (falsos positivos comunes)
    if any(k in texto for k in ["official", "fanpage", "fan page", "página oficial"]):
        score -= 3  # cuenta oficial/fanpage, no personal
    if handle.lower() in nombre_emp_lower.replace(" ", ""):
        score -= 2  # el handle coincide con el nombre del negocio → es la cuenta del negocio
    if any(k in texto for k in ["españa", "mexico", "chile", "colombia", "peru", "miami", "usa", "madrid", "barcelona"]):
        score -= 3  # perfil extranjero

    return max(0, score)


def buscar_responsable(nombre_empresa: str, url: str = "") -> dict:
    """
    Busca el dueño, fundador o director de una empresa en dos pasos:
    1. Extrae el nombre real desde el sitio web (about, schema.org, meta author)
    2. Busca ese nombre en Instagram y LinkedIn con queries específicos
    Filtra falsos positivos con scoring de validez.
    """
    dominio = url.replace("https://", "").replace("http://", "").split("/")[0] if url else ""

    # Paso 1: intentar extraer nombre desde el sitio
    nombre_responsable = ""
    if url:
        nombre_responsable = _extraer_nombre_responsable_del_sitio(url)

    # Paso 2: armar queries específicos según si tenemos nombre o no
    queries = []
    if nombre_responsable:
        queries += [
            f'"{nombre_responsable}" instagram.com Argentina',
            f'"{nombre_responsable}" site:instagram.com',
            f'"{nombre_responsable}" linkedin.com/in',
        ]
    # Queries genéricos como fallback
    queries += [
        f'"{nombre_empresa}" dueño OR fundador OR CEO site:instagram.com Argentina',
        f'"{nombre_empresa}" fundador OR founder linkedin.com/in',
        f'dueño "{nombre_empresa}" Argentina instagram',
    ]
    if dominio:
        queries.append(f'site:{dominio} fundador OR dueño OR CEO OR "sobre mí"')

    candidatos = []
    try:
        with DDGS() as ddgs:
            for query in queries:
                for r in ddgs.text(query, max_results=5):
                    href = r.get("href", "")
                    body = r.get("body", "")
                    title = r.get("title", "")

                    es_ig = "instagram.com" in href
                    es_li = "linkedin.com/in" in href
                    if not (es_ig or es_li):
                        continue

                    handle_ig = ""
                    if es_ig:
                        partes = href.rstrip("/").split("/")
                        handle = partes[-1] if partes else ""
                        invalidos = {"instagram.com", "p", "reel", "stories", "explore",
                                     "accounts", "tv", "share", "reels"}
                        if handle and handle not in invalidos and not handle.startswith("_"):
                            handle_ig = f"@{handle}"
                        else:
                            continue  # URL de IG sin handle válido, ignorar

                    # Calcular score de validez
                    validez = 0
                    if es_ig and handle_ig:
                        validez = _validar_candidato_ig(
                            handle_ig, title, body, nombre_empresa, nombre_responsable
                        )
                        if validez < 1:
                            continue  # falso positivo muy probable

                    candidatos.append({
                        "fuente": "instagram" if es_ig else "linkedin",
                        "url": href,
                        "handle_ig": handle_ig,
                        "titulo": title[:80],
                        "descripcion": body[:120],
                        "validez": validez,
                    })

                if len(candidatos) >= 5:
                    break
    except Exception as e:
        return {"error": str(e), "nombre_encontrado_en_sitio": nombre_responsable, "candidatos": []}

    # Ordenar por validez descendente
    candidatos.sort(key=lambda c: c.get("validez", 0), reverse=True)

    ig_personales = [c for c in candidatos if c["fuente"] == "instagram" and c["handle_ig"]]
    linkedin = [c for c in candidatos if c["fuente"] == "linkedin"]

    # Determinar confianza
    mejor_ig = ig_personales[0] if ig_personales else None
    mejor_li = linkedin[0] if linkedin else None

    if mejor_ig and mejor_ig.get("validez", 0) >= 4:
        confianza = "alta"
    elif mejor_ig and mejor_ig.get("validez", 0) >= 2:
        confianza = "media"
    elif mejor_li or nombre_responsable:
        confianza = "media"
    else:
        confianza = "baja"

    return {
        "empresa": nombre_empresa,
        "nombre_encontrado_en_sitio": nombre_responsable,
        "instagram_responsable": mejor_ig,
        "linkedin_responsable": mejor_li,
        "confianza": confianza,
        "todos_los_candidatos": candidatos[:5],
    }


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
    {
        "name": "buscar_responsable",
        "description": (
            "Busca al dueño, fundador o director de una empresa. "
            "Devuelve su Instagram personal y/o LinkedIn si los encuentra. "
            "Usá esta herramienta para cada prospecto seleccionado — el outreach va al responsable, "
            "no a la cuenta del negocio."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre_empresa": {"type": "string", "description": "Nombre del negocio"},
                "url": {"type": "string", "description": "URL del sitio (ayuda a afinar la búsqueda)"},
            },
            "required": ["nombre_empresa"],
        },
    },
]


def ejecutar_herramienta(nombre: str, inputs: dict):
    if nombre == "buscar_empresas":
        return buscar_empresas(**inputs)
    elif nombre == "analizar_sitio":
        return analizar_sitio(**inputs)
    elif nombre == "buscar_responsable":
        return buscar_responsable(**inputs)
    return {"error": f"Herramienta desconocida: {nombre}"}


# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sos un agente de prospección para Mirada Digital, agencia de performance digital argentina.
Tu especialidad: encontrar negocios que facturan bien pero invierten mal (o nada) en publicidad digital.

═══════════════════════════════════════════════════════
PERFIL DE CLIENTE IDEAL — MIRADA DIGITAL
═══════════════════════════════════════════════════════

Mirada Digital cobra $200-400 USD/mes de gestión + $300-500 USD de setup inicial.
El cliente ideal puede y quiere pagar eso. Filtrá con estos criterios:

TAMAÑO MÍNIMO (necesario para pagar la agencia):
→ Ecommerce: tienda con catálogo real (+50 productos), plataforma seria (Shopify, TiendaNube, VTEX, Magento)
→ Servicios: negocio con 2+ años de historia, precios visibles en el sitio que impliquen ticket alto
→ Señales de volumen: local físico + online, múltiples sucursales, staff visible, reseñas en Google

SEÑALES DE QUE TIENE PRESUPUESTO PARA PAUTA:
→ Ya corre algún anuncio (aunque sea mal configurado) — mejor prospecto que uno que nunca invirtió
→ Tiene Meta Pixel O Google Ads instalado — ya invirtió en setup, entiende el valor
→ Ecommerce con precio promedio visible >$15.000 ARS por producto
→ Servicio con sesión/consulta >$50.000 ARS

DESCARTAR:
→ Directorios, portales, marketplaces (Zonaprop, MercadoLibre, etc.)
→ Negocios sin sitio propio (solo Instagram o solo MercadoLibre)
→ Tiendas con menos de 10 productos o sitio claramente abandonado
→ Franquicias grandes (McDonald's, etc.) — ya tienen agencia
→ Negocios que claramente tienen equipo de marketing interno

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

Paso 3 — Buscar responsable (OBLIGATORIO para cada prospecto seleccionado):
  Llamá buscar_responsable con el nombre y URL de cada prospecto que vayas a incluir.
  El outreach NUNCA va a la cuenta del negocio — siempre al dueño o fundador directamente.
  Si no encontrás responsable con confianza "alta" o "media":
    → Revisá si analizar_sitio devolvió un whatsapp_link — usalo como contacto alternativo.
    → El WhatsApp de un negocio pequeño casi siempre es el del dueño.
    → Si no hay WhatsApp ni responsable verificable, descartá ese prospecto.

Paso 4 — Scoring y selección:
  Seleccioná la cantidad de prospectos que te pidieron (indicado en el mensaje del usuario) usando esta lógica:

  Score base (suma):
  +3 → es ecommerce activo (plataforma detectada)
  +2 → servicios high-ticket detectados
  +2 → NO tiene Meta Pixel → oportunidad: arrancar pauta desde cero
  +2 → NO tiene Google Ads → oportunidad: captura de búsquedas sin competencia
  +1 → NO tiene GTM → tracking deficiente aunque tenga anuncios
  +1 → NO tiene formulario ni WhatsApp → sin captación de leads
  +2 → tiene Meta Pixel O Google Ads pero NO ambos → ya invierte, falta escalar
  +1 → tiene todos los píxeles pero sin GTM → mal configurado, oportunidad de auditoría

  Nota: un ecommerce CON anuncios corriendo NO baja el score. Al contrario:
  ya sabe que los anuncios funcionan y tiene presupuesto — solo necesita una agencia mejor.

Paso 4 — Output por prospecto:
  Para cada prospecto de la lista final:

  ┌─────────────────────────────────────────────────┐
  │ #N  NOMBRE DEL NEGOCIO                          │
  │ Web: https://...                                │
  │ Tipo: Ecommerce (TiendaNube) / High-ticket / ...│
  │ Score: X/10                                     │
  │                                                 │
  │ CONTACTO DIRECTO:                               │
  │ Nombre: [nombre del responsable si se encontró] │
  │ Instagram personal: @handle  (si se encontró)  │
  │ LinkedIn: linkedin.com/in/...  (si aplica)      │
  │ WhatsApp: wa.me/... (si no hay contacto personal│
  │           pero el sitio tiene WhatsApp)          │
  │                                                 │
  │ DIAGNÓSTICO (2 líneas):                         │
  │ Tiene/No tiene: [lista de píxeles]              │
  │ Brecha principal: [1 línea]                     │
  │                                                 │
  │ MENSAJE DE OUTREACH (listo para copiar):        │
  │ [Dirigido al responsable por nombre si lo tenés]│
  └─────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════
CÓMO ESCRIBIR EL MENSAJE DE OUTREACH
═══════════════════════════════════════════════════════

- Máximo 3 párrafos
- Tono: cercano, argentino, directo. NO corporativo.
- Si tenés el nombre del responsable, arrancá con "Hola [nombre]!" — nunca "Hola [nombre del negocio]!"
- Primer párrafo: mostrá que investigaste su negocio (mencioná algo concreto)
- Segundo párrafo: señalá UNA brecha específica basada en el análisis real:
    → Sin pixel ni anuncios: "estás vendiendo sin saber qué funciona"
    → Tiene anuncios pero mal tracking: "estás invirtiendo plata sin poder medir el resultado real"
    → Tiene pixel y anuncios: "con una auditoría te mostramos dónde se está escapando el presupuesto"
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
            " Modo ECOMMERCE: el rubro es secundario, lo que importa es que tenga tienda online activa."
            " Buscá tiendas de cualquier categoría: indumentaria, calzado, cosmética, mascotas,"
            " hogar, deportes, electrónica, alimentos, juguetes, librería — lo que sea."
            " CUALQUIER ecommerce activo es prospecto válido, con o sin píxeles, con o sin anuncios corriendo."
            " Si no tiene píxeles: oportunidad de arrancar desde cero."
            " Si ya tiene anuncios: oportunidad de mejorar performance y tomar la cuenta."
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
        # Reintento automático si hay rate limit
        for intento in range(4):
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=8000,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                )
                break
            except anthropic.RateLimitError:
                espera = 30 * (intento + 1)
                print(f"⏳ Rate limit — esperando {espera}s...", flush=True)
                time.sleep(espera)
        else:
            print("❌ Rate limit persistente, abortando.", flush=True)
            break

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

            # Recortar resultados grandes para no exceder rate limit de tokens
            if tool_name == "buscar_empresas" and isinstance(result, list):
                result = result[:8]
                for r in result:
                    if "descripcion" in r:
                        r["descripcion"] = r["descripcion"][:100]

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
            elif tool_name == "buscar_responsable":
                if isinstance(result, dict):
                    confianza = result.get("confianza", "baja")
                    ig = result.get("instagram_responsable")
                    handle = ig.get("handle_ig", "") if ig else ""
                    li = result.get("linkedin_responsable")
                    if handle:
                        print(f"   → 👤 {handle}  [{confianza}]")
                    elif li:
                        print(f"   → 👤 LinkedIn encontrado  [{confianza}]")
                    else:
                        print(f"   → ⚠ Responsable no encontrado  [{confianza}]")

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
