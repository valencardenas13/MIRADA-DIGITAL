"""
Fuentes de datos históricos — Mirada Digital

- API-Football (https://www.api-football.com, v3): partidos, árbitros, estadios,
  estadísticas por partido, goleadores, lesiones y suspensiones.
- Open-Meteo (https://open-meteo.com): pronóstico del clima, gratis y sin key.

Cada función devuelve dicts ya "aplanados" con los nombres que usa db.py.
"""

import os
import re
from datetime import datetime, timezone

import httpx

AF_URL = os.environ.get("API_FOOTBALL_URL", "https://v3.football.api-sports.io")


class FuenteError(Exception):
    pass


class ApiFootball:
    def __init__(self, api_key: str):
        self.http = httpx.Client(base_url=AF_URL, headers={"x-apisports-key": api_key}, timeout=30)
        self.llamadas = 0

    def _get(self, path: str, params: dict) -> list:
        try:
            r = self.http.get(path, params=params)
        except httpx.HTTPError as e:
            raise FuenteError(f"No se pudo conectar con API-Football: {e}") from e
        self.llamadas += 1
        if r.status_code >= 400:
            raise FuenteError(f"API-Football respondió {r.status_code}: {r.text[:200]}")
        data = r.json()
        # API-Football devuelve 200 con "errors" cuando se excede el plan o falta un parámetro
        if data.get("errors"):
            raise FuenteError(f"API-Football: {data['errors']}")
        return data.get("response", [])

    def temporada_actual(self, liga_id: int) -> dict | None:
        resp = self._get("/leagues", {"id": liga_id, "current": "true"})
        if not resp or not resp[0].get("seasons"):
            return None
        r = resp[0]
        return {"id": liga_id, "nombre": r["league"]["name"], "pais": r["country"]["name"],
                "temporada": r["seasons"][0]["year"]}

    def partidos(self, liga_id: int, temporada: int) -> list[dict]:
        return [_partido(f) for f in self._get("/fixtures", {"league": liga_id, "season": temporada})]

    def partidos_con_estadisticas(self, ids: list[int]) -> list[tuple[dict, list[tuple[int, dict]]]]:
        """Hasta 20 partidos por llamada; la respuesta trae las estadísticas embebidas."""
        out = []
        for f in self._get("/fixtures", {"ids": "-".join(str(i) for i in ids[:20])}):
            stats = [(s["team"]["id"], _stats(s.get("statistics") or [])) for s in f.get("statistics") or []]
            out.append((_partido(f), stats))
        return out

    def goleadores(self, liga_id: int, temporada: int) -> list[dict]:
        out = []
        for r in self._get("/players/topscorers", {"league": liga_id, "season": temporada}):
            st = (r.get("statistics") or [{}])[0]
            out.append({
                "id": r["player"]["id"], "nombre": r["player"]["name"],
                "equipo_id": st.get("team", {}).get("id"), "liga_id": liga_id, "temporada": temporada,
                "goles": (st.get("goals") or {}).get("total") or 0,
                "asistencias": (st.get("goals") or {}).get("assists") or 0,
                "partidos": (st.get("games") or {}).get("appearences") or 0,
                "minutos": (st.get("games") or {}).get("minutes") or 0,
            })
        return out

    def bajas(self, partido_id: int) -> list[dict]:
        return [{
            "partido_id": partido_id, "jugador_id": r["player"]["id"], "equipo_id": r["team"]["id"],
            "nombre": r["player"]["name"], "tipo": r["player"].get("type"), "motivo": r["player"].get("reason"),
        } for r in self._get("/injuries", {"fixture": partido_id})]


def _partido(f: dict) -> dict:
    fx, teams, goals = f["fixture"], f["teams"], f.get("goals") or {}
    return {
        "id": fx["id"], "liga_id": f["league"]["id"], "temporada": f["league"]["season"],
        "fecha": fx["timestamp"], "estado": fx["status"]["short"],
        "local_id": teams["home"]["id"], "local": teams["home"]["name"],
        "visitante_id": teams["away"]["id"], "visitante": teams["away"]["name"],
        "goles_local": goals.get("home"), "goles_visitante": goals.get("away"),
        "arbitro": fx.get("referee"), "estadio": (fx.get("venue") or {}).get("name"),
        "ciudad": (fx.get("venue") or {}).get("city"),
    }


STATS = {
    "Total Shots": "tiros", "Shots on Goal": "tiros_arco", "Corner Kicks": "corners", "Fouls": "faltas",
    "Yellow Cards": "amarillas", "Red Cards": "rojas", "Ball Possession": "posesion", "expected_goals": "xg",
}


def _stats(lista: list[dict]) -> dict:
    out = {}
    for s in lista:
        campo = STATS.get(s.get("type"))
        v = s.get("value")
        if not campo:
            continue
        if isinstance(v, str):
            v = re.sub(r"[^\d.]", "", v) or None   # "55%" -> "55"
        out[campo] = float(v) if v is not None else (0.0 if campo in ("amarillas", "rojas") else None)
    return out


# ── Clima ─────────────────────────────────────────────────────────────────────

def coordenadas(ciudad: str) -> tuple[float, float] | None:
    nombre = re.split(r"[,(]", ciudad)[0].strip()
    try:
        r = httpx.get("https://geocoding-api.open-meteo.com/v1/search",
                      params={"name": nombre, "count": 1, "language": "es"}, timeout=15)
        res = r.json().get("results") or []
    except (httpx.HTTPError, ValueError):
        return None
    return (res[0]["latitude"], res[0]["longitude"]) if res else None


def pronostico(lat: float, lon: float, ts: int) -> dict | None:
    """Clima a la hora del partido (Open-Meteo pronostica hasta 16 días)."""
    dia = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")
    try:
        r = httpx.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon, "timezone": "UTC", "start_date": dia, "end_date": dia,
            "hourly": "temperature_2m,precipitation,wind_speed_10m"}, timeout=15)
        h = r.json()["hourly"]
    except (httpx.HTTPError, ValueError, KeyError):
        return None
    hora = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:00")
    if hora not in h["time"]:
        return None
    i = h["time"].index(hora)
    return {"temperatura": h["temperature_2m"][i], "lluvia": h["precipitation"][i], "viento": h["wind_speed_10m"][i]}
