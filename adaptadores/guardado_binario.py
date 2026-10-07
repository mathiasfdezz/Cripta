import struct
import zlib

from estructuras.ordenamientos import ordenar

MAGIC = b"CRPT"
VERSION_FORMATO = 2
VIDA_DEL_CATALOGO = -1
NINGUNO = -1   # rastro, antorcha o cursor que no existen

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
    """Registro del jugador y de lo global de la partida: contadores, agenda
    pendiente y estado del azar, para que al cargar se siga exactamente igual."""
    _campos = ("vida", "sala", "tiempo_siguiente", "inventario", "velocidad", "cursor",
               "acciones", "enemigos_derrotados", "salida_abierta", "antorcha_hasta",
               "siguiente_secuencia", "azar", "eventos", "bitacora", "comandos")

    def __init__(self, vida, sala, tiempo_siguiente, inventario, velocidad=100, cursor=NINGUNO,
                 acciones=0, enemigos_derrotados=0, salida_abierta=False, antorcha_hasta=None,
                 siguiente_secuencia=1, azar=None, eventos=(), bitacora="", comandos=0):
        self.vida = vida
        self.sala = sala
        self.tiempo_siguiente = tiempo_siguiente
        self.inventario = inventario
        self.velocidad = velocidad
        self.cursor = cursor
        self.acciones = acciones
        self.enemigos_derrotados = enemigos_derrotados
        self.salida_abierta = salida_abierta
        self.antorcha_hasta = antorcha_hasta
        self.siguiente_secuencia = siguiente_secuencia
        self.azar = azar                    # lo que devuelve random.Random.getstate()
        self.eventos = list(eventos)        # [(tiempo, secuencia, tipo, objetivo, dato)]
        self.bitacora = bitacora            # bitácora de la partida y cuántos comandos
        self.comandos = comandos            # tenía al guardar, para que el replay siga


class DatosSala(_Datos):
    _campos = ("id", "rastro", "puertas", "objetos", "enemigos", "trampas", "cargada")

    def __init__(self, id_sala, rastro, puertas, objetos, enemigos, trampas, cargada=True):
        self.id = id_sala
        self.rastro = rastro
        self.puertas = puertas
        self.objetos = objetos
        self.enemigos = enemigos
        self.trampas = trampas
        self.cargada = cargada   # False: solo está porque hay un enemigo que llegó ahí


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


def _opcional(valor):
    return NINGUNO if valor is None else valor


def _empaquetar_azar(azar):
    if azar is None:
        return struct.pack("<B", 0)
    version, internos, gauss = azar
    partes = [struct.pack("<BBH", 1, version, len(internos)),
              struct.pack("<%dI" % len(internos), *internos)]
    partes.append(struct.pack("<Bd", 0, 0.0) if gauss is None else struct.pack("<Bd", 1, gauss))
    return b"".join(partes)


def _desempaquetar_azar(datos, pos):
    (hay,) = struct.unpack_from("<B", datos, pos)
    pos += 1
    if not hay:
        return None, pos
    version, n = struct.unpack_from("<BH", datos, pos)
    pos += struct.calcsize("<BH")
    internos = struct.unpack_from("<%dI" % n, datos, pos)
    pos += 4 * n
    hay_gauss, gauss = struct.unpack_from("<Bd", datos, pos)
    pos += struct.calcsize("<Bd")
    return (version, internos, gauss if hay_gauss else None), pos


def _empaquetar_jugador(j):
    partes = [struct.pack("<iiqH", j.vida, j.sala, j.tiempo_siguiente, len(j.inventario))]
    for id_obj, equipado in j.inventario:
        partes.append(_cadena(id_obj))
        partes.append(struct.pack("<B", 1 if equipado else 0))
    partes.append(struct.pack("<iiiiBqq", j.velocidad, j.cursor, j.acciones,
                              j.enemigos_derrotados, 1 if j.salida_abierta else 0,
                              _opcional(j.antorcha_hasta), j.siguiente_secuencia))
    partes.append(_empaquetar_azar(j.azar))
    partes.append(struct.pack("<H", len(j.eventos)))
    for tiempo, secuencia, tipo, objetivo, dato in j.eventos:
        partes.append(struct.pack("<qq", tiempo, secuencia) + _cadena(tipo) + _cadena(objetivo)
                      + struct.pack("<Bq", 0 if dato is None else 1, 0 if dato is None else dato))
    partes.append(_cadena(j.bitacora) + struct.pack("<I", j.comandos))
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
    (velocidad, cursor, acciones, enemigos, salida_abierta, antorcha,
     secuencia) = struct.unpack_from("<iiiiBqq", datos, pos)
    pos += struct.calcsize("<iiiiBqq")
    azar, pos = _desempaquetar_azar(datos, pos)
    (n,) = struct.unpack_from("<H", datos, pos)
    pos += 2
    eventos = []
    for _ in range(n):
        tiempo_evento, secuencia_evento = struct.unpack_from("<qq", datos, pos)
        pos += 16
        tipo, pos = _leer_cadena(datos, pos)
        objetivo, pos = _leer_cadena(datos, pos)
        hay_dato, dato = struct.unpack_from("<Bq", datos, pos)
        pos += struct.calcsize("<Bq")
        eventos.append((tiempo_evento, secuencia_evento, tipo, objetivo, dato if hay_dato else None))
    bitacora, pos = _leer_cadena(datos, pos)
    (comandos,) = struct.unpack_from("<I", datos, pos)
    return DatosJugador(vida, sala, tiempo, inventario, velocidad, cursor, acciones, enemigos,
                        bool(salida_abierta), None if antorcha == NINGUNO else antorcha,
                        secuencia, azar, eventos, bitacora, comandos)


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
    p.append(struct.pack("<B", 1 if s.cargada else 0))
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
    (cargada,) = struct.unpack_from("<B", d, pos)
    return DatosSala(id_sala, rastro, puertas, objetos, enemigos, trampas, bool(cargada))


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