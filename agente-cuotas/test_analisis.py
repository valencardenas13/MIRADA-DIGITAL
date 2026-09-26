"""Tests del análisis de cuotas. Correr con: python -m unittest -v"""

import unittest

import formato
from analisis import analizar_evento
from odds_client import MockOddsClient


def linea(book, side, odds, group="moneyline::0", market="moneyline", **extra):
    return {"bookmaker": book, "side": side, "odds": odds, "market_group_id": group,
            "market_key": market, "period": 0, "selection_name": side, **extra}


class TestAnalisis(unittest.TestCase):
    def test_margen_y_prob_justa(self):
        lines = [linea("bet365", "home", 1.90), linea("bet365", "away", 1.90)]
        m = analizar_evento(lines)[0]
        self.assertAlmostEqual(m.margenes["bet365"], 2 / 1.9 - 1, places=6)
        self.assertAlmostEqual(m.justa["home"], 0.5)
        self.assertEqual(m.valor, [])      # con una sola casa no hay consenso
        self.assertIsNone(m.arbitraje)

    def test_mejor_cuota_y_arbitraje(self):
        lines = [
            linea("bet365", "home", 2.10), linea("bet365", "away", 1.80),
            linea("stake", "home", 1.80), linea("stake", "away", 2.10),
        ]
        m = analizar_evento(lines)[0]
        self.assertEqual(m.mejor["home"], (2.10, "bet365"))
        self.assertEqual(m.mejor["away"], (2.10, "stake"))
        self.assertAlmostEqual(m.arbitraje["ganancia"], 1 / (2 / 2.1) - 1)
        self.assertAlmostEqual(sum(m.arbitraje["reparto"].values()), 1.0)

    def test_sin_arbitraje_en_una_sola_casa(self):
        # una casa con suma < 1 (error de datos) no cuenta como arbitraje entre casas
        lines = [linea("betano", "home", 2.2), linea("betano", "away", 2.2)]
        self.assertIsNone(analizar_evento(lines)[0].arbitraje)

    def test_valor(self):
        lines = [
            linea("bet365", "home", 2.00), linea("bet365", "away", 1.80),
            linea("betano", "home", 2.00), linea("betano", "away", 1.80),
            linea("stake", "home", 2.30), linea("stake", "away", 1.60),
        ]
        m = analizar_evento(lines, edge_min=0.03)[0]
        self.assertEqual([(v["side"], v["casa"]) for v in m.valor], [("home", "stake")])

    def test_ignora_no_disponibles_y_props(self):
        lines = [
            linea("bet365", "home", 2.0), linea("bet365", "away", 2.0),
            linea("stake", "home", 9.0, is_available=False),
            linea("stake", "over", 1.9, group="p::0", market="player_points", player_name="X"),
        ]
        mercados = analizar_evento(lines)
        self.assertEqual(len(mercados), 1)
        self.assertEqual(mercados[0].mejor["home"], (2.0, "bet365"))

    def test_mercados_separados_por_linea(self):
        lines = [linea("bet365", s, 1.9, group=f"total::0::{l}", market="total", line=l)
                 for l in ("2.5", "3.5") for s in ("over", "under")]
        self.assertEqual(sorted(m.line for m in analizar_evento(lines)), ["2.5", "3.5"])


class TestMockYFormato(unittest.TestCase):
    def test_mock_tiene_arbitraje_y_valor(self):
        c = MockOddsClient()
        todos = [m for e in c.events("soccer") for m in analizar_evento(c.odds(e["event_id"], ["bet365", "betano", "stake"]))]
        self.assertTrue(any(m.arbitraje for m in todos))
        self.assertTrue(any(m.valor for m in todos))

    def test_detalle_avisa_casa_faltante(self):
        c = MockOddsClient()
        e = c.events("soccer", "Brazil")[0]
        texto = formato.detalle_evento(e, analizar_evento(c.odds(e["event_id"], ["bet365", "betano", "stake"])),
                                       ["bet365", "betano", "stake"])
        self.assertIn("Sin cuotas de: Stake", texto)

    def test_partir_respeta_limite(self):
        texto = "\n\n".join("x" * 1000 for _ in range(10))
        self.assertTrue(all(len(b) <= 4000 for b in formato.partir(texto)))


if __name__ == "__main__":
    unittest.main()
