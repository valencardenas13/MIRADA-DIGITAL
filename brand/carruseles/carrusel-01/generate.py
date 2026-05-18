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

def hr(y, c=CYAN, op=0.2):
    return f'<line x1="80" y1="{y}" x2="1000" y2="{y}" stroke="{c}" stroke-width="1.5" opacity="{op}"/>'

def num(n):
    return (f'<text x="80" y="200" font-family="Liberation Sans,Arial,sans-serif" '
            f'font-weight="700" font-size="520" fill="{CYAN}" opacity="0.05"'
            f' text-anchor="start">{n}</text>')

def ftr():
    return (f'<line x1="80" y1="1016" x2="1000" y2="1016" stroke="{CYAN}" stroke-width="1" opacity="0.15"/>'
            f'{t(540, 1056, "@somosmiradadigital", 26, GRAY, 400, "middle", 3)}')

def swipe():
    return t(1000, 1056, "desliza  >", 26, CYAN, 400, "end")

# ── 01 — COVER ───────────────────────────────────────────────────
# Hook: pregunta que duele. Sin mas texto.
render("slide-01.png",
    ftr(), swipe(),
    t(80,  310, "Tu agencia", 130, WHITE, 700),
    t(80,  460, "te esta",    130, WHITE, 700),
    t(80,  610, "mintiendo?", 130, CYAN,  700),
    hr(700),
    t(80,  790, "5 senales que no te va a mostrar.", 52, GRAY, 400),
)

# ── 02 — SENAL 1 ─────────────────────────────────────────────────
render("slide-02.png",
    ftr(), swipe(), num("1"),
    t(80, 200, "SENAL 1", 34, CYAN, 400, ls=8),
    t(80, 440, "No recibes",  120, WHITE, 700),
    t(80, 580, "reportes.",   120, CYAN,  700),
    hr(670),
    t(80, 760, "Si no muestran numeros,", 52, GRAY, 400),
    t(80, 828, "no tienen nada bueno que mostrar.", 52, WHITE, 400),
)

# ── 03 — SENAL 2 ─────────────────────────────────────────────────
render("slide-03.png",
    ftr(), swipe(), num("2"),
    t(80, 200, "SENAL 2", 34, CYAN, 400, ls=8),
    t(80, 430, "Solo hablan", 118, WHITE, 700),
    t(80, 566, "de likes.",   118, CYAN,  700),
    hr(658),
    t(80, 748, "Likes no pagan sueldos.", 52, WHITE, 700),
    t(80, 816, "Pedi conversiones, leads, ventas.", 52, GRAY, 400),
)

# ── 04 — SENAL 3 ─────────────────────────────────────────────────
render("slide-04.png",
    ftr(), swipe(), num("3"),
    t(80, 200, "SENAL 3", 34, CYAN, 400, ls=8),
    t(80, 410, "No podes",    118, WHITE, 700),
    t(80, 546, "entrar a tu", 118, WHITE, 700),
    t(80, 682, "cuenta.",     118, CYAN,  700),
    hr(760),
    t(80, 850, "Tu cuenta es TUYA. Siempre.", 52, WHITE, 700),
)

# ── 05 — SENAL 4+5 ───────────────────────────────────────────────
render("slide-05.png",
    ftr(), swipe(),
    t(80, 160, "SENAL 4", 34, CYAN, 400, ls=8),
    t(80, 280, '"Los resultados', 86, WHITE, 700),
    t(80, 380,  'estan por venir."', 86, CYAN, 700),
    hr(450, op=0.12),
    t(80, 540, "SENAL 5", 34, CYAN, 400, ls=8),
    t(80, 660, "No explican", 86, WHITE, 700),
    t(80, 760, "nada de lo que hacen.", 86, CYAN, 700),
    hr(840, CYAN, 0.3),
    t(80, 930, "Las dos juntas = salida urgente.", 46, GRAY, 400),
)

# ── 06 — CTA ─────────────────────────────────────────────────────
render("slide-06.png",
    ftr(),
    t(80,  240, "Nosotros",    128, WHITE, 700),
    t(80,  388, "hacemos lo",  128, WHITE, 700),
    t(80,  536, "contrario.",  128, CYAN,  700),
    hr(620, CYAN, 0.35),
    t(80,  720, "Auditoria gratuita de tu cuenta.", 54, WHITE, 400),
    t(80,  790, "72 horas. Sin compromiso.",        54, GRAY,  400),
    hr(870, op=0.12),
    t(80,  960, "Escribinos por WhatsApp  >>", 50, GREEN, 700),
)

print("\nCarrusel 01 - 6 slides.")
