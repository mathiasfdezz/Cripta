from estructuras.fila import Fila
from estructuras.vector_ordenado import VectorOrdenado

ANTIGUEDAD_MAXIMA = 400


def decidir_con_bfs(esqueleto, rastro, origen, ahora):
    """Alternativa descartada para el rastreador: recorre todo lo alcanzable desde su sala
    buscando el rastro fresco más reciente y devuelve el primer paso hacia él. Encuentra
    rastros lejanos, pero cuesta según el tamaño de la cripta."""
    visitadas = VectorOrdenado()
    fila = Fila()
    visitadas.insertar(origen, True)
    fila.encolar((origen, None))
    mejor, mejor_tiempo = None, None
    while not fila.esta_vacia():
        sala, primer_paso = fila.desencolar()
        tiempo = rastro.tiempo_en(sala)
        if (sala != origen and tiempo is not None and ahora - tiempo < ANTIGUEDAD_MAXIMA
                and (mejor_tiempo is None or tiempo > mejor_tiempo)):
            mejor, mejor_tiempo = primer_paso, tiempo
        for salida in esqueleto.obtener(sala).salidas:
            destino = salida.sala_destino
            if esqueleto.puede_atravesar(sala, salida.direccion) and visitadas.insertar(destino, True):
                fila.encolar((destino, destino if primer_paso is None else primer_paso))
    return mejor
