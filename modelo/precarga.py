from estructuras.fila import Fila
from estructuras.vector_ordenado import VectorOrdenado

LOTE_CONTENIDO = 10   # GET /contenido acepta hasta 10 salas


def _recorrer(esqueleto, origen, ya_pedida, limite, solo_abiertas, elegidas, resultado):
    """BFS desde 'origen'. Agrega a 'resultado' las salas aun no pedidas,
    en orden de cercania, hasta llegar a 'limite'. Las salas ya pedidas se
    atraviesan (sirven de camino) pero no se vuelven a incluir."""
    visitadas = VectorOrdenado()
    cola = Fila()
    visitadas.insertar(origen, True)
    cola.encolar(origen)

    while not cola.esta_vacia() and len(resultado) < limite:
        actual = cola.desencolar()

        if not ya_pedida(actual) and not elegidas.contiene(actual):
            elegidas.insertar(actual, True)
            resultado.append(actual)

        sala = esqueleto.obtener(actual)
        if sala is None:
            continue
        for salida in sala.salidas:
            if solo_abiertas and salida.cerrada:
                continue
            if visitadas.insertar(salida.sala_destino, True):
                cola.encolar(salida.sala_destino)


def salas_a_precargar(esqueleto, origen, ya_pedida, limite=LOTE_CONTENIDO):
    """Ids de las salas mas cercanas a 'origen' cuyo contenido falta pedir.

    - Primero cuenta solo caminos por salidas abiertas.
    - Si no llega a 'limite', completa atravesando tambien las puertas
      cerradas con llave (el jugador puede abrirlas).
    - 'ya_pedida(id)' evita repetir salas ya solicitadas o cargadas.
    - 'origen' se incluye si aun no se pidio (distancia 0): garantiza que la
      sala donde esta el jugador siempre tenga su contenido.
    - Orden determinista: cercania, y a igual distancia el orden N, S, E, O.
    """
    elegidas = VectorOrdenado()
    resultado = []
    _recorrer(esqueleto, origen, ya_pedida, limite, True, elegidas, resultado)
    if len(resultado) < limite:
        _recorrer(esqueleto, origen, ya_pedida, limite, False, elegidas, resultado)
    return resultado
