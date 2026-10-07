import os

from adaptadores.cabecera_partida import CabeceraPartida
from adaptadores.error_bitacora import ErrorBitacora

MARCA = "# CRIPTA partida"
FIN_CABECERA = "---"


class BitacoraPartida:
    """Archivo de texto de solo anexado: cabecera y luego un comando del jugador
    por línea. Con él --replay repite la partida sin interacción."""

    def __init__(self, ruta):
        self.ruta = ruta

    def crear(self, cabecera):
        carpeta = os.path.dirname(self.ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            archivo.write(f"{MARCA}\n")
            archivo.write(f"cripta={cabecera.cripta_id}\n")
            archivo.write(f"version_cripta={cabecera.version_cripta}\n")
            archivo.write(f"version_catalogo={cabecera.version_catalogo}\n")
            archivo.write(f"semilla={cabecera.semilla}\n")
            if not cabecera.reproducible:
                archivo.write("reproducible=no\n")
            archivo.write(f"{FIN_CABECERA}\n")

    @staticmethod
    def continuar(ruta_nueva, cabecera, ruta_origen, comandos):
        """Bitácora nueva para una partida cargada: copia los primeros comandos de la
        bitácora original, así --replay llega al mismo punto del guardado y sigue."""
        try:
            _, anteriores = BitacoraPartida.leer(ruta_origen)
            reproducible = len(anteriores) >= comandos
        except ErrorBitacora:
            anteriores, reproducible = [], False
        nueva = BitacoraPartida(ruta_nueva)
        nueva.crear(CabeceraPartida(cabecera.cripta_id, cabecera.version_cripta,
                                    cabecera.version_catalogo, cabecera.semilla, reproducible))
        if reproducible:
            for comando in anteriores[:comandos]:
                nueva.anotar(comando)
        return nueva

    def anotar(self, comando):
        # se abre y se cierra en cada comando: si el programa se cae, lo jugado queda
        with open(self.ruta, "a", encoding="utf-8") as archivo:
            archivo.write(comando.replace("\n", " ") + "\n")

    @staticmethod
    def leer(ruta):
        """Devuelve (CabeceraPartida, lista de comandos)."""
        try:
            with open(ruta, encoding="utf-8") as archivo:
                lineas = [linea.rstrip("\n") for linea in archivo]
        except FileNotFoundError:
            raise ErrorBitacora(f"no existe la bitácora {ruta}")
        if not lineas or lineas[0] != MARCA or FIN_CABECERA not in lineas:
            raise ErrorBitacora(f"{ruta} no es una bitácora de partida de Cripta")
        fin = lineas.index(FIN_CABECERA)
        cripta = version_cripta = version_catalogo = semilla = None
        reproducible = True
        for linea in lineas[1:fin]:
            clave, _, valor = linea.partition("=")
            if clave == "cripta":
                cripta = valor
            elif clave == "version_cripta":
                version_cripta = valor
            elif clave == "version_catalogo":
                version_catalogo = valor
            elif clave == "semilla":
                semilla = valor
            elif clave == "reproducible":
                reproducible = valor != "no"
        if None in (cripta, version_cripta, version_catalogo, semilla):
            raise ErrorBitacora(f"a la cabecera de {ruta} le faltan datos")
        try:
            semilla = int(semilla)
        except ValueError:
            raise ErrorBitacora(f"la semilla de {ruta} no es un número")
        comandos = [linea for linea in lineas[fin + 1:] if linea.strip()]
        return CabeceraPartida(cripta, version_cripta, version_catalogo, semilla,
                               reproducible), comandos
