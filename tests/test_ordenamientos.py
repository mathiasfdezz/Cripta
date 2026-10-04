import random
import unittest

from estructuras.ordenamientos import (
    ALGORITMO_INSERCION, ALGORITMO_MERGE, elegir_algoritmo, insertion_sort,
    merge_sort, ordenar, proporcion_desorden)


def ident(x):
    return x


def casos(azar):
    yield []
    yield [1]
    yield [2, 1]
    yield [3, 3, 3]
    for n in (5, 20, 21, 100, 333):
        d = list(range(n)); azar.shuffle(d); yield d
        yield list(range(n))
        yield list(range(n, 0, -1))
        yield [azar.randrange(5) for _ in range(n)]   # muchos repetidos


class PruebasOrdenamientos(unittest.TestCase):

    def test_correctitud_contra_referencia(self):
        # sorted() solo se usa aqui como ORACULO de la prueba, no en el programa.
        azar = random.Random(1)
        for d in casos(azar):
            for f in (insertion_sort, merge_sort, ordenar):
                assert f(d, ident) == sorted(d)
                assert f(d, ident, reverso=True) == sorted(d, reverse=True)

    def test_no_modifica_la_entrada(self):
        d = [3, 1, 2]
        for f in (insertion_sort, merge_sort, ordenar):
            f(d, ident)
            assert d == [3, 1, 2]

    def test_estabilidad(self):
        pares = [(1, "a"), (0, "b"), (1, "c"), (0, "d"), (1, "e")] * 10
        esperado = sorted(pares, key=lambda p: p[0])            # estable
        esperado_rev = sorted(pares, key=lambda p: p[0], reverse=True)
        for f in (insertion_sort, merge_sort, ordenar):
            assert f(pares, lambda p: p[0]) == esperado
            assert f(pares, lambda p: p[0], reverso=True) == esperado_rev

    def test_selector(self):
        azar = random.Random(2)
        aleatorio = list(range(500)); azar.shuffle(aleatorio)
        assert elegir_algoritmo([5, 4, 3, 2, 1], ident) == ALGORITMO_INSERCION
        assert elegir_algoritmo(list(range(500)), ident) == ALGORITMO_INSERCION
        assert elegir_algoritmo(aleatorio, ident) == ALGORITMO_MERGE
        assert elegir_algoritmo(list(range(500, 0, -1)), ident) == ALGORITMO_MERGE
        # el sentido importa: descendente ya ordenado + reverso=True -> insercion
        assert elegir_algoritmo(list(range(500, 0, -1)), ident, True) == ALGORITMO_INSERCION
        assert proporcion_desorden([1, 2, 3], ident) == 0.0
        assert proporcion_desorden([3, 2, 1], ident) == 1.0
        assert proporcion_desorden([], ident) == 0.0

    def test_clave_por_nombre_sin_mayusculas(self):
        nombres = ["pocion", "Antorcha", "espada", "Daga"]
        r = ordenar(nombres, lambda s: s.lower())
        assert r == ["Antorcha", "Daga", "espada", "pocion"]


if __name__ == "__main__":
    unittest.main()
