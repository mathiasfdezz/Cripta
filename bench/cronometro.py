import time


def medir_us(funcion, repeticiones):
    """Microsegundos promedio por llamada de funcion(i)."""
    inicio = time.perf_counter()
    for i in range(repeticiones):
        funcion(i)
    return (time.perf_counter() - inicio) / repeticiones * 1e6