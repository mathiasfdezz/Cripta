import os

from estructuras.ordenamientos import ordenar
from modelo.registro_puntaje import RegistroPuntaje

SEPARADOR = "\t"


class TablaPuntajes:
    """Tabla local de puntajes en un archivo de texto, una partida por línea."""

    def __init__(self, ruta="puntajes.txt"):
        self._ruta = ruta

    def agregar(self, registro):
        carpeta = os.path.dirname(self._ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        nombre = registro.nombre.replace(SEPARADOR, " ").replace("\n", " ").strip() or "anónimo"
        campos = (nombre, registro.cripta_id, registro.version_cripta, registro.resultado,
                  str(registro.acciones), str(registro.enemigos_derrotados),
                  str(registro.tiempo_final))
        with open(self._ruta, "a", encoding="utf-8") as archivo:
            archivo.write(SEPARADOR.join(campos) + "\n")

    def leer(self):
        """Victorias primero, luego menos acciones y luego menos tiempo."""
        if not os.path.exists(self._ruta):
            return []
        registros = []
        with open(self._ruta, encoding="utf-8") as archivo:
            for linea in archivo:
                partes = linea.rstrip("\n").split(SEPARADOR)
                if len(partes) != 7:
                    continue   # una línea dañada no tumba la tabla
                try:
                    registros.append(RegistroPuntaje(partes[0], partes[1], partes[2], partes[3],
                                                     int(partes[4]), int(partes[5]),
                                                     int(partes[6])))
                except ValueError:
                    continue
        return ordenar(registros, lambda r: (0 if r.resultado == "victoria" else 1,
                                             r.acciones, r.tiempo_final))
