import argparse
import os
import secrets
import sys
from datetime import datetime

from adaptadores.almacen_catalogo import AlmacenCatalogoDisco
from adaptadores.bitacora_partida import BitacoraPartida
from adaptadores.cabecera_partida import CabeceraPartida
from adaptadores.cliente_offline import ClienteOffline
from adaptadores.cliente_red_con_copia import ClienteRedConCopia
from adaptadores.conexion_api import ConexionApi
from adaptadores.error_bitacora import ErrorBitacora
from adaptadores.error_fuente_datos import ErrorFuenteDatos
from adaptadores.error_presupuesto import ErrorPresupuesto
from adaptadores.tabla_puntajes import TablaPuntajes
from controlador.partida import ControladorPartida
from controlador.verificacion_cripta import VerificacionCripta
from modelo.cache_catalogo import CacheCatalogo
from vista.consola import Consola
from modelo.linea_tiempo import CADA_POR_DEFECTO
from vista.texto_historia import lineas_historia
from vista.texto_resolubilidad import lineas_resolubilidad
from vista.vista_replay import VistaReplay

CARPETA_CACHE = "cache_catalogo"
CARPETA_CRIPTAS = "cache_criptas"
CARPETA_PARTIDAS = "partidas"
ARCHIVO_PUNTAJES = "puntajes.txt"


class VistaSilenciosa:
    """Para --replay --hasta: no muestra nada mientras se reproduce."""

    def __getattr__(self, nombre):
        return lambda *args, **kwargs: None


def avisar_espera(operacion, segundos, intento):
    print(f"[429] {operacion}: esperando {segundos}s (intento {intento})")


def _positivo(texto):
    valor = int(texto)
    if valor < 1:
        raise argparse.ArgumentTypeError("debe ser 1 o mayor")
    return valor


def leer_argumentos(argv=None):
    parser = argparse.ArgumentParser(description="Cripta")
    parser.add_argument("cripta", nargs="?",
                        help="id de la cripta; si no se indica, se elige de la lista")
    parser.add_argument("--offline", action="store_true",
                        help="leer los datos de datos_offline/ en vez del API")
    parser.add_argument("--cache-size", type=_positivo, default=25,
                        help="fichas del catalogo que caben en memoria")
    parser.add_argument("--replay", metavar="PARTIDA.LOG",
                        help="reproducir una partida guardada")
    parser.add_argument("--bench", action="store_true",
                        help="correr las mediciones y salir")
    parser.add_argument("--semilla", type=int,
                        help="semilla del azar (por defecto se elige una al azar)")
    parser.add_argument("--verificar", metavar="CRIPTA",
                        help="solo verificar si la cripta se puede ganar, sin jugar")
    parser.add_argument("--forzar", action="store_true",
                        help="jugar aunque la cripta no sea resoluble")
    parser.add_argument("--checkpoint-cada", type=_positivo, default=CADA_POR_DEFECTO,
                        metavar="K", help="acciones entre puntos de control de la línea de tiempo")
    parser.add_argument("--hasta", type=int, metavar="T",
                        help="con --replay: mostrar el estado en el instante T y salir")
    return parser.parse_args(argv)


def crear_fuente(offline):
    if offline:
        return ClienteOffline()
    # esqueleto y contenido quedan en disco para la próxima partida de la misma versión
    return ClienteRedConCopia(ConexionApi(al_esperar=avisar_espera), CARPETA_CRIPTAS)


def preparar_cache(fuente, version_catalogo, tamano):
    cache = CacheCatalogo(fuente, AlmacenCatalogoDisco(CARPETA_CACHE), capacidad=tamano)
    cache.validar_version(version_catalogo)
    return cache


def verificar(cripta_id, fuente):
    """--verificar: solo la verificación, sin vista interactiva (FR-208)."""
    datos = fuente.datos_cripta(cripta_id)
    fuente.fijar_presupuesto(datos.presupuesto_solicitudes)
    _, reporte = VerificacionCripta.ejecutar(fuente, datos)
    for linea in lineas_resolubilidad(reporte, datos.id):
        print(linea)
    print(f"Solicitudes usadas: {fuente.solicitudes_realizadas()}")
    return 0 if reporte.resoluble else 1


def jugar(cripta_id, fuente, tamano_cache, semilla, vista, forzar=False,
          checkpoint_cada=CADA_POR_DEFECTO):
    datos = fuente.datos_cripta(cripta_id)
    fuente.fijar_presupuesto(datos.presupuesto_solicitudes)
    esqueleto, reporte = VerificacionCripta.ejecutar(fuente, datos)
    vista.mostrar_resolubilidad(reporte, datos.id)
    if not reporte.resoluble and not forzar:
        print("La partida no inicia porque la cripta no se puede ganar. "
              "Usa --forzar para jugarla igual.")
        return 1
    version_catalogo = fuente.version_catalogo()
    cache = preparar_cache(fuente, version_catalogo, tamano_cache)
    if semilla is None:
        semilla = secrets.randbelow(10 ** 9)

    controlador = ControladorPartida(datos, fuente, cache, vista, semilla, version_catalogo,
                                     CARPETA_PARTIDAS, esqueleto, checkpoint_cada)
    ruta = os.path.join(CARPETA_PARTIDAS, f"partida-{datetime.now():%Y%m%d-%H%M%S}.log")
    bitacora = BitacoraPartida(ruta)
    bitacora.crear(CabeceraPartida(datos.id, datos.version, version_catalogo, semilla))
    print(f"Cripta {datos.id} v{datos.version}, semilla {semilla}. Bitácora: {ruta}")
    print("Juega eligiendo el número de una opción del menú. Escribe ? para ver la ayuda.")

    controlador.jugar(vista.pedir_comando, bitacora)

    if controlador.estado.terminada():
        tabla = TablaPuntajes(ARCHIVO_PUNTAJES)
        tabla.agregar(controlador.registro_puntaje(vista.pedir_nombre()))
        vista.mostrar_puntajes(tabla.leer())
    vista.mostrar_reporte(fuente.solicitudes_realizadas(), datos.presupuesto_solicitudes,
                          cache.aciertos, cache.fallos)
    return 0


def reproducir(ruta, fuente, tamano_cache, hasta=None, checkpoint_cada=CADA_POR_DEFECTO):
    cabecera, comandos = BitacoraPartida.leer(ruta)
    if not cabecera.reproducible:
        print("[REPLAY] Esta bitácora empieza desde un guardado cuya bitácora original ya no "
              "existe: no se puede garantizar una reproducción fiel.")
        return 1
    datos = fuente.datos_cripta(cabecera.cripta_id)
    fuente.fijar_presupuesto(datos.presupuesto_solicitudes)
    version_catalogo = fuente.version_catalogo()
    if datos.version != cabecera.version_cripta or version_catalogo != cabecera.version_catalogo:
        print(f"[REPLAY] No se puede garantizar una reproducción fiel: la bitácora es de "
              f"{cabecera.cripta_id} v{cabecera.version_cripta} con catálogo "
              f"{cabecera.version_catalogo}, y los datos disponibles son v{datos.version} "
              f"con catálogo {version_catalogo}.")
        return 1
    cache = preparar_cache(fuente, version_catalogo, tamano_cache)

    # con --hasta solo se imprime el resumen, sin la vista (FR-307)
    vista = VistaReplay() if hasta is None else VistaSilenciosa()
    controlador = ControladorPartida(datos, fuente, cache, vista, cabecera.semilla,
                                     version_catalogo, CARPETA_PARTIDAS,
                                     checkpoint_cada=checkpoint_cada)
    pendientes = iter(comandos)
    controlador.jugar(lambda: next(pendientes, None))
    if hasta is not None:
        estado = controlador.estado
        if hasta > estado.tiempo:
            # la partida grabada terminó antes del instante pedido: se muestra el final
            for linea in lineas_historia(estado, f"t={hasta}", estado.tiempo):
                print(linea)
            print(f"La partida grabada termina en t={estado.tiempo}, antes de t={hasta}.")
        else:
            consultado, que, instante = controlador.consultar_historia(str(hasta))
            for linea in lineas_historia(consultado, que, instante):
                print(linea)
        return 0
    vista.mostrar_reporte(fuente.solicitudes_realizadas(), datos.presupuesto_solicitudes,
                          cache.aciertos, cache.fallos)
    return 0


def principal(argv=None):
    args = leer_argumentos(argv)

    if args.bench:
        from bench.bench import principal as correr_bench
        correr_bench()
        return 0

    fuente = crear_fuente(args.offline)
    try:
        if args.replay:
            return reproducir(args.replay, fuente, args.cache_size, args.hasta,
                              args.checkpoint_cada)
        if args.hasta is not None:
            print("--hasta se usa junto con --replay partida.log")
            return 1
        if args.verificar:
            return verificar(args.verificar, fuente)
        vista = Consola()
        # ninguna cripta queda escrita en el código: si no se indica, se elige de la lista
        cripta_id = args.cripta or vista.elegir_cripta(fuente.listar_criptas())
        if cripta_id is None:
            print("No se eligió ninguna cripta.")
            return 1
        return jugar(cripta_id, fuente, args.cache_size, args.semilla, vista, args.forzar,
                     args.checkpoint_cada)
    except ErrorPresupuesto as error:
        print(f"[PRESUPUESTO] {error}")
    except ErrorFuenteDatos as error:
        print(f"[ERROR] {error}")
    except ErrorBitacora as error:
        print(f"[REPLAY] {error}")
    except KeyboardInterrupt:
        # Ctrl+C fuera del juego (por ejemplo esperando a la red): se sale sin traza
        print()
        print("Partida interrumpida.")
    print(f"Solicitudes usadas: {fuente.solicitudes_realizadas()}")
    return 1


if __name__ == "__main__":
    sys.exit(principal())