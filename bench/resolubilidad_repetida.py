from estructuras.fila import Fila
from estructuras.vector_ordenado import VectorOrdenado


def verificar_repetido(esqueleto, ubicaciones, sala_inicial, sala_salida, llave_salida):
    """Alternativa ingenua que pide medir §5.4 (no la usa el juego): un recorrido
    completo desde la sala inicial con las llaves que se tienen; si encontró llaves
    nuevas, otro recorrido desde cero. Devuelve (resoluble, recorridos hechos)."""
    grafo = esqueleto.grafo()
    tengo = VectorOrdenado()
    recorridos = 0
    while True:
        recorridos += 1
        alcanzada = [False] * grafo.cantidad_salas()
        fila = Fila()
        inicio = grafo.indice(sala_inicial)
        alcanzada[inicio] = True
        fila.encolar(inicio)
        while not fila.esta_vacia():
            sala = fila.desencolar()
            for destino, _, salida in grafo.salientes[sala]:
                if alcanzada[destino]:
                    continue
                id_sala, direccion = grafo.salida_de[salida]
                dto = esqueleto.salida(id_sala, direccion)
                if not dto.cerrada or (dto.llave is not None and tengo.contiene(dto.llave)):
                    alcanzada[destino] = True
                    fila.encolar(destino)
        nuevas = False
        for ubicacion in ubicaciones:
            sala = grafo.indice(ubicacion.sala)
            if sala is not None and alcanzada[sala] and not tengo.contiene(ubicacion.id):
                tengo.insertar(ubicacion.id, True)
                nuevas = True
        if not nuevas:
            break
    salida_sala = grafo.indice(sala_salida)
    if not tengo.contiene(llave_salida):
        return False, recorridos
    for origen, _, salida in grafo.entrantes[salida_sala]:
        id_sala, direccion = grafo.salida_de[salida]
        dto = esqueleto.salida(id_sala, direccion)
        if alcanzada[origen] and dto.cerrada and dto.llave == llave_salida:
            return True, recorridos
    return False, recorridos
