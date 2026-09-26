"""Tests de la base histórica, el modelo y el filtro. Correr con: python -m unittest -v"""

import time
import unittest

import db
import demo_datos
import fuentes
import modelo
import recolector
from analisis import analizar_evento
from odds_client import MockOddsClient

CASAS = ["bet365", "betano", "stake"]


def fixture_af(fid, home, away, gh, ga, ts, estado="FT", referee="Juan Pérez, Argentina", stats=None):
    """Partido con la forma que devuelve API-Football /fixtures."""
    return {
        "fixture": {"id": fid, "referee": referee, "timestamp": ts, "status": {"short": estado},
                    "venue": {"id": 1, "name": "Monumental", "city": "Buenos Aires"}},
        "league": {"id": 128, "season": 2026},
        "teams": {"home": {"id": home, "name": f"Equipo {home}"}, "away": {"id": away, "name": f"Equipo {away}"}},
        "goals": {"home": gh, "away": ga},
        "statistics": stats or [],
    }


class TestFuentes(unittest.TestCase):
    def test_parseo_partido(self):
        p = fuentes._partido(fixture_af(10, 1, 2, 3, 1, 1000))
        self.assertEqual((p["local_id"], p["goles_local"], p["arbitro"], p["ciudad"]), (1, 3, "Juan Pérez, Argentina", "Buenos Aires"))

    def test_parseo_estadisticas(self):
        s = fuentes._stats([{"type": "Ball Possession", "value": "55%"}, {"type": "Yellow Cards", "value": None},
                            {"type": "Total Shots", "value": 14}, {"type": "expected_goals", "value": "1.72"},
                            {"type": "Offsides", "value": 3}])
        self.assertEqual(s, {"posesion": 55.0, "amarillas": 0.0, "tiros": 14.0, "xg": 1.72})


class FakeApi:
    """Imita fuentes.ApiFootball contando llamadas."""

    def __init__(self, ahora):
        self.llamadas, self.ahora = 0, ahora

    def temporada_actual(self, liga_id):
        self.llamadas += 1
        return {"id": liga_id, "nombre": "Liga", "pais": "AR", "temporada": 2026}

    def partidos(self, liga_id, temporada):
        self.llamadas += 1
        ps = [fixture_af(i, 1 + i % 2, 2 - i % 2, i % 3, 1, self.ahora - i * 86400) for i in range(1, 45)]
        ps.append(fixture_af(99, 1, 2, None, None, self.ahora + 3600, estado="NS"))
        return [fuentes._partido(p) for p in ps]

    def goleadores(self, liga_id, temporada):
        self.llamadas += 1
        return [{"id": 7, "nombre": "Goleador", "equipo_id": 1, "liga_id": liga_id, "temporada": temporada,
                 "goles": 10, "asistencias": 2, "partidos": 20, "minutos": 1700}]

    def partidos_con_estadisticas(self, ids):
        self.llamadas += 1
        stats = [{"team": {"id": 1}, "statistics": [{"type": "Yellow Cards", "value": 2}]},
                 {"team": {"id": 2}, "statistics": [{"type": "Yellow Cards", "value": 3}]}]
        return [(fuentes._partido(fixture_af(i, 1 + i % 2, 2 - i % 2, i % 3, 1, self.ahora - i * 86400)),
                 [(s["team"]["id"], fuentes._stats(s["statistics"])) for s in stats]) for i in ids]

    def bajas(self, partido_id):
        self.llamadas += 1
        return [{"partido_id": partido_id, "jugador_id": 7, "equipo_id": 1, "nombre": "Goleador",
                 "tipo": "Missing Fixture", "motivo": "Suspended"}]


class TestRecolector(unittest.TestCase):
    def setUp(self):
        self.con = db.conectar(":memory:")
        self.ahora = int(time.time())
        recolector.LIGAS = [128]

    def test_sincroniza_todo_y_respeta_tope(self):
        api = FakeApi(self.ahora)
        recolector.sincronizar(self.con, api, log=lambda m: None)
        c = self.con.execute
        self.assertEqual(c("SELECT COUNT(*) FROM partidos").fetchone()[0], 45)
        self.assertEqual(c("SELECT COUNT(*) FROM partidos WHERE stats_ok = 1").fetchone()[0], 44)
        self.assertEqual(c("SELECT nombre FROM bajas WHERE partido_id = 99").fetchone()[0], "Goleador")
        self.assertEqual(c("SELECT goles FROM jugadores WHERE id = 7").fetchone()[0], 10)

        recolector.MAX_LLAMADAS, antes = 2, recolector.MAX_LLAMADAS
        try:
            api2 = FakeApi(self.ahora)
            recolector.sincronizar(db.conectar(":memory:"), api2, log=lambda m: None)
            self.assertLessEqual(api2.llamadas, 2)
        finally:
            recolector.MAX_LLAMADAS = antes

    def test_vincular_nombres_distintos(self):
        db.guardar_partido(self.con, {"id": 5, "liga_id": 128, "temporada": 2026, "fecha": self.ahora, "estado": "NS",
                                      "local_id": 1, "local": "CA River Plate", "visitante_id": 2,
                                      "visitante": "Boca Juniors", "goles_local": None, "goles_visitante": None,
                                      "arbitro": None, "estadio": None, "ciudad": None})
        ev = {"event_id": "x", "home_team": "River Plate", "away_team": "Boca Juniors", "start_time": self.ahora + 600}
        self.assertEqual(recolector.vincular(self.con, ev), 5)
        otro = {"event_id": "y", "home_team": "Racing Club", "away_team": "Boca Juniors", "start_time": self.ahora}
        self.assertIsNone(recolector.vincular(self.con, otro))

    def test_liquidar_picks(self):
        db.guardar_partido(self.con, {"id": 5, "liga_id": 128, "temporada": 2026, "fecha": self.ahora, "estado": "FT",
                                      "local_id": 1, "local": "A", "visitante_id": 2, "visitante": "B",
                                      "goles_local": 2, "goles_visitante": 1, "arbitro": None, "estadio": None, "ciudad": None})
        for sel, mercado, linea in (("home", "moneyline", ""), ("draw", "moneyline", ""),
                                    ("over", "total", "2.5"), ("under", "total", "3.0")):
            self.con.execute("INSERT INTO picks(event_id, partido_id, mercado, linea, seleccion, cuota) VALUES (?,?,?,?,?,?)",
                             ("e", 5, mercado, linea, sel, 2.0))
        recolector.liquidar_picks(self.con)
        res = [r[0] for r in self.con.execute("SELECT resultado FROM picks ORDER BY id")]
        self.assertEqual(res, ["ganado", "perdido", "ganado", "anulado"])


class TestModelo(unittest.TestCase):
    def test_poisson_suma_uno(self):
        m = modelo.matriz_poisson(1.4, 1.1)
        self.assertAlmostEqual(sum(map(sum, m)), 1.0)

    def test_equipos_iguales_simetricos(self):
        f = modelo.Ficha(1, 1, 0, "A", "B", 1, 2, matriz=modelo.matriz_poisson(1.2, 1.2))
        self.assertAlmostEqual(f.prob("moneyline", "home"), f.prob("moneyline", "away"))
        self.assertIsNone(f.prob("total", "over", "2.0"))   # líneas enteras no cubiertas
        self.assertAlmostEqual(f.prob("total", "over", "2.5") + f.prob("total", "under", "2.5"), 1.0)

    def _escenario(self):
        con = db.conectar(":memory:")
        c = MockOddsClient()
        eventos = c.events("soccer")
        demo_datos.cargar_demo(con, eventos)
        out = {}
        for e in eventos:
            pid = recolector.vincular(con, e)
            p = con.execute("SELECT ciudad, fecha FROM partidos WHERE id = ?", (pid,)).fetchone()
            f = modelo.armar_ficha(con, pid, recolector.clima(con, p["ciudad"], p["fecha"]))
            out[e["home_team"]] = (f, analizar_evento(c.odds(e["event_id"], CASAS)))
        return con, out

    def test_bajas_bajan_goles_esperados(self):
        con, out = self._escenario()
        f, _ = out["River Plate"]
        sin_bajas = modelo.armar_ficha(con, f.partido_id, f.clima)
        con.execute("DELETE FROM bajas")
        limpio = modelo.armar_ficha(con, f.partido_id, f.clima)
        self.assertLess(sin_bajas.goles_esperados[1], limpio.goles_esperados[1])
        self.assertTrue(any("Bajas en Boca" in a for a in sin_bajas.ajustes))

    def test_filtro(self):
        _, out = self._escenario()
        f, ms = out["Flamengo"]
        picks, _ = modelo.evaluar(ms, f, 0.03)
        self.assertEqual([p["nombre"] for p in picks], ["Flamengo"])

        f, ms = out["River Plate"]   # el "valor" del mercado en Más de 2.5 no lo respalda el historial
        picks, descartes = modelo.evaluar(ms, f, 0.03)
        self.assertEqual(picks, [])
        self.assertTrue(any("historial no la respalda" in d["motivo"] for d in descartes))

        f, ms = out["Real Madrid"]   # modelo y mercado demasiado lejos
        picks, descartes = modelo.evaluar(ms, f, 0.03)
        self.assertEqual(picks, [])
        self.assertTrue(any("muy lejos" in d["motivo"] for d in descartes))

    def test_clima_cambia_la_decision(self):
        con, out = self._escenario()
        f, ms = out["River Plate"]
        self.assertGreater(f.clima["lluvia"], 4)
        seco = modelo.armar_ficha(con, f.partido_id, None)
        self.assertLess(f.prob("total", "over", "2.5"), seco.prob("total", "over", "2.5"))
        picks_seco, _ = modelo.evaluar(ms, seco, 0.03)
        self.assertIn("Más de 2.5", [p["nombre"] for p in picks_seco])   # sin lluvia sí pasaba

    def test_sin_ficha_o_poco_historial_no_manda(self):
        _, out = self._escenario()
        f, ms = out["Flamengo"]
        picks, descartes = modelo.evaluar(ms, None, 0.03)
        self.assertEqual(picks, [])
        self.assertTrue(all("no está en la base" in d["motivo"] for d in descartes))
        f.n_local = 3
        picks, descartes = modelo.evaluar(ms, f, 0.03)
        self.assertEqual(picks, [])
        self.assertTrue(any("poco historial" in d["motivo"] for d in descartes))


if __name__ == "__main__":
    unittest.main()


class TestReferencia(unittest.TestCase):
    def test_referencia_no_se_recomienda_pero_cuenta_para_consenso(self):
        from test_analisis import linea
        lines = [linea("bet365", "home", 2.10), linea("bet365", "away", 1.75),
                 linea("pinnacle", "home", 2.25), linea("pinnacle", "away", 1.70)]
        m = analizar_evento(lines, 0.03, ["bet365"])[0]
        self.assertEqual(m.mejor["home"], (2.10, "bet365"))   # pinnacle paga más pero no se recomienda
        self.assertEqual(set(m.margenes), {"bet365", "pinnacle"})
        self.assertIsNone(m.arbitraje)

    def test_una_sola_casa_no_manda_picks(self):
        from test_analisis import linea
        lines = [linea("bet365", s, o) for s, o in (("home", 3.0), ("draw", 3.4), ("away", 2.6))]
        m = analizar_evento(lines, 0.03, ["bet365"])
        f = modelo.Ficha(1, 1, 0, "A", "B", 1, 2, n_local=30, n_visitante=30, matriz=modelo.matriz_poisson(2.0, 0.8))
        picks, descartes = modelo.evaluar(m, f, 0.03)
        self.assertEqual(picks, [])
        self.assertTrue(any("referencia" in d["motivo"] for d in descartes))


class TestConfig(unittest.TestCase):
    def test_lee_env_con_comentarios_y_comillas(self):
        import os
        import tempfile
        from pathlib import Path
        import config
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_text('# comentario\nPRUEBA_A=abc123   # explicación\nPRUEBA_B="con # numeral"\n'
                         'PRUEBA_C=\nPRUEBA_E=    # solo comentario\nPRUEBA_D=ya_definida\n', encoding="utf-8")
            os.environ["PRUEBA_D"] = "del_sistema"
            config.cargar_env(p)
            self.assertEqual(os.environ["PRUEBA_A"], "abc123")
            self.assertEqual(os.environ["PRUEBA_B"], "con # numeral")
            self.assertNotIn("PRUEBA_C", os.environ)   # vacío: queda el valor por defecto
            self.assertNotIn("PRUEBA_E", os.environ)
            self.assertEqual(os.environ["PRUEBA_D"], "del_sistema")


class TestOcultarSecretos(unittest.TestCase):
    def test_tapa_claves(self):
        import io
        import os
        import config
        os.environ["TELEGRAM_TOKEN"], antes = "123456:SECRETO-LARGO", os.environ.get("TELEGRAM_TOKEN")
        try:
            buf = io.StringIO()
            salida = config._SalidaSinSecretos(buf)
            salida.write("Error en https://api.telegram.org/bot123456:SECRETO-LARGO/getUpdates")
            self.assertEqual(buf.getvalue(), "Error en https://api.telegram.org/bot***/getUpdates")
        finally:
            if antes is None:
                del os.environ["TELEGRAM_TOKEN"]
            else:
                os.environ["TELEGRAM_TOKEN"] = antes


class TestNumeros(unittest.TestCase):
    def test_valor_mal_escrito_usa_defecto(self):
        import os
        import config
        os.environ["PRUEBA_N"] = "cada cuántos minutos"
        os.environ["PRUEBA_F"] = "0,05"
        os.environ["PRUEBA_L"] = "128, 71"
        self.assertEqual(config.numero("PRUEBA_N", 0), 0)
        self.assertEqual(config.numero("PRUEBA_F", 0.03), 0.05)
        self.assertEqual(config.numero("PRUEBA_NADA", 12), 12)
        self.assertEqual(config.lista_numeros("PRUEBA_L", "1"), [128, 71])
