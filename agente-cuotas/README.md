# Agente de Cuotas — Mirada Digital

Bot de Telegram para grupos que compara las cuotas de **Bet365, Betano y Stake** y
**solo recomienda las que respalda el historial**: forma de los equipos, goles,
cara a cara, estadísticas, bajas de jugadores clave, árbitro y clima. Todo sale de
una base de datos propia (SQLite) que el bot actualiza solo.

## Cómo decide si manda una cuota

```
cuotas (odds-api.net) ─┐
                       ├─> ¿la cuota paga más de lo que dicen los datos? ──> sí: pick con "Por qué"
base histórica ─> modelo┘                                                 └─> no: descartada con motivo
```

1. **Mercado**: mejor cuota entre las 3 casas y probabilidad justa (consenso sin margen).
2. **Modelo con historial**: goles esperados de cada equipo según su ataque y defensa,
   de local y de visitante, con más peso a los partidos recientes. Con eso se calculan
   las probabilidades de 1X2 y Más/Menos (distribución de Poisson).
   - **Bajas**: si falta un goleador (lesión o suspensión), el equipo pierde la mitad
     de lo que ese jugador aporta en goles.
   - **Clima**: con lluvia fuerte o viento, −7% de goles; con calor extremo, −5%.
   - **Árbitro, forma, cara a cara, tiros, xG y córners**: se muestran en el
     "Por qué" de cada pick y en `/ficha`.
3. **Filtro**: una cuota se manda solo si se cumplen las cuatro condiciones:
   - los dos equipos tienen al menos `MIN_PARTIDOS` partidos en la base
   - el modelo le da una ventaja de al menos `EDGE_MODELO` (cuota × prob. del modelo − 1)
   - la cuota no está por debajo del consenso de las casas
   - modelo y mercado no difieren en más de `MAX_DESVIO`. Si difieren más,
     probablemente falta información (una rotación, una lesión de último momento)
     y se descarta.
4. **Registro**: cada pick enviado se guarda y, cuando termina el partido, se marca
   como ganado o perdido. `/rendimiento` muestra el acierto y el ROI reales.

Las cuotas que parecían tentadoras pero no pasan el filtro se muestran como
**descartadas, con el motivo**, para que el grupo vea por qué no se recomiendan.

## Fuentes de datos

| Qué | De dónde | Key |
|---|---|---|
| Cuotas Bet365 / Betano / Stake | [odds-api.net](https://odds-api.net) | `ODDS_API_KEY` |
| Partidos, árbitros, estadios, estadísticas, goleadores, lesiones y suspensiones | [API-Football](https://www.api-football.com) | `API_FOOTBALL_KEY` |
| Clima a la hora del partido | [Open-Meteo](https://open-meteo.com) | no hace falta |

No se scrapean las casas: sus términos lo prohíben y bloquean bots.

**Casas de referencia**: si tu proveedor cubre pocas de las casas donde apostás, agregá
otras en `REFERENCIA` (por ejemplo `pinnacle`, que es la referencia habitual del mercado).
Se usan solo para calcular la probabilidad justa y nunca se recomiendan. Con una sola
casa en total, el bot no manda picks, porque no hay contra qué comparar.

**API-Football**: el plan gratis tiene un límite diario de consultas y restricciones
de temporadas. Para ligas actuales y varias ligas conviene un plan pago; revisá el
detalle en su dashboard. El recolector no se pasa de `MAX_LLAMADAS` por corrida y
baja las estadísticas de a 20 partidos por consulta. La primera carga puede tardar
algunos días en completarse con el plan gratis.

Sin keys, el bot funciona con **datos de ejemplo** (cuotas e historial inventados) para probarlo.

## Puesta en marcha

1. Creá el bot con [@BotFather](https://t.me/BotFather) → `/newbot` → copiá el token.
   Agregalo al grupo.
2. Instalá y configurá:
   ```bash
   cd agente-cuotas
   pip install -r requirements.txt
   cp .env.example .env    # completá los valores
   set -a; source .env; set +a
   python recolector.py --temporadas 2   # primera carga: temporada actual + anterior
   python bot.py
   ```
3. Para probar sin Telegram: `python bot.py --prueba` · Tests: `python -m unittest -v`

El bot tiene que quedar corriendo en una máquina (VPS, Railway, Render…). Mientras
corre, actualiza la base cada `SYNC_HORAS` y, si configurás `TELEGRAM_CHAT_ID` y
`ALERTAS_MIN`, avisa al grupo los picks nuevos. Nunca repite un pick ya enviado.

IDs de ligas en API-Football (`LIGAS`): 128 Argentina Liga Profesional ·
71 Brasil Serie A · 13 Copa Libertadores · 39 Premier League · 140 LaLiga.
Verificalos en tu dashboard de API-Football antes de usarlos.

## Comandos

| Comando | Qué hace |
|---|---|
| `/partidos [deporte] [liga]` | Próximos partidos (48 hs), numerados |
| `/cuotas N` | Tabla de cuotas + modelo + picks y descartes del partido N |
| `/ficha N` | Todos los datos del partido: forma, estadísticas, cara a cara, bajas, árbitro, clima |
| `/valor [deporte] [liga]` | Picks respaldados por datos, con su "Por qué" |
| `/arbitraje [deporte] [liga]` | Arbitrajes entre casas (matemáticos, no dependen del historial) |
| `/rendimiento` | Acierto y ROI de los picks enviados |
| `/analisis N` | Comentario con IA sobre cuotas + ficha (requiere `ANTHROPIC_API_KEY`) |
| `/deportes`, `/ligas [deporte]`, `/casas` | Catálogos, cobertura y tamaño de la base |

## Archivos

- `bot.py`: Telegram, comandos, alertas y actualización periódica
- `odds_client.py`: cuotas (odds-api.net) y datos de ejemplo
- `analisis.py`: mejor cuota, margen, probabilidad justa, arbitraje
- `db.py`: esquema SQLite y consultas (forma, cara a cara, árbitro, bajas…)
- `fuentes.py`: API-Football y Open-Meteo
- `recolector.py`: llena la base, vincula partidos entre APIs y liquida picks
- `modelo.py`: modelo de goles, ajustes y filtro de picks
- `formato.py`: mensajes para Telegram
- `ia.py`: comentario con Claude
- `demo_datos.py`: base histórica de ejemplo

## Límites honestos

- El modelo es simple y transparente, no una bola de cristal. Las casas grandes
  tienen modelos mejores; buscar valor contra ellas es difícil. Por eso se exige
  que modelo **y** consenso de mercado coincidan.
- Los ajustes por bajas y clima son estimaciones razonables, no valores calibrados
  con datos. Mirá `/rendimiento` después de 100 picks o más antes de confiar.
- Las fuerzas de equipos de ligas distintas (por ejemplo, en la Libertadores) se
  comparan contra el promedio de cada liga, lo que es una aproximación.

> Es información, no consejo. Las cuotas cambian en segundos, las casas limitan
> cuentas que ganan seguido y ninguna apuesta es segura. Solo para mayores de 18.
