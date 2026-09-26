"""
Carga el archivo .env de esta carpeta como variables de entorno.
Se importa primero en bot.py y recolector.py, así funciona igual en Windows, Mac y Linux
sin tener que exportar nada a mano. Las variables ya definidas en el sistema tienen prioridad
y los renglones vacíos se ignoran (queda el valor por defecto).
"""

import os
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"


def cargar_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for linea in path.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        clave, valor = clave.strip(), valor.strip()
        if valor.startswith("#"):          # "CLAVE=   # explicación" = vacío
            valor = ""
        elif valor[:1] in ("'", '"') and valor[-1:] == valor[:1]:
            valor = valor[1:-1]
        else:
            # comentario al final del renglón: "CLAVE=valor   # explicación"
            for sep in (" #", "\t#"):
                if sep in valor:
                    valor = valor.split(sep, 1)[0].rstrip()
        if valor:   # vacío = usar el valor por defecto del bot
            os.environ.setdefault(clave, valor)


cargar_env()


# ── Tapar claves en todo lo que se muestra en pantalla ────────────────────────

SECRETOS = ("TELEGRAM_TOKEN", "ODDS_API_KEY", "API_FOOTBALL_KEY", "ANTHROPIC_API_KEY")


class _SalidaSinSecretos:
    """Envuelve stdout/stderr y reemplaza cualquier clave por *** (ej. un error de red con la URL de Telegram)."""

    def __init__(self, destino):
        self._destino = destino
        self._secretos = [v for k in SECRETOS if len(v := os.environ.get(k, "")) >= 8]

    def write(self, texto):
        for s in self._secretos:
            texto = texto.replace(s, "***")
        return self._destino.write(texto)

    def __getattr__(self, nombre):
        return getattr(self._destino, nombre)


def ocultar_secretos() -> None:
    import sys
    if not isinstance(sys.stdout, _SalidaSinSecretos):
        sys.stdout = _SalidaSinSecretos(sys.stdout)
        sys.stderr = _SalidaSinSecretos(sys.stderr)


ocultar_secretos()
