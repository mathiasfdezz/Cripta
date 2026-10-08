def insertion_sort(datos, clave, reverso=False):
    resultado = datos[:]

    for i in range(1, len(resultado)):
        actual = resultado[i]
        valor_actual = clave(actual)
        j = i - 1

        while j >= 0:
            valor_j = clave(resultado[j])

            if reverso:
                if valor_j >= valor_actual:
                    break
            else:
                if valor_j <= valor_actual:
                    break

            resultado[j + 1] = resultado[j]
            j -= 1

        resultado[j + 1] = actual

    return resultado


def merge_sort(datos, clave, reverso=False):
    if len(datos) <= 1:
        return datos[:]

    medio = len(datos) // 2
    izquierda = merge_sort(datos[:medio], clave, reverso)
    derecha = merge_sort(datos[medio:], clave, reverso)
    return _merge(izquierda, derecha, clave, reverso)


def _merge(izquierda, derecha, clave, reverso):
    resultado = []
    i = 0
    j = 0

    while i < len(izquierda) and j < len(derecha):
        valor_izquierda = clave(izquierda[i])
        valor_derecha = clave(derecha[j])

        if reverso:
            tomar_izquierda = valor_izquierda >= valor_derecha
        else:
            tomar_izquierda = valor_izquierda <= valor_derecha

        if tomar_izquierda:
            resultado.append(izquierda[i])
            i += 1
        else:
            resultado.append(derecha[j])
            j += 1

    while i < len(izquierda):
        resultado.append(izquierda[i])
        i += 1

    while j < len(derecha):
        resultado.append(derecha[j])
        j += 1

    return resultado

UMBRAL_TAMANO = 50
UMBRAL_DESORDEN = 0.05

ALGORITMO_INSERCION = "insercion"
ALGORITMO_MERGE = "merge"


def proporcion_desorden(datos, clave, reverso=False):
    n = len(datos)
    if n < 2:
        return 0.0
    descensos = 0
    previo = clave(datos[0])
    for k in range(1, n):
        actual = clave(datos[k])
        if reverso:
            if actual > previo:
                descensos += 1
        else:
            if actual < previo:
                descensos += 1
        previo = actual
    return descensos / (n - 1)


def elegir_algoritmo(datos, clave, reverso=False):
    if len(datos) <= UMBRAL_TAMANO:
        return ALGORITMO_INSERCION
    if proporcion_desorden(datos, clave, reverso) <= UMBRAL_DESORDEN:
        return ALGORITMO_INSERCION
    return ALGORITMO_MERGE


def ordenar(datos, clave, reverso=False):
    if elegir_algoritmo(datos, clave, reverso) == ALGORITMO_INSERCION:
        return insertion_sort(datos, clave, reverso)
    return merge_sort(datos, clave, reverso)