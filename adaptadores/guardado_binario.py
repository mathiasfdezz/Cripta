import struct
import zlib

from estructuras.ordenamientos import ordenar

MAGIC = b"CRPT"
VERSION_FORMATO = 1
VIDA_DEL_CATALOGO = -1

_PREFIJO = struct.Struct("<4sHqqIQQ")
_ENTRADA_INDICE = struct.Struct("<iQI")
_CRC = struct.Struct("<I")


class GuardadoInvalido(Exception):
    """El archivo no es un guardado de Cripta o esta danado."""


class GuardadoIncompatible(Exception):
    """El archivo es de otra version del formato."""


class _Datos:
    _campos = ()

    def _tupla(self):
        return tuple(getattr(self, c) for c in self._campos)

    def __eq__(self, otro):
        return type(self) is type(otro) and self._tupla() == otro._tupla()

    def __repr__(self):
        return type(self).__name__ + repr(self._tupla())


class DatosCabecera(_Datos):
    _campos = ("cripta_id", "cripta_version", "catalogo_version", "semilla", "reloj")

    def __init__(self, cripta_id, cripta_version, catalogo_version, semilla, reloj):
        self.cripta_id = cripta_id
        self.cripta_version = cripta_version
        self.catalogo_version = catalogo_version
        self.semilla = semilla
        self.reloj = reloj


class DatosJugador(_Datos):
    _campos = ("vida", "sala", "tiempo_siguiente", "inventario")

    def __init__(self, vida, sala, tiempo_siguiente, inventario):
        self.vida = vida
        self.sala = sala
        self.tiempo_siguiente = tiempo_siguiente
        self.inventario = inventario


class DatosSala(_Datos):
    _campos = ("id", "rastro", "puertas", "objetos", "enemigos", "trampas")

    def __init__(self, id_sala, rastro, puertas, objetos, enemigos, trampas):
        self.id = id_sala
        self.rastro = rastro
        self.puertas = puertas
        self.objetos = objetos
        self.enemigos = enemigos
        self.trampas = trampas


def _cadena(texto):
    crudo = texto.encode("utf-8")
    return struct.pack("<H", len(crudo)) + crudo


def _leer_cadena(datos, pos):
    (largo,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    return datos[pos:pos + largo].decode("utf-8"), pos + largo


def _con_crc(payload):
    return payload + _CRC.pack(zlib.crc32(payload) & 0xFFFFFFFF)


def _verificar_crc(registro, que):
    payload, esperado = registro[:-4], _CRC.unpack(registro[-4:])[0]
    if (zlib.crc32(payload) & 0xFFFFFFFF) != esperado:
        raise GuardadoInvalido("registro danado (CRC) en " + que)
    return payload


def _empaquetar_jugador(j):
    partes = [struct.pack("<iiqH", j.vida, j.sala, j.tiempo_siguiente, len(j.inventario))]
    for id_obj, equipado in j.inventario:
        partes.append(_cadena(id_obj))
        partes.append(struct.pack("<B", 1 if equipado else 0))
    return _con_crc(b"".join(partes))


def _desempaquetar_jugador(registro):
    datos = _verificar_crc(registro, "jugador")
    vida, sala, tiempo, n = struct.unpack_from("<iiqH", datos, 0)
    pos = struct.calcsize("<iiqH")
    inventario = []
    for _ in range(n):
        id_obj, pos = _leer_cadena(datos, pos)
        (eq,) = struct.unpack_from("<B", datos, pos)
        pos += 1
        inventario.append((id_obj, bool(eq)))
    return DatosJugador(vida, sala, tiempo, inventario)


def _empaquetar_sala(s):
    p = [struct.pack("<iqH", s.id, s.rastro, len(s.puertas))]
    for direccion, abierta in s.puertas:
        p.append(direccion.encode("ascii") + struct.pack("<B", 1 if abierta else 0))
    p.append(struct.pack("<H", len(s.objetos)))
    for id_obj in s.objetos:
        p.append(_cadena(id_obj))
    p.append(struct.pack("<H", len(s.enemigos)))
    for inst, tipo, vida, tiempo, activo in s.enemigos:
        vida_guardada = VIDA_DEL_CATALOGO if vida is None else vida
        p.append(_cadena(inst) + _cadena(tipo) +
                 struct.pack("<iqB", vida_guardada, tiempo, 1 if activo else 0))
    p.append(struct.pack("<H", len(s.trampas)))
    for inst, tipo, armada in s.trampas:
        p.append(_cadena(inst) + _cadena(tipo) + struct.pack("<B", 1 if armada else 0))
    return _con_crc(b"".join(p))


def _desempaquetar_sala(registro):
    d = _verificar_crc(registro, "sala")
    id_sala, rastro, n_puertas = struct.unpack_from("<iqH", d, 0)
    pos = struct.calcsize("<iqH")
    puertas = []
    for _ in range(n_puertas):
        direccion = d[pos:pos + 1].decode("ascii")
        (abierta,) = struct.unpack_from("<B", d, pos + 1)
        pos += 2
        puertas.append((direccion, bool(abierta)))
    (n,) = struct.unpack_from("<H", d, pos); pos += 2
    objetos = []
    for _ in range(n):
        id_obj, pos = _leer_cadena(d, pos)
        objetos.append(id_obj)
    (n,) = struct.unpack_from("<H", d, pos); pos += 2
    enemigos = []
    for _ in range(n):
        inst, pos = _leer_cadena(d, pos)
        tipo, pos = _leer_cadena(d, pos)
        vida, tiempo, activo = struct.unpack_from("<iqB", d, pos)
        pos += struct.calcsize("<iqB")
        enemigos.append((inst, tipo, None if vida == VIDA_DEL_CATALOGO else vida,
                         tiempo, bool(activo)))
    (n,) = struct.unpack_from("<H", d, pos); pos += 2
    trampas = []
    for _ in range(n):
        inst, pos = _leer_cadena(d, pos)
        tipo, pos = _leer_cadena(d, pos)
        (armada,) = struct.unpack_from("<B", d, pos)
        pos += 1
        trampas.append((inst, tipo, bool(armada)))
    return DatosSala(id_sala, rastro, puertas, objetos, enemigos, trampas)


def guardar(ruta, cabecera, jugador, salas):
    """Escribe el archivo completo. 'salas' es una lista de DatosSala."""
    ordenadas = ordenar(salas, lambda s: s.id)

    cadenas = (_cadena(cabecera.cripta_id) + _cadena(cabecera.cripta_version) +
               _cadena(cabecera.catalogo_version))
    off_jugador = _PREFIJO.size + len(cadenas)
    registro_jugador = _empaquetar_jugador(jugador)

    cuerpo = []
    entradas = []
    offset = off_jugador + len(registro_jugador)
    for sala in ordenadas:
        reg = _empaquetar_sala(sala)
        entradas.append(_ENTRADA_INDICE.pack(sala.id, offset, len(reg)))
        cuerpo.append(reg)
        offset += len(reg)
    off_indice = offset

    prefijo = _PREFIJO.pack(MAGIC, VERSION_FORMATO, cabecera.semilla, cabecera.reloj,
                            len(ordenadas), off_jugador, off_indice)
    with open(ruta, "wb") as f:
        f.write(prefijo)
        f.write(cadenas)
        f.write(registro_jugador)
        for reg in cuerpo:
            f.write(reg)
        for entrada in entradas:
            f.write(entrada)


class ArchivoGuardado:

    def __init__(self, ruta):
        self._f = open(ruta, "rb")
        try:
            self._leer_prefijo()
        except Exception:
            self._f.close()
            raise

    def _leer_prefijo(self):
        crudo = self._f.read(_PREFIJO.size)
        if len(crudo) < _PREFIJO.size:
            raise GuardadoInvalido("archivo demasiado corto")
        (magic, version, semilla, reloj, n_salas,
         self._off_jugador, self._off_indice) = _PREFIJO.unpack(crudo)
        if magic != MAGIC:
            raise GuardadoInvalido("no es un guardado de Cripta")
        if version != VERSION_FORMATO:
            raise GuardadoIncompatible(
                "formato version %d; este programa lee la version %d"
                % (version, VERSION_FORMATO))
        self.n_salas = n_salas
        resto = self._f.read(self._off_jugador - _PREFIJO.size)
        cripta_id, pos = _leer_cadena(resto, 0)
        cripta_version, pos = _leer_cadena(resto, pos)
        catalogo_version, pos = _leer_cadena(resto, pos)
        self.cabecera = DatosCabecera(cripta_id, cripta_version, catalogo_version,
                                      semilla, reloj)

    def leer_jugador(self):
        if self.n_salas > 0:
            fin = self._entrada(0)[1]
        else:
            fin = self._off_indice
        self._f.seek(self._off_jugador)
        return _desempaquetar_jugador(self._f.read(fin - self._off_jugador))

    def _entrada(self, k):
        self._f.seek(self._off_indice + k * _ENTRADA_INDICE.size)
        return _ENTRADA_INDICE.unpack(self._f.read(_ENTRADA_INDICE.size))

    def _leer_indice(self):
        self._f.seek(self._off_indice)
        crudo = self._f.read(self.n_salas * _ENTRADA_INDICE.size)
        return list(_ENTRADA_INDICE.iter_unpack(crudo))

    def leer_sala(self, id_sala):
        bajo, alto = 0, self.n_salas - 1
        while bajo <= alto:
            medio = (bajo + alto) // 2
            id_medio, offset, largo = self._entrada(medio)
            if id_medio == id_sala:
                self._f.seek(offset)
                return _desempaquetar_sala(self._f.read(largo))
            if id_medio < id_sala:
                bajo = medio + 1
            else:
                alto = medio - 1
        return None

    def leer_todas(self):
        if self.n_salas == 0:
            return []
        indice = self._leer_indice()
        inicio = min(off for _, off, _ in indice)
        fin = max(off + largo for _, off, largo in indice)
        self._f.seek(inicio)
        bloque = self._f.read(fin - inicio)
        return [_desempaquetar_sala(bloque[off - inicio:off - inicio + largo])
                for _, off, largo in indice]

    def cerrar(self):
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cerrar()