import cairosvg, os

OUT = "/home/user/MIRADA-DIGITAL/brand/highlights/stories"
os.makedirs(OUT, exist_ok=True)

NAVY, CYAN, WHITE, GREEN, GRAY = "#0D1B2A","#00D4FF","#FFFFFF","#00E676","#8892A4"
W, H = 1080, 1920

# ── primitives ─────────────────────────────────────────────────────────────

def render(name, *parts):
    body = "\n".join(p for p in parts if p)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}">'
           f'<rect width="{W}" height="{H}" fill="{NAVY}"/>'
           f'{body}</svg>')
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{OUT}/{name}",
                     output_width=W, output_height=H)
    print(f"  ✓ {name}")

def t(x, y, s, sz=60, c=WHITE, w=700, anchor="start", ls=0, op=1):
    return (f'<text x="{x}" y="{y}" font-family="Liberation Sans,Arial,sans-serif" '
            f'font-weight="{w}" font-size="{sz}" fill="{c}" text-anchor="{anchor}" '
            f'letter-spacing="{ls}" opacity="{op}">{s}</text>')

def hr(y, c=CYAN, op=0.18, x1=80, x2=1000):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{c}" stroke-width="1.5" opacity="{op}"/>'

def accent(y, w=80):
    return f'<rect x="80" y="{y}" width="{w}" height="6" rx="3" fill="{CYAN}"/>'

def pill(x, y, label, c=CYAN):
    chars = len(label)
    pw = chars * 22 + 40
    return (f'<rect x="{x}" y="{y-36}" width="{pw}" height="52" rx="26" '
            f'fill="{c}" opacity="0.15"/>'
            f'<rect x="{x}" y="{y-36}" width="{pw}" height="52" rx="26" '
            f'fill="none" stroke="{c}" stroke-width="1.5"/>'
            f'{t(x+20, y, label, 28, c, 500, ls=3)}')

def big_bg(x, y, s, sz=400, c=CYAN, op=0.04):
    return t(x, y, s, sz, c, 700, "middle", op=op)

def eye(cx, cy, r=90):
    ru = r * 55/45;  rl = r * 80/45;  ri = r * 15/45
    iy = cy - r*4/45
    sw = max(3, r*2.5/45)
    return (f'<path d="M {cx-r},{cy} A {ru},{ru} 0 0,1 {cx+r},{cy} '
            f'A {rl},{rl} 0 0,0 {cx-r},{cy} Z" '
            f'fill="none" stroke="{CYAN}" stroke-width="{sw:.1f}" stroke-linejoin="round"/>'
            f'<circle cx="{cx}" cy="{iy:.1f}" r="{ri:.1f}" '
            f'fill="{NAVY}" stroke="{CYAN}" stroke-width="{max(2.5,sw*0.8):.1f}"/>')

def num_step(x, y, n, title, *desc_lines):
    parts = [
        f'<circle cx="{x+36}" cy="{y+10}" r="36" fill="none" stroke="{CYAN}" stroke-width="3" opacity="0.4"/>',
        t(x+36, y+26, str(n), 52, CYAN, 700, "middle"),
        t(x+96, y+26, title, 56, WHITE, 700),
    ]
    for i, d in enumerate(desc_lines):
        parts.append(t(x+96, y+26+62*(i+1), d, 40, GRAY, 400))
    return "\n".join(parts)

def hdr(label, cur, tot):
    return ""  # counter removed

def ftr():
    return "\n".join([hr(1796, op=0.12),
                      t(540, 1860, "@somosmiradadigital", 30, GRAY, 400, "middle", 2)])

# ════════════════════════════════════════════════════════════════
# NOSOTROS
# ════════════════════════════════════════════════════════════════
print("\nNOSOTROS")

# 1/6 — Portada
render("nosotros-1.png",
    ftr(),
    eye(540, 530, 130),
    t(540, 820, "MIRADA", 148, WHITE, 700, "middle"),
    t(540, 950, "DIGITAL", 90,  CYAN,  700, "middle", 8),
    hr(1060, op=0.25),
    t(540, 1160, "La agencia que te muestra", 44, GRAY, 400, "middle"),
    t(540, 1220, "la verdad sobre tu inversion digital.", 44, GRAY, 400, "middle"),
)

# 2/6 — El problema
render("nosotros-2.png",
    hdr("NOSOTROS", 1, 6), ftr(),
    big_bg(540, 900, "?", 700, CYAN, 0.04),
    t(80, 460, "Cuantas veces",    90, WHITE, 700),
    t(80, 570, "invertiste en",    90, WHITE, 700),
    t(80, 680, "digital y no",     90, WHITE, 700),
    t(80, 790, "supiste si",       90, WHITE, 700),
    t(80, 900, "funciono?",        90, CYAN,  700),
    hr(1040, CYAN, 0.3),
    t(80, 1140, "Eso cambia con nosotros.", 58, WHITE, 400),
)

# 3/6 — Diferencia
render("nosotros-3.png",
    hdr("NOSOTROS", 2, 6), ftr(),
    t(80, 340, "Lo que nos", 86, WHITE, 700),
    t(80, 450, "diferencia", 86, CYAN,  700),
    accent(500),
    t(80, 606, "LOS DEMAS", 32, GRAY, 400, ls=6),
    t(80, 684, "x  Ejecutan y no explican",      52, GRAY, 400),
    t(80, 754, "x  Reportes incomprensibles", 52, GRAY, 400),
    t(80, 824, "x  Desaparecen al cobrar",52, GRAY, 400),
    hr(920, CYAN, 0.5),
    t(80, 1010, "NOSOTROS", 32, CYAN, 400, ls=6),
    t(80, 1096, "+  Cada peso tiene su reporte",  54, GREEN, 700),
    t(80, 1174, "+  Explicamos cada decision",    54, GREEN, 700),
    t(80, 1252, "+  Resultados que se ven",       54, GREEN, 700),
)

# 4/6 — Servicios resumen
render("nosotros-4.png",
    hdr("NOSOTROS", 3, 6), ftr(),
    t(80, 340, "Lo que", 90, WHITE, 700),
    t(80, 450, "hacemos", 90, CYAN,  700),
    hr(510),
    t(80, 620, "Paid Ads",          60, WHITE, 700),
    t(80, 688, "Google + Meta Ads con reporte", 40, GRAY, 400),
    hr(760, op=0.10),
    t(80, 850, "SEO + Web",         60, WHITE, 700),
    t(80, 918, "Que te encuentren cuando buscan", 40, GRAY, 400),
    hr(990, op=0.10),
    t(80, 1080, "Social Media",      60, WHITE, 700),
    t(80, 1148, "Contenido con objetivo real",   40, GRAY, 400),
    hr(1220, op=0.10),
    t(80, 1310, "Auditoria Express", 60, CYAN,  700),
    t(80, 1378, "Diagnostico en 72 horas",       40, GRAY, 400),
)

# 5/6 — Proceso
render("nosotros-5.png",
    hdr("NOSOTROS", 4, 6), ftr(),
    t(80, 330, "Como trabajamos", 76, WHITE, 700),
    accent(380),
    num_step(80, 490, 1, "DIAGNOSTICO",
             "Analizamos campanas,", "web y redes que ya tenes."),
    hr(730, op=0.15),
    num_step(80, 820, 2, "ESTRATEGIA",
             "Canales, presupuesto", "y objetivos alcanzables."),
    hr(1060, op=0.15),
    num_step(80, 1150, 3, "RESULTADOS",
             "Ejecutamos, optimizamos", "y te mostramos todo."),
)

# 6/6 — CTA
render("nosotros-6.png",
    hdr("NOSOTROS", 5, 6), ftr(),
    big_bg(540, 1000, "!", 600, CYAN, 0.04),
    t(80, 460, "Queres saber",   90, WHITE, 700),
    t(80, 570, "exactamente en", 90, WHITE, 700),
    t(80, 680, "que se va tu",   90, WHITE, 700),
    t(80, 790, "inversion?",     90, CYAN,  700),
    hr(900, CYAN, 0.3),
    t(80, 1010, "Empeza gratis.", 68, WHITE, 700),
    t(80, 1110, "Sin costo. Sin compromiso.", 44, GRAY, 400),
    pill(80, 1320, "AUDITORIA EXPRESS - 72hs  >>>", CYAN),
)

# ════════════════════════════════════════════════════════════════
# SERVICIOS
# ════════════════════════════════════════════════════════════════
print("\nSERVICIOS")

# 1/6 — Portada
render("servicios-1.png",
    ftr(),
    t(80, 480, "Que",        148, WHITE, 700),
    t(80, 640, "hacemos",    148, CYAN,  700),
    hr(720, CYAN, 0.3),
    t(80, 860, "Todo lo que tu negocio", 52, GRAY, 400),
    t(80, 930, "necesita para crecer en", 52, GRAY, 400),
    t(80, 1000,"digital - y medirlo.",    52, WHITE, 400),
)

# 2/6 — Paid Ads
render("servicios-2.png",
    hdr("SERVICIOS", 1, 5), ftr(),
    pill(80, 284, "PAID ADS", CYAN),
    t(80, 410, "Google Ads +",   100, WHITE, 700),
    t(80, 530, "Meta Ads",       100, CYAN,  700),
    hr(610),
    t(80, 700, "Campanas de busqueda,",    48, GRAY, 400),
    t(80, 758, "shopping y remarketing.",  48, GRAY, 400),
    hr(830, op=0.10),
    t(80, 920, "Publicos calificados,",    48, GRAY, 400),
    t(80, 978, "no alcance vacio.",        48, GRAY, 400),
    hr(1050, op=0.10),
    t(80, 1140, "Reporte semanal",         52, GREEN, 700),
    t(80, 1200, "incluido siempre.",       52, GREEN, 700),
    hr(1300, CYAN, 0.25),
    t(80, 1400, "Ideal para negocios que quieren", 42, GRAY, 400),
    t(80, 1452, "ventas y leads predecibles.",      42, GRAY, 400),
)

# 3/6 — SEO + Web
render("servicios-3.png",
    hdr("SERVICIOS", 2, 5), ftr(),
    pill(80, 284, "SEO + WEB", CYAN),
    t(80, 410, "Que te",         100, WHITE, 700),
    t(80, 530, "encuentren",     100, CYAN,  700),
    hr(610),
    t(80, 700, "Posicionamiento local",    48, GRAY, 400),
    t(80, 758, "y nacional.",              48, GRAY, 400),
    hr(830, op=0.10),
    t(80, 920, "Web profesional,",         48, GRAY, 400),
    t(80, 978, "rapida y que convierte.",  48, GRAY, 400),
    hr(1050, op=0.10),
    t(80, 1140, "Resultados en 90 dias",   52, GREEN, 700),
    t(80, 1200, "o te explicamos por que.",52, GREEN, 700),
    hr(1300, CYAN, 0.25),
    t(80, 1400, "Ideal para negocios que", 42, GRAY, 400),
    t(80, 1452, "no aparecen cuando los buscan.", 42, GRAY, 400),
)

# 4/6 — Social Media
render("servicios-4.png",
    hdr("SERVICIOS", 3, 5), ftr(),
    pill(80, 284, "SOCIAL MEDIA", CYAN),
    t(80, 410, "Contenido",      100, WHITE, 700),
    t(80, 530, "con objetivo",   100, CYAN,  700),
    hr(610),
    t(80, 700, "No solo posteos",          48, GRAY, 400),
    t(80, 758, "para llenar el feed.",     48, GRAY, 400),
    hr(830, op=0.10),
    t(80, 920, "Calendario editorial",     48, GRAY, 400),
    t(80, 978, "orientado a ventas.",      48, GRAY, 400),
    hr(1050, op=0.10),
    t(80, 1140, "Cada pieza tiene",        52, GREEN, 700),
    t(80, 1200, "un objetivo medible.",    52, GREEN, 700),
    hr(1300, CYAN, 0.25),
    t(80, 1400, "Ideal para marcas que quieren", 42, GRAY, 400),
    t(80, 1452, "comunidad y autoridad.",         42, GRAY, 400),
)

# 5/6 — Auditoria Express
render("servicios-5.png",
    hdr("SERVICIOS", 4, 5), ftr(),
    big_bg(540, 900, "72", 500, CYAN, 0.05),
    pill(80, 284, "AUDITORIA EXPRESS", CYAN),
    t(80, 400, "Ya invertis",    90, WHITE, 700),
    t(80, 510, "y no ves",       90, WHITE, 700),
    t(80, 620, "resultados?",    90, CYAN,  700),
    hr(720, CYAN, 0.3),
    t(80, 820, "En 72hs te decimos:", 54, WHITE, 400),
    t(80, 904, "que falla en tus campanas", 48, GRAY, 400),
    t(80, 962, "donde perdes plata hoy",    48, GRAY, 400),
    t(80, 1020,"que cambiar primero",        48, GRAY, 400),
    hr(1120, CYAN, 0.25),
    t(80, 1220, "GRATIS",                   80, GREEN, 700),
    t(80, 1310, "para nuevos clientes.",    52, WHITE, 400),
)

# 6/6 — CTA servicios (reutiliza nosotros-6 approach)
render("servicios-6.png",
    hdr("SERVICIOS", 5, 5), ftr(),
    t(80, 480, "No sabes",       90, WHITE, 700),
    t(80, 590, "por donde",      90, WHITE, 700),
    t(80, 700, "empezar?",       90, CYAN,  700),
    hr(800, CYAN, 0.3),
    t(80, 920, "Empieza por la auditoria.", 58, WHITE, 400),
    t(80, 1000,"Sin costo. Sin compromiso.", 58, WHITE, 400),
    t(80, 1100,"Con resultados en 72hs.",    58, WHITE, 400),
    hr(1230, op=0.15),
    pill(80, 1400, "ESCRIBINOS AHORA  >>>", CYAN),
)

# ════════════════════════════════════════════════════════════════
# TRABAJEMOS
# ════════════════════════════════════════════════════════════════
print("\nTRABAJEMOS")

# 1/4 — Portada
render("trabajemos-1.png",
    ftr(),
    eye(540, 500, 120),
    t(80, 810, "Trabajamos",  120, WHITE, 700),
    t(80, 950, "juntos?",     120, CYAN,  700),
    hr(1040, CYAN, 0.3),
    t(80, 1160, "Asi de simple es arrancar.", 58, GRAY, 400),
)

# 2/4 — Paso 1
render("trabajemos-2.png",
    hdr("TRABAJEMOS", 1, 3), ftr(),
    t(80, 310, "01", 130, CYAN, 700, op=0.15),
    t(200, 310, "AUDITORIA", 80, WHITE, 700),
    t(200, 410, "GRATUITA",  80, CYAN,  700),
    hr(490, CYAN, 0.3),
    t(80, 620, "Analizamos lo que ya tenes:", 52, WHITE, 400),
    t(80, 700, "campanas, web y redes.",       52, GRAY, 400),
    hr(800, op=0.12),
    t(80, 900, "Te decimos que esta bien,",   52, WHITE, 400),
    t(80, 970, "que esta mal y que",           52, WHITE, 400),
    t(80, 1040,"cambiariamos.",                52, CYAN,  400),
    hr(1140, op=0.12),
    t(80, 1270, "Sin costo.", 68, GREEN, 700),
    t(80, 1360, "Resultado en 72 horas.", 52, GREEN, 400),
)

# 3/4 — Paso 2
render("trabajemos-3.png",
    hdr("TRABAJEMOS", 2, 3), ftr(),
    t(80, 310, "02", 130, CYAN, 700, op=0.15),
    t(200, 310, "PROPUESTA",  80, WHITE, 700),
    t(200, 410, "A MEDIDA",   80, CYAN,  700),
    hr(490, CYAN, 0.3),
    t(80, 620, "Basados en la auditoria,",    52, WHITE, 400),
    t(80, 690, "te presentamos un plan real:", 52, WHITE, 400),
    hr(790, op=0.12),
    t(80, 890,  "Que servicios necesitas",    52, GRAY, 400),
    t(80, 960,  "Que resultados son reales",  52, GRAY, 400),
    t(80, 1030, "Cuanto invierte tu budget",  52, GRAY, 400),
    hr(1130, op=0.12),
    t(80, 1250, "Sin paquetes genericos.",    58, GREEN, 700),
    t(80, 1340, "Sin promesas magicas.",      58, GREEN, 700),
)

# 4/4 — CTA final
render("trabajemos-4.png",
    hdr("TRABAJEMOS", 3, 3), ftr(),
    t(80, 310, "03", 130, CYAN, 700, op=0.15),
    t(200, 310, "ARRANCAMOS", 80, WHITE, 700),
    hr(430, CYAN, 0.3),
    t(80, 570, "Vos invertis.",          64, WHITE, 700),
    t(80, 660, "Nosotros ejecutamos,",   64, WHITE, 400),
    t(80, 750, "optimizamos y te",       64, WHITE, 400),
    t(80, 840, "mostramos que pasa",     64, WHITE, 400),
    t(80, 930, "con cada peso.",         64, CYAN,  700),
    hr(1040, CYAN, 0.3),
    t(80, 1160, "Empezamos?", 80, WHITE, 700),
    hr(1280, op=0.12),
    pill(80, 1440, "ESCRIBINOS AHORA  >>>", CYAN),
    t(80, 1560, "whatsapp / dm / link en bio", 38, GRAY, 400),
)

print("\nDone — 16 stories generated.")
