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


def ordenar(datos, clave, reverso=False):
    if len(datos) <= 10:
        return insertion_sort(datos, clave, reverso)
    return merge_sort(datos, clave, reverso)