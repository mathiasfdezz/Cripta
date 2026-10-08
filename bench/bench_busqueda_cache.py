import random

from bench.arbol_binario import ArbolBinario
from bench.cronometro import medir_us
from estructuras.vector_ordenado import VectorOrdenado


def _ids(n):
    return ["itm_%05d" % i for i in range(n)]


def _armar(estructura, claves):
    for clave in claves:
        estructura.insertar(clave, clave)
    return estructura


def principal():
    print("== Buscar una ficha: vector ordenado vs arbol binario simple (us por busqueda) ==")
    print("%6s %-10s %12s %12s %14s" % ("fichas", "llegada", "vector", "arbol", "altura arbol"))
    for n in (25, 250, 2000):
        for llegada in ("al azar", "ordenada"):
            claves = _ids(n)
            if llegada == "al azar":
                random.Random(n).shuffle(claves)
            vector = _armar(VectorOrdenado(), claves)
            arbol = _armar(ArbolBinario(), claves)
            consultas = _ids(n)
            repeticiones = max(2000, n)
            t_vector = medir_us(lambda i: vector.buscar(consultas[i % n]), repeticiones)
            t_arbol = medir_us(lambda i: arbol.buscar(consultas[i % n]), repeticiones)
            print("%6d %-10s %12.2f %12.2f %14d" % (n, llegada, t_vector, t_arbol, arbol.altura()))


if __name__ == "__main__":
    principal()