import random
import time

from estructuras.ordenamientos import insertion_sort, merge_sort


def _casi_ordenado(n, desorden, azar):
    datos = list(range(n))
    for _ in range(int(n * desorden)):
        i = azar.randrange(n)
        j = azar.randrange(n)
        datos[i], datos[j] = datos[j], datos[i]
    return datos


def generar(tipo, n, azar):
    if tipo == "aleatorio":
        datos = list(range(n))
        azar.shuffle(datos)
        return datos
    if tipo == "ordenado":
        return list(range(n))
    if tipo == "inverso":
        return list(range(n, 0, -1))
    if tipo == "casi 2%":
        return _casi_ordenado(n, 0.02, azar)
    if tipo == "casi 10%":
        return _casi_ordenado(n, 0.10, azar)
    raise ValueError(tipo)


def clave_barata(x):
    return x


def clave_costosa(x):
    total = 0
    for _ in range(40):
        total += x % 7
    return x * 1000 + total


def medir(funcion, datos, clave, repeticiones):
    mejor = None
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        funcion(datos, clave)
        dt = time.perf_counter() - t0
        if mejor is None or dt < mejor:
            mejor = dt
    return mejor * 1000.0   # ms


def contar_llamadas(funcion, datos):
    cuenta = [0]

    def clave(x):
        cuenta[0] += 1
        return x
    funcion(datos, clave)
    return cuenta[0]


def principal():
    azar = random.Random(42)
    tipos = ["aleatorio", "ordenado", "inverso", "casi 2%", "casi 10%"]

    print("== Tiempo (ms) por tamano y tipo de dato, clave barata ==")
    print("%-10s %6s %12s %12s  %s" % ("datos", "n", "insercion", "merge", "gana"))
    for n in (5, 10, 20, 50, 200, 1000):
        for tipo in tipos:
            datos = generar(tipo, n, azar)
            reps = 200 if n <= 50 else (20 if n <= 200 else 3)
            a = medir(insertion_sort, datos, clave_barata, reps)
            b = medir(merge_sort, datos, clave_barata, reps)
            print("%-10s %6d %12.4f %12.4f  %s" %
                  (tipo, n, a, b, "insercion" if a < b else "merge"))

    print("\n== Llamadas a clave() (proxy de comparaciones costosas), n=1000 ==")
    for tipo in tipos:
        datos = generar(tipo, 1000, azar)
        print("%-10s insercion=%8d  merge=%8d" %
              (tipo, contar_llamadas(insertion_sort, datos),
               contar_llamadas(merge_sort, datos)))

    print("\n== Tiempo (ms) con clave COSTOSA, n=200 ==")
    for tipo in tipos:
        datos = generar(tipo, 200, azar)
        a = medir(insertion_sort, datos, clave_costosa, 5)
        b = medir(merge_sort, datos, clave_costosa, 5)
        print("%-10s insercion=%9.3f  merge=%9.3f" % (tipo, a, b))


if __name__ == "__main__":
    principal()
