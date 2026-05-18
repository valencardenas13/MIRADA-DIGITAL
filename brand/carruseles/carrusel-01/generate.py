import cairosvg, os

OUT = "/home/user/MIRADA-DIGITAL/brand/carruseles/carrusel-01"
os.makedirs(OUT, exist_ok=True)

NAVY, CYAN, WHITE, GREEN, GRAY = "#0D1B2A","#00D4FF","#FFFFFF","#00E676","#8892A4"
W = H = 1080

def render(name, *parts):
    body = "\n".join(p for p in parts if p)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}">'
           f'<rect width="{W}" height="{H}" fill="{NAVY}"/>'
           f'{body}</svg>')
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{OUT}/{name}",
                     output_width=W*2, output_height=H*2)
    print(f"  ✓ {name}")

def t(x, y, s, sz=60, c=WHITE, w=700, anchor="start", ls=0, op=1):
    return (f'<text x="{x}" y="{y}" font-family="Liberation Sans,Arial,sans-serif" '
            f'font-weight="{w}" font-size="{sz}" fill="{c}" text-anchor="{anchor}" '
            f'letter-spacing="{ls}" opacity="{op}">{s}</text>')

def hr(y, c=CYAN, op=0.18, x1=80, x2=1000):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{c}" stroke-width="1.5" opacity="{op}"/>'

def accent(y, w=70):
    return f'<rect x="80" y="{y}" width="{w}" height="5" rx="2" fill="{CYAN}"/>'

def pill(label, x=80, y=940, c=CYAN):
    pw = len(label) * 20 + 48
    return (f'<rect x="{x}" y="{y-38}" width="{pw}" height="56" rx="28" fill="{c}" opacity="0.12"/>'
            f'<rect x="{x}" y="{y-38}" width="{pw}" height="56" rx="28" fill="none" stroke="{c}" stroke-width="1.5"/>'
            f'{t(x+24, y, label, 28, c, 500, ls=2)}')

def ftr():
    return "\n".join([hr(1000), t(540, 1044, "@somosmiradadigital", 28, GRAY, 400, "middle", 2)])

def eye(cx, cy, r=52):
    ru=r*55/45; rl=r*80/45; ri=r*15/45; iy=cy-r*4/45; sw=r*2.5/45
    return (f'<path d="M {cx-r},{cy} A {ru},{ru} 0 0,1 {cx+r},{cy} A {rl},{rl} 0 0,0 {cx-r},{cy} Z"'
            f' fill="none" stroke="{CYAN}" stroke-width="{sw:.1f}" stroke-linejoin="round"/>'
            f'<circle cx="{cx}" cy="{iy:.1f}" r="{ri:.1f}" fill="{NAVY}" stroke="{CYAN}" stroke-width="{sw*0.8:.1f}"/>')

def num_badge(x, y, n, c=CYAN):
    return (f'<circle cx="{x}" cy="{y}" r="42" fill="{c}" opacity="0.1"/>'
            f'<circle cx="{x}" cy="{y}" r="42" fill="none" stroke="{c}" stroke-width="2.5"/>'
            f'{t(x, y+20, str(n), 60, c, 700, "middle")}')

def bg_text(s, x=540, y=620, sz=380):
    return t(x, y, s, sz, CYAN, 700, "middle", op=0.04)

# ── SLIDE 1 — Cover / Hook ───────────────────────────────────────
render("slide-01.png",
    ftr(),
    eye(540, 300, 80),
    t(80, 500, "5 senales de que", 82, WHITE, 700),
    t(80, 606, "tu agencia NO", 82, CYAN,  700),
    t(80, 712, "esta funcionando", 82, WHITE, 700),
    hr(790, CYAN, 0.3),
    t(80, 880, "Y como detectarlas antes de", 46, GRAY, 400),
    t(80, 938, "seguir perdiendo plata.", 46, GRAY, 400),
)

# ── SLIDE 2 — Intro / Contexto ───────────────────────────────────
render("slide-02.png",
    ftr(), bg_text("?"),
    t(80, 220, "La mayoria de", 78, WHITE, 700),
    t(80, 316, "los negocios que", 78, WHITE, 700),
    t(80, 412, "invierten en digital", 78, CYAN,  700),
    t(80, 508, "no saben si su", 78, WHITE, 700),
    t(80, 604, "agencia funciona.", 78, WHITE, 700),
    hr(680, CYAN, 0.25),
    t(80, 770, "No es tu culpa.", 52, WHITE, 400),
    t(80, 838, "Nadie te lo explico.", 52, GRAY,  400),
    t(80, 906, "Hasta hoy.", 52, CYAN,  700),
)

# ── SLIDE 3 — Señal 1 ────────────────────────────────────────────
render("slide-03.png",
    ftr(), bg_text("1"),
    num_badge(122, 200, 1),
    t(190, 222, "SENAL 1", 34, CYAN, 400, ls=6),
    accent(270),
    t(80, 370, "No recibes", 90, WHITE, 700),
    t(80, 478, "reportes", 90, WHITE, 700),
    t(80, 586, "periodicos.", 90, CYAN,  700),
    hr(660, op=0.15),
    t(80, 754, "Si tu agencia no te muestra", 50, GRAY, 400),
    t(80, 818, "numeros cada semana o mes,", 50, GRAY, 400),
    t(80, 882, "no tienen nada bueno que mostrar.", 50, WHITE, 400),
)

# ── SLIDE 4 — Señal 2 ────────────────────────────────────────────
render("slide-04.png",
    ftr(), bg_text("2"),
    num_badge(122, 200, 2),
    t(190, 222, "SENAL 2", 34, CYAN, 400, ls=6),
    accent(270),
    t(80, 370, "Solo te hablan", 86, WHITE, 700),
    t(80, 474, "de likes e", 86, WHITE, 700),
    t(80, 578, "impresiones.", 86, CYAN,  700),
    hr(650, op=0.15),
    t(80, 744, "Likes no pagan sueldos.", 50, WHITE, 700),
    t(80, 810, "Lo que importa: cuantos leads,", 50, GRAY, 400),
    t(80, 874, "ventas y a que costo.", 50, GRAY, 400),
)

# ── SLIDE 5 — Señal 3 ────────────────────────────────────────────
render("slide-05.png",
    ftr(), bg_text("3"),
    num_badge(122, 200, 3),
    t(190, 222, "SENAL 3", 34, CYAN, 400, ls=6),
    accent(270),
    t(80, 370, "No podes entrar", 84, WHITE, 700),
    t(80, 466, "a tu propia", 84, WHITE, 700),
    t(80, 562, "cuenta.", 84, CYAN,  700),
    hr(640, op=0.15),
    t(80, 730, "Tu cuenta de Google Ads o", 50, GRAY,  400),
    t(80, 794, "Meta Ads es TUYA.", 50, WHITE, 700),
    t(80, 858, "Si no tenes acceso,", 50, GRAY,  400),
    t(80, 922, "hay un problema serio.", 50, WHITE, 400),
)

# ── SLIDE 6 — Señal 4 ────────────────────────────────────────────
render("slide-06.png",
    ftr(), bg_text("4"),
    num_badge(122, 200, 4),
    t(190, 222, "SENAL 4", 34, CYAN, 400, ls=6),
    accent(270),
    t(80, 370, "Los resultados", 86, WHITE, 700),
    t(80, 466, '"siempre estan', 86, WHITE, 700),
    t(80, 562, 'por venir."', 86, CYAN,  700),
    hr(640, op=0.15),
    t(80, 730, "El primer mes puede ser de", 50, GRAY,  400),
    t(80, 794, "aprendizaje. El segundo tambien.", 50, GRAY,  400),
    t(80, 858, "Pero si al tercer mes siguen", 50, WHITE, 400),
    t(80, 922, '"proxima semana lo vemos", corre.', 50, WHITE, 400),
)

# ── SLIDE 7 — Señal 5 ────────────────────────────────────────────
render("slide-07.png",
    ftr(), bg_text("5"),
    num_badge(122, 200, 5),
    t(190, 222, "SENAL 5", 34, CYAN, 400, ls=6),
    accent(270),
    t(80, 370, "No te explican", 86, WHITE, 700),
    t(80, 466, "que cambiaron", 86, WHITE, 700),
    t(80, 562, "ni por que.", 86, CYAN,  700),
    hr(640, op=0.15),
    t(80, 730, "Cada optimizacion tiene una razon.", 48, GRAY,  400),
    t(80, 794, "Si tu agencia no te la comunica,", 48, GRAY,  400),
    t(80, 858, "o no la tienen, o no les importa", 48, WHITE, 400),
    t(80, 922, "que la entiendas.", 48, WHITE, 400),
)

# ── SLIDE 8 — CTA ────────────────────────────────────────────────
render("slide-08.png",
    ftr(),
    eye(540, 210, 70),
    t(540, 390, "En Mirada Digital", 54, GRAY,  400, "middle"),
    t(540, 470, "hacemos exactamente", 66, WHITE, 700, "middle"),
    t(540, 554, "lo contrario.", 66, CYAN,  700, "middle"),
    hr(620, CYAN, 0.25),
    t(80, 710, "Cada peso con su reporte.", 52, WHITE, 400),
    t(80, 774, "Cada decision explicada.", 52, WHITE, 400),
    t(80, 838, "Resultados que se ven.", 52, GREEN, 700),
    hr(900, op=0.15),
    pill("AUDITORIA GRATUITA — 72hs  >>>", 80, 978),
)

print("\nCarrusel 01 — 8 slides generados.")
