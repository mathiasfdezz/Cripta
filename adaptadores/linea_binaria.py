import struct

from adaptadores.guardado_binario import GuardadoInvalido
from dtos.contenido_sala import ContenidoSala
from dtos.instancia_enemigo import InstanciaEnemigo
from dtos.instancia_trampa import InstanciaTrampa
from modelo.linea_tiempo import (ACCION, AVANZAR, CONTENIDO, CURSOR, INICIAR, PERGAMINO,
                                 SIGUIENTE)

# un byte por operación en el archivo (formato 5)
CODIGOS = ((CONTENIDO, 1), (INICIAR, 2), (ACCION, 3), (AVANZAR, 4), (CURSOR, 5),
           (PERGAMINO, 6), (SIGUIENTE, 7))
SIN_VIDA = -1


def _codigo(tipo):
    for nombre, codigo in CODIGOS:
        if nombre == tipo:
            return codigo
    raise ValueError(f"operación sin código: {tipo}")


def _tipo(codigo):
    for nombre, valor in CODIGOS:
        if valor == codigo:
            return nombre
    raise GuardadoInvalido(f"operación desconocida en la línea de tiempo: {codigo}")


def _cadena(texto):
    crudo = (texto or "").encode("utf-8")
    return struct.pack("<H", len(crudo)) + crudo


def _leer_cadena(datos, pos):
    (largo,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    return bytes(datos[pos:pos + largo]).decode("utf-8"), pos + largo


def empaquetar_linea(linea):
    """K y las operaciones de la línea de tiempo, en bytes."""
    partes = [struct.pack("<II", linea.cada, len(linea.operaciones))]
    for operacion in linea.operaciones:
        tipo = operacion[0]
        partes.append(struct.pack("<B", _codigo(tipo)))
        if tipo == ACCION:
            partes.append(_cadena(operacion[1]))
            partes.append(struct.pack("<B", operacion[2] is not None) + _cadena(operacion[2]))
        elif tipo == CURSOR:
            partes.append(struct.pack("<b", operacion[1]))
        elif tipo == CONTENIDO:
            partes.append(_contenido(operacion[1]))
    return b"".join(partes)


def _contenido(contenido):
    partes = [struct.pack("<iH", contenido.sala, len(contenido.enemigos))]
    for enemigo in contenido.enemigos:
        vida = SIN_VIDA if enemigo.vida is None else enemigo.vida
        partes.append(_cadena(enemigo.instancia) + _cadena(enemigo.tipo) + struct.pack("<i", vida))
    partes.append(struct.pack("<H", len(contenido.objetos)))
    for objeto in contenido.objetos:
        partes.append(_cadena(objeto))
    partes.append(struct.pack("<H", len(contenido.trampas)))
    for trampa in contenido.trampas:
        partes.append(_cadena(trampa.instancia) + _cadena(trampa.tipo))
    return b"".join(partes)


def desempaquetar_linea(datos):
    """(K, operaciones) desde los bytes de empaquetar_linea."""
    try:
        cada, cantidad = struct.unpack_from("<II", datos, 0)
        pos = 8
        operaciones = []
        for _ in range(cantidad):
            tipo = _tipo(datos[pos])
            pos += 1
            if tipo == ACCION:
                nombre, pos = _leer_cadena(datos, pos)
                hay = datos[pos] != 0
                argumento, pos = _leer_cadena(datos, pos + 1)
                operaciones.append((ACCION, nombre, argumento if hay else None))
            elif tipo == CURSOR:
                (paso,) = struct.unpack_from("<b", datos, pos)
                pos += 1
                operaciones.append((CURSOR, paso))
            elif tipo == CONTENIDO:
                contenido, pos = _leer_contenido(datos, pos)
                operaciones.append((CONTENIDO, contenido))
            else:
                operaciones.append((tipo,))
        return cada, operaciones
    except (struct.error, IndexError, UnicodeDecodeError) as error:
        raise GuardadoInvalido(f"línea de tiempo dañada ({error})")


def _leer_contenido(datos, pos):
    sala, n = struct.unpack_from("<iH", datos, pos)
    pos += 6
    enemigos = []
    for _ in range(n):
        instancia, pos = _leer_cadena(datos, pos)
        tipo, pos = _leer_cadena(datos, pos)
        (vida,) = struct.unpack_from("<i", datos, pos)
        pos += 4
        enemigos.append(InstanciaEnemigo(instancia, tipo, None if vida == SIN_VIDA else vida))
    (n,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    objetos = []
    for _ in range(n):
        objeto, pos = _leer_cadena(datos, pos)
        objetos.append(objeto)
    (n,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    trampas = []
    for _ in range(n):
        instancia, pos = _leer_cadena(datos, pos)
        tipo, pos = _leer_cadena(datos, pos)
        trampas.append(InstanciaTrampa(instancia, tipo))
    return ContenidoSala(sala, tuple(enemigos), tuple(objetos), tuple(trampas)), pos
