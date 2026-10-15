import os
import sys

# nombre del estilo y su código ANSI
CODIGOS = (
    ("titulo", "1;36"),
    ("negrita", "1"),
    ("ok", "32"),
    ("alerta", "33"),
    ("peligro", "31"),
    ("tenue", "2"),
    ("nuevo", "1;33"),
)


class Estilo:
    """Colores para la consola. Solo se usan si la salida es una terminal de verdad y no
    existe la variable NO_COLOR; en las pruebas o al redirigir a un archivo queda texto plano."""

    def __init__(self):
        self._terminal_lista = self._preparar_terminal()

    def aplicar(self, texto, estilo):
        if not self._terminal_lista or not self._es_terminal():
            return texto
        for nombre, codigo in CODIGOS:
            if nombre == estilo:
                return f"\033[{codigo}m{texto}\033[0m"
        return texto

    @staticmethod
    def _es_terminal():
        try:
            return sys.stdout.isatty()
        except (AttributeError, ValueError):
            return False

    @staticmethod
    def _preparar_terminal():
        if os.environ.get("NO_COLOR") is not None:
            return False
        if os.name != "nt":
            return True
        # en Windows hay que pedirle a la consola que entienda los códigos de color
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            manejador = kernel32.GetStdHandle(-11)
            modo = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(manejador, ctypes.byref(modo)):
                return False
            return bool(kernel32.SetConsoleMode(manejador, modo.value | 0x0004))
        except (AttributeError, OSError):
            return False
