import random

from estructuras.min_heap import MinHeap


def prueba_heap_vacio():
    h = MinHeap()
    assert h.esta_vacio() and h.tamano() == 0
    for operacion in (h.ver_minimo, h.extraer_minimo):
        try:
            operacion()
            assert False, "debió lanzar IndexError"
        except IndexError:
            pass


def prueba_ejemplo_del_juego():
    h = MinHeap()
    for e in [(100, 1), (66, 2), (80, 3), (300, 4)]:
        h.insertar(e)
    assert h.ver_minimo() == (66, 2)
    assert h.tamano() == 4
    salida = [h.extraer_minimo() for _ in range(4)]
    assert salida == [(66, 2), (80, 3), (100, 1), (300, 4)]
    assert h.esta_vacio()


def prueba_empate_por_secuencia():
    h = MinHeap()
    for e in [(100, 5), (100, 2), (100, 9), (50, 7)]:
        h.insertar(e)
    salida = [h.extraer_minimo() for _ in range(4)]
    assert salida == [(50, 7), (100, 2), (100, 5), (100, 9)]


def prueba_ver_minimo_no_saca():
    h = MinHeap()
    h.insertar((10, 1))
    h.insertar((5, 2))
    assert h.ver_minimo() == (5, 2)
    assert h.ver_minimo() == (5, 2)
    assert h.tamano() == 2


def prueba_intercalado():
    h = MinHeap()
    h.insertar((30, 1))
    h.insertar((10, 2))
    assert h.extraer_minimo() == (10, 2)
    h.insertar((20, 3))
    h.insertar((5, 4))
    assert h.extraer_minimo() == (5, 4)
    assert h.extraer_minimo() == (20, 3)
    assert h.extraer_minimo() == (30, 1)


def prueba_muchos_aleatorios():
    azar = random.Random(42)
    h = MinHeap()
    valores = [(azar.randint(0, 1000), sec) for sec in range(1000)]
    for v in valores:
        h.insertar(v)
    salida = [h.extraer_minimo() for _ in range(1000)]
    for i in range(1, len(salida)):
        assert salida[i - 1] < salida[i]


if __name__ == "__main__":
    pruebas = [prueba_heap_vacio, prueba_ejemplo_del_juego, prueba_empate_por_secuencia,
               prueba_ver_minimo_no_saca, prueba_intercalado, prueba_muchos_aleatorios]
    for prueba in pruebas:
        prueba()
        print(f"ok  {prueba.__name__}")
