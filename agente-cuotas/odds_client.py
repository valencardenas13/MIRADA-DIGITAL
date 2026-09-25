"""
Cliente de cuotas — Mirada Digital

Trae eventos y cuotas desde odds-api.net (https://api.odds-api.net/v1), que
agrega casas como bet365, betano y stake en un formato único.

No scrapeamos las casas directamente: sus términos lo prohíben y bloquean bots.

Si no hay ODDS_API_KEY (o ODDS_API_MOCK=1) se usa MockOddsClient con datos de
ejemplo, así el bot se puede probar sin gastar cuota de la API.
"""

import os
import time

import httpx

BASE_URL = os.environ.get("ODDS_API_BASE_URL", "https://api.odds-api.net/v1")


class OddsApiError(Exception):
    pass


class OddsApiClient:
    def __init__(self, api_key: str, base_url: str = BASE_URL):
        self.http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"X-API-Key": api_key},
            timeout=20,
        )

    def _get(self, path: str, params: dict | None = None) -> dict:
        params = {k: v for k, v in (params or {}).items() if v not in (None, "")}
        try:
            r = self.http.get(path, params=params)
        except httpx.HTTPError as e:
            raise OddsApiError(f"No se pudo conectar con la API de cuotas: {e}") from e
        if r.status_code == 401:
            raise OddsApiError("ODDS_API_KEY inválida o vencida.")
        if r.status_code == 429:
            raise OddsApiError("Se alcanzó el límite de consultas de la API de cuotas. Probá en un rato.")
        if r.status_code >= 400:
            raise OddsApiError(f"API de cuotas respondió {r.status_code}: {r.text[:200]}")
        return r.json()

    def sports(self) -> list[str]:
        return self._get("/sports").get("items", [])

    def leagues(self, sport: str) -> list[str]:
        return self._get("/leagues", {"sport": sport}).get("items", [])

    def bookmakers(self) -> list[str]:
        return [b["bookmaker"] for b in self._get("/bookmakers").get("items", [])]

    def events(self, sport: str, league: str | None = None, hours: int = 48, limit: int = 20) -> list[dict]:
        now = int(time.time())
        data = self._get("/events", {
            "sport": sport,
            "league": league,
            "start_from": now,
            "start_to": now + hours * 3600,
            "limit": limit,
        })
        return sorted(data.get("items", []), key=lambda e: e.get("start_time") or 0)

    def odds(self, event_id: str, bookmakers: list[str]) -> list[dict]:
        """Todas las líneas de cuotas del evento para las casas pedidas (pagina sola)."""
        lines, cursor = [], None
        for _ in range(10):  # tope de páginas para no quemar cuota
            data = self._get(f"/events/{event_id}/odds/snapshot", {
                "bookmakers": ",".join(bookmakers),
                "price_fields": "odds",
                "cursor": cursor,
            })
            lines.extend(data.get("items", []))
            cursor = data.get("next_cursor")
            if not cursor:
                break
        return lines


# ── Datos de ejemplo ──────────────────────────────────────────────────────────

def _moneyline(event_id, book, home, draw, away, teams):
    out = []
    for side, odds, name in (("home", home, teams[0]), ("draw", draw, "Empate"), ("away", away, teams[1])):
        out.append({
            "event_id": event_id, "bookmaker": book, "market_key": "moneyline",
            "market_group_id": "moneyline::0", "period": 0, "side": side,
            "selection_name": name, "odds": odds, "is_available": True,
        })
    return out


def _total(event_id, book, line, over, under):
    return [
        {"event_id": event_id, "bookmaker": book, "market_key": "total",
         "market_group_id": f"total::0::{line}", "period": 0, "line": line,
         "side": side, "selection_name": f"{label} {line}", "odds": odds, "is_available": True}
        for side, label, odds in (("over", "Más de", over), ("under", "Menos de", under))
    ]


class MockOddsClient:
    """Imita OddsApiClient con partidos inventados (incluye un arbitraje y cuotas con valor)."""

    def __init__(self):
        now = int(time.time())
        self._events = [
            {"event_id": "mock-1", "sport": "soccer", "league": "Argentina Liga Profesional",
             "home_team": "River Plate", "away_team": "Boca Juniors", "start_time": now + 5 * 3600},
            {"event_id": "mock-2", "sport": "soccer", "league": "LaLiga",
             "home_team": "Real Madrid", "away_team": "Barcelona", "start_time": now + 26 * 3600},
            {"event_id": "mock-3", "sport": "soccer", "league": "Brazil Serie A",
             "home_team": "Flamengo", "away_team": "Palmeiras", "start_time": now + 30 * 3600},
        ]
        rb, rm, fp = ("River Plate", "Boca Juniors"), ("Real Madrid", "Barcelona"), ("Flamengo", "Palmeiras")
        self._odds = {
            "mock-1": (
                _moneyline("mock-1", "bet365", 2.30, 3.10, 3.20, rb)
                + _moneyline("mock-1", "betano", 2.45, 3.00, 3.05, rb)
                + _moneyline("mock-1", "stake", 2.35, 3.25, 3.40, rb)
                + _total("mock-1", "bet365", "2.5", 2.05, 1.75)
                + _total("mock-1", "betano", "2.5", 2.35, 1.62)
                + _total("mock-1", "stake", "2.5", 2.00, 1.80)
            ),
            "mock-2": (
                _moneyline("mock-2", "bet365", 2.10, 3.60, 3.30, rm)
                + _moneyline("mock-2", "betano", 2.25, 3.50, 3.20, rm)
                + _moneyline("mock-2", "stake", 2.05, 3.75, 3.60, rm)
            ),
            "mock-3": (
                _moneyline("mock-3", "bet365", 1.95, 3.40, 4.00, fp)
                + _moneyline("mock-3", "betano", 2.00, 3.30, 3.90, fp)
            ),
        }

    def sports(self):
        return ["soccer"]

    def leagues(self, sport):
        return sorted({e["league"] for e in self._events if e["sport"] == sport})

    def bookmakers(self):
        return ["bet365", "betano", "stake"]

    def events(self, sport, league=None, hours=48, limit=20):
        return [e for e in self._events
                if e["sport"] == sport and (not league or league.lower() in e["league"].lower())][:limit]

    def odds(self, event_id, bookmakers):
        return [l for l in self._odds.get(event_id, []) if l["bookmaker"] in bookmakers]


def crear_cliente():
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if not key or os.environ.get("ODDS_API_MOCK") == "1":
        print("[Cuotas] Sin ODDS_API_KEY — usando datos de EJEMPLO", flush=True)
        return MockOddsClient(), True
    return OddsApiClient(key), False
