import cairosvg
import os

OUTPUT = "/home/user/MIRADA-DIGITAL/brand/highlights"

NAVY  = "#0D1B2A"
CYAN  = "#00D4FF"
WHITE = "#FFFFFF"
GREEN = "#00E676"

def cover(name, icon_svg, filename):
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1080" width="1080" height="1080">
  <rect width="1080" height="1080" fill="{NAVY}"/>
  <!-- subtle grid texture -->
  <line x1="540" y1="200" x2="540" y2="880" stroke="{CYAN}" stroke-width="1" opacity="0.06"/>
  <line x1="200" y1="540" x2="880" y2="540" stroke="{CYAN}" stroke-width="1" opacity="0.06"/>
  <g transform="translate(540, 480)">
    {icon_svg}
  </g>
  <text x="540" y="650"
        font-family="Arial, Helvetica, sans-serif"
        font-weight="700" font-size="52" fill="{WHITE}"
        text-anchor="middle" letter-spacing="8">{name}</text>
</svg>"""
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{OUTPUT}/{filename}", output_width=1080, output_height=1080)
    print(f"✓ {filename}")

# 1. NOSOTROS — eye icon
cover("NOSOTROS", f"""
  <path d="M -80,0 A 92,92 0 0,1 80,0 A 133,133 0 0,0 -80,0 Z"
        fill="none" stroke="{CYAN}" stroke-width="7" stroke-linejoin="round"/>
  <circle cx="0" cy="-10" r="30" fill="{NAVY}" stroke="{CYAN}" stroke-width="6"/>
  <circle cx="0" cy="-10" r="9"  fill="{CYAN}" opacity="0.5"/>
  <polyline points="-20,14 -6,2 6,-12 20,-24"
            fill="none" stroke="{GREEN}" stroke-width="6"
            stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="-6" cy="2"   r="5.5" fill="{GREEN}"/>
  <circle cx="6"  cy="-12" r="5.5" fill="{GREEN}"/>
  <circle cx="20" cy="-24" r="5.5" fill="{GREEN}"/>
""", "cover-nosotros.png")

# 2. RESULTADOS — ascending bars (minimal, thin)
cover("RESULTADOS", f"""
  <rect x="-72" y="20"  width="28" height="60"  rx="4" fill="{CYAN}" opacity="0.5"/>
  <rect x="-24" y="-16" width="28" height="96"  rx="4" fill="{CYAN}" opacity="0.75"/>
  <rect x="24"  y="-60" width="28" height="140" rx="4" fill="{CYAN}"/>
  <line x1="-86" y1="80" x2="66" y2="80" stroke="{WHITE}" stroke-width="3" opacity="0.2"/>
""", "cover-resultados.png")

# 3. SERVICIOS — 2x2 grid of rounded squares
cover("SERVICIOS", f"""
  <rect x="-68" y="-68" width="52" height="52" rx="10" fill="none" stroke="{CYAN}" stroke-width="5"/>
  <rect x="16"  y="-68" width="52" height="52" rx="10" fill="none" stroke="{CYAN}" stroke-width="5"/>
  <rect x="-68" y="16"  width="52" height="52" rx="10" fill="none" stroke="{CYAN}" stroke-width="5"/>
  <rect x="16"  y="16"  width="52" height="52" rx="10" fill="{CYAN}" stroke="{CYAN}" stroke-width="5"/>
""", "cover-servicios.png")

# 4. CLIENTES — speech bubble with quote marks
cover("CLIENTES", f"""
  <rect x="-70" y="-60" width="140" height="100" rx="18" fill="none" stroke="{CYAN}" stroke-width="6"/>
  <polygon points="-20,40 -40,72 10,40" fill="{NAVY}" stroke="{CYAN}" stroke-width="6" stroke-linejoin="round"/>
  <text x="-22" y="4" font-family="Georgia, serif" font-size="64" fill="{CYAN}" opacity="0.9">"</text>
""", "cover-clientes.png")

# 5. APRENDE — upward diagonal arrow
cover("APRENDE", f"""
  <circle cx="0" cy="0" r="72" fill="none" stroke="{CYAN}" stroke-width="6" opacity="0.3"/>
  <line x1="-30" y1="30" x2="30" y2="-30"
        stroke="{CYAN}" stroke-width="7" stroke-linecap="round"/>
  <polyline points="4,-30 30,-30 30,-4"
            fill="none" stroke="{CYAN}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
""", "cover-aprende.png")

# 6. TRABAJEMOS — arrow in circle (CTA feel)
cover("TRABAJEMOS", f"""
  <circle cx="0" cy="0" r="72" fill="none" stroke="{CYAN}" stroke-width="6"/>
  <line x1="-28" y1="0" x2="28" y2="0"
        stroke="{WHITE}" stroke-width="7" stroke-linecap="round"/>
  <polyline points="10,-18 28,0 10,18"
            fill="none" stroke="{WHITE}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
""", "cover-trabajemos.png")

print("\nAll covers generated.")
