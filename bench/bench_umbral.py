import random

from bench.cronometro import medir_us
from estructuras.ordenamientos import (UMBRAL_DESORDEN, UMBRAL_TAMANO, elegir_algoritmo,
                                       insertion_sort, merge_sort)


def _datos(tipo, n, azar):
    if tipo == "aleatorio":
        return [azar.randint(0, 10 ** 6) for _ in range(n)]
    if tipo == "inverso":
        return list(range(n, 0, -1))
    datos = list(range(n))
    # casi ordenado: se cambia de lugar un 2% de los elementos
    for _ in range(max(1, n * 2 // 100)):
        i, j = azar.randrange(n), azar.randrange(n)
        datos[i], datos[j] = datos[j], datos[i]
    return datos


def principal():
    print("== Alrededor del umbral de tamano (%d) y de desorden (%.0f%%): us por ordenamiento =="
          % (UMBRAL_TAMANO, UMBRAL_DESORDEN * 100))
    print("%-10s %6s %12s %12s %10s %10s" % ("datos", "n", "insercion", "merge", "gana", "elige"))
    clave = lambda x: x
    for tipo in ("aleatorio", "inverso", "casi 2%"):
        for n in (25, 50, 75, 100, 125, 150):
            datos = _datos(tipo, n, random.Random(n))
            insercion = medir_us(lambda _: insertion_sort(datos, clave), 200)
            merge = medir_us(lambda _: merge_sort(datos, clave), 200)
            gana = "insercion" if insercion < merge else "merge"
            print("%-10s %6d %12.2f %12.2f %10s %10s" % (tipo, n, insercion, merge, gana,
                                                         elegir_algoritmo(datos, clave)))


if __name__ == "__main__":
    principal()