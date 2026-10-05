import argparse
import sys

from adaptadores.almacen_catalogo import AlmacenCatalogoDisco
from adaptadores.cliente_offline import ClienteOffline
from adaptadores.cliente_red import ClienteRed
from adaptadores.conexion_api import ConexionApi
from adaptadores.error_fuente_datos import ErrorFuenteDatos
from adaptadores.error_presupuesto import ErrorPresupuesto
from controlador import partida
from modelo.cache_catalogo import CacheCatalogo

CARPETA_CACHE = "cache_catalogo"


def avisar_espera(operacion, segundos, intento):
    print(f"[429] {operacion}: esperando {segundos}s (intento {intento})")


def _positivo(texto):
    valor = int(texto)
    if valor < 1:
        raise argparse.ArgumentTypeError("debe ser 1 o mayor")
    return valor


def leer_argumentos(argv=None):
    parser = argparse.ArgumentParser(description="Cripta")
    parser.add_argument("cripta", nargs="?", default="cripta-01", help="id de la cripta")
    parser.add_argument("--offline", action="store_true",
                        help="leer los datos de datos_offline/ en vez del API")
    parser.add_argument("--cache-size", type=_positivo, default=25,
                        help="fichas del catalogo que caben en memoria")
    parser.add_argument("--replay", metavar="PARTIDA.LOG",
                        help="reproducir una partida guardada")
    parser.add_argument("--bench", action="store_true",
                        help="correr las mediciones y salir")
    return parser.parse_args(argv)


def crear_fuente(offline):
    if offline:
        return ClienteOffline()
    return ClienteRed(ConexionApi(al_esperar=avisar_espera))


def preparar_cache(fuente, tamano):
    cache = CacheCatalogo(fuente, AlmacenCatalogoDisco(CARPETA_CACHE), capacidad=tamano)
    cache.validar_version(fuente.version_catalogo())
    return cache


def principal(argv=None):
    args = leer_argumentos(argv)

    if args.bench:
        from bench.bench import principal as correr_bench
        correr_bench()
        return 0

    fuente = crear_fuente(args.offline)
    try:
        datos = fuente.datos_cripta(args.cripta)
        fuente.fijar_presupuesto(datos.presupuesto_solicitudes)
        cache = preparar_cache(fuente, args.cache_size)
        print(f"Cripta {datos.id} v{datos.version}: {datos.salas_total} salas, "
              f"presupuesto {datos.presupuesto_solicitudes} solicitudes")
        return partida.iniciar(datos, cache, fuente, args.replay)
    except ErrorPresupuesto as error:
        print(f"[PRESUPUESTO] {error}")
        return 1
    except ErrorFuenteDatos as error:
        print(f"[ERROR] {error}")
        return 1
    finally:
        print(f"Solicitudes usadas: {fuente.solicitudes_realizadas()}")


if __name__ == "__main__":
    sys.exit(principal())