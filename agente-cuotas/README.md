# Agente de Cuotas — Mirada Digital

Bot de Telegram para grupos que compara las cuotas de **Bet365, Betano y Stake**:

- **/cuotas** — tabla comparativa por mercado (1X2, Más/Menos), mejor cuota marcada y margen de cada casa
- **Probabilidad justa** — consenso de las casas quitando su margen
- **/valor** — cuotas que pagan más que la probabilidad justa (ventaja ≥ `EDGE_MIN`)
- **/arbitraje** — combinaciones entre casas que suman < 100% de probabilidad, con cuánto apostar a cada resultado
- **/analisis** — comentario corto del partido escrito por Claude (opcional)
- **Alertas automáticas** al grupo cuando aparece valor o un arbitraje nuevo (opcional)

## De dónde salen las cuotas

De la API de [odds-api.net](https://odds-api.net) (claves `bet365`, `betano`, `stake`).
No se scrapean las casas directamente: sus términos lo prohíben y bloquean bots.
La cobertura de cada casa depende de la liga y del plan: `/casas` muestra cuáles
están disponibles con tu key, y `/cuotas` avisa si falta alguna en un partido.

Sin `ODDS_API_KEY` el bot funciona igual con **datos de ejemplo**, para probar.

## Puesta en marcha

1. Creá el bot con [@BotFather](https://t.me/BotFather) → `/newbot` → copiá el token.
2. Agregalo al grupo. Con el modo privacidad por defecto solo ve comandos, que es lo que necesita.
3. Instalá y configurá:
   ```bash
   cd agente-cuotas
   pip install -r requirements.txt
   cp .env.example .env    # completá los valores
   set -a; source .env; set +a
   python bot.py
   ```
4. Probar sin Telegram: `python bot.py --prueba` · Tests: `python -m unittest -v`

El bot usa *long polling*, así que tiene que quedar corriendo en una máquina
(VPS, Railway, Render, una Raspberry…). GitHub Actions no sirve para esto
porque los jobs terminan.

Para las alertas: poné `TELEGRAM_CHAT_ID` con el id del grupo (empieza con `-100`)
y `ALERTAS_MIN=15`, por ejemplo. Cada escaneo consulta hasta `ESCANEO_MAX`
partidos por liga, así que ajustalo según la cuota de tu plan de la API.

## Comandos

| Comando | Qué hace |
|---|---|
| `/partidos [deporte] [liga]` | Próximos partidos (48 hs), numerados |
| `/cuotas N` | Compara cuotas del partido N de la última lista (o un `event_id`) |
| `/valor [deporte] [liga]` | Busca cuotas con valor |
| `/arbitraje [deporte] [liga]` | Busca arbitrajes |
| `/analisis N` | Comentario con IA (requiere `ANTHROPIC_API_KEY`) |
| `/deportes`, `/ligas [deporte]`, `/casas` | Catálogos y cobertura |

## Cómo se calcula

- **Margen** de una casa = Σ(1/cuota) − 1
- **Probabilidad justa** = promedio entre casas de (1/cuota) / Σ(1/cuota)
- **Valor** = mejor cuota × probabilidad justa − 1 (se exige ≥ 2 casas con el mercado completo)
- **Arbitraje** si Σ(1/mejor cuota) < 1 usando más de una casa; ganancia = 1/Σ − 1

## Archivos

- `bot.py` — Telegram, comandos y alertas
- `odds_client.py` — cliente de la API de cuotas + datos de ejemplo
- `analisis.py` — cálculos (sin red, testeado en `test_analisis.py`)
- `formato.py` — mensajes HTML para Telegram
- `ia.py` — comentario con Claude

> Es información, no consejo. Las cuotas cambian en segundos, las casas limitan
> cuentas que arbitran y ninguna apuesta es segura. Solo para mayores de 18.
