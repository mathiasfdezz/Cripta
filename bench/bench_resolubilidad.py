import os
import time

from adaptadores.mapeadores.mapeador_salas import pagina_salas_desde_json
from bench.resolubilidad_repetida import verificar_repetido
from controlador.verificacion_cripta import VerificacionCripta
from dtos.ubicacion_llave import UbicacionLlave
from modelo.esqueleto import Esqueleto
from modelo.verificador_resolubilidad import VerificadorResolubilidad

LIMITE_MS = 200
POR_TRAMO = 6          # salas entre una puerta cerrada y la siguiente


def cripta_encadenada(llaves, por_tramo=POR_TRAMO):
    """Determinista: tramos de salas en fila; para pasar de un tramo al siguiente hay
    una puerta que pide la llave que está al principio del tramo anterior. La última
    llave es la de la salida. Devuelve (esqueleto, ubicaciones, inicial, salida, llave)."""
    salas = []
    ubicaciones = []
    total = llaves * por_tramo
    for numero in range(1, total + 1):
        salidas = {}
        if numero > 1:
            salidas["O"] = {"sala": numero - 1}
        if numero < total:
            salidas["E"] = {"sala": numero + 1}
            if numero % por_tramo == 0:
                salidas["E"].update({"cerrada": True, "llave": f"k{numero // por_tramo:05d}"})
        # en cada tramo, un desvío al norte con salas sin llave para que el mapa sea ancho
        salidas["N"] = {"sala": total + numero}
        salas.append({"id": numero, "nombre": f"S{numero}", "salidas": salidas})
        salas.append({"id": total + numero, "nombre": f"N{numero}",
                      "salidas": {"S": {"sala": numero}}})
        if numero % por_tramo == 1:
            ubicaciones.append(UbicacionLlave(f"k{numero // por_tramo + 1:05d}", numero))
    salida = 2 * total + 1
    salas[-2]["salidas"]["E"] = {"sala": salida, "cerrada": True, "llave": "negra"}
    salas.append({"id": salida, "nombre": "Salida", "salidas": {}})
    ubicaciones.append(UbicacionLlave("negra", total))
    esqueleto = Esqueleto()
    esqueleto.agregar_pagina(pagina_salas_desde_json({"pagina": 1, "total_paginas": 1,
                                                      "salas": salas}))
    return esqueleto, ubicaciones, 1, salida, "negra"


def medir_publicadas():
    print("== Verificación de las criptas publicadas (ms, límite %d en la más grande) ==" % LIMITE_MS)
    print("%-12s %7s %8s %7s %11s %10s" % ("cripta", "salas", "salidas", "llaves", "resoluble",
                                          "ms"))
    if not os.path.isdir("datos_offline"):
        return
    from adaptadores.cliente_offline import ClienteOffline
    fuente = ClienteOffline()
    for resumen in fuente.listar_criptas():
        datos = fuente.datos_cripta(resumen.id)
        inicio = time.perf_counter()
        _, reporte = VerificacionCripta.ejecutar(fuente, datos)
        total = (time.perf_counter() - inicio) * 1000
        # sin la lectura de archivos: solo el verificador (incluye armar los índices)
        esqueleto, _ = VerificacionCripta.ejecutar(fuente, datos)
        llaves = fuente.llaves(datos.id)
        inicio = time.perf_counter()
        VerificadorResolubilidad(esqueleto, llaves).verificar(
            datos.sala_inicial, datos.sala_salida, datos.llave_salida)
        solo = (time.perf_counter() - inicio) * 1000
        print("%-12s %7d %8d %7d %11s %10.2f   (con lectura de disco %.1f)"
              % (resumen.id, reporte.salas, reporte.salidas, reporte.llaves,
                 "si" if reporte.resoluble else "no", solo, total))


def comparar_incremental_repetido():
    print("\n== Llaves encadenadas: recorrido incremental frente a repetir el recorrido "
          "por llave (ms) ==")
    print("%-8s %7s %9s %13s %11s %10s %8s" % ("llaves", "salas", "salidas", "incremental",
                                              "repetido", "recorridos", "razón"))
    for llaves in (50, 200, 500):
        esqueleto, ubicaciones, inicial, salida, llave = cripta_encadenada(llaves)
        grafo = esqueleto.grafo()
        inicio = time.perf_counter()
        reporte = VerificadorResolubilidad(esqueleto, ubicaciones).verificar(inicial, salida, llave)
        incremental = (time.perf_counter() - inicio) * 1000
        inicio = time.perf_counter()
        resoluble, recorridos = verificar_repetido(esqueleto, ubicaciones, inicial, salida, llave)
        repetido = (time.perf_counter() - inicio) * 1000
        if resoluble != reporte.resoluble or not resoluble:
            raise AssertionError("las dos verificaciones no coinciden")
        print("%-8d %7d %9d %13.1f %11.1f %10d %8.0f"
              % (llaves, grafo.cantidad_salas(), grafo.cantidad_salidas(), incremental, repetido,
                 recorridos, repetido / incremental))
    print("(las dos alternativas dicen que es resoluble; el incremental hace un solo recorrido)")


def principal():
    medir_publicadas()
    comparar_incremental_repetido()


if __name__ == "__main__":
    principal()
