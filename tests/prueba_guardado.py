import os
import random
import shutil
import struct
import tempfile

from adaptadores.guardado_binario import (
    ArchivoGuardado, DatosCabecera, DatosJugador, DatosSala, GuardadoIncompatible,
    GuardadoInvalido, VERSION_FORMATO, guardar)


def estado(n_salas, azar):
    ids = list(range(1, n_salas * 3, 3))          # ids no contiguos
    azar.shuffle(ids)                             # fuera de orden a proposito
    salas = []
    for i in ids:
        salas.append(DatosSala(
            i, azar.choice([-1, 0, 250, 1000]),
            [("N", True), ("E", False)],
            ["itm_antorcha"] * azar.randrange(3),
            [("e-%d" % (i * 10 + k), "ent_rata_gigante", azar.randrange(1, 13),
              azar.randrange(0, 5000), bool(k % 2)) for k in range(azar.randrange(3))],
            [("t-%d" % i, "trp_dardos", bool(i % 2))]))
    jugador = DatosJugador(23, ids[0], 1450,
                           [("itm_daga_oxidada", True), ("itm_pocion_menor", False),
                            ("itm_pergamino", False)])
    cab = DatosCabecera("cripta-01", "a3f91c", "cat-2026-08-01", 12345, 1450)
    return cab, jugador, salas


def con_archivo(fn):
    carpeta = tempfile.mkdtemp()
    try:
        fn(os.path.join(carpeta, "partida.sav"))
    finally:
        shutil.rmtree(carpeta)


def test_ida_y_vuelta_completa():
    def caso(ruta):
        cab, jug, salas = estado(30, random.Random(1))
        guardar(ruta, cab, jug, salas)
        with ArchivoGuardado(ruta) as a:
            assert a.cabecera == cab and a.n_salas == 30
            assert a.leer_jugador() == jug
            leidas = a.leer_todas()
        esperadas = sorted(salas, key=lambda s: s.id)
        assert leidas == esperadas
    con_archivo(caso)


def test_leer_una_sala_sin_leer_todo():
    def caso(ruta):
        cab, jug, salas = estado(200, random.Random(2))
        guardar(ruta, cab, jug, salas)
        with ArchivoGuardado(ruta) as a:
            leidos = [0]
            real = a._f.read
            def contado(n=-1):
                leidos[0] += n if n > 0 else 10**9
                return real(n)
            a._f.read = contado
            objetivo = salas[77]
            assert a.leer_sala(objetivo.id) == objetivo
            assert leidos[0] < os.path.getsize(ruta) / 5   # una fraccion minima
            assert a.leer_sala(2) is None                  # id inexistente
    con_archivo(caso)


def test_version_de_formato_incompatible():
    def caso(ruta):
        cab, jug, salas = estado(3, random.Random(3))
        guardar(ruta, cab, jug, salas)
        with open(ruta, "r+b") as f:                       # cambia la version
            f.seek(4)
            f.write(struct.pack("<H", VERSION_FORMATO + 1))
        try:
            ArchivoGuardado(ruta)
            assert False
        except GuardadoIncompatible as e:
            assert str(VERSION_FORMATO) in str(e)
    con_archivo(caso)


def test_archivo_que_no_es_guardado_o_danado():
    def caso(ruta):
        with open(ruta, "wb") as f:
            f.write(b"hola mundo, esto no es un guardado" * 3)
        try:
            ArchivoGuardado(ruta); assert False
        except GuardadoInvalido:
            pass
        cab, jug, salas = estado(5, random.Random(4))
        guardar(ruta, cab, jug, salas)
        crudo = bytearray(open(ruta, "rb").read())
        crudo[len(crudo) - 16 * 5 - 6] ^= 0xFF              # corrompe una sala
        open(ruta, "wb").write(bytes(crudo))
        with ArchivoGuardado(ruta) as a:
            try:
                a.leer_todas(); assert False
            except GuardadoInvalido:
                pass
    con_archivo(caso)


def test_cripta_sin_salas_y_caracteres_unicode():
    def caso(ruta):
        cab = DatosCabecera("cripta-\u00f1", "v\u00e1", "cat", -7, 0)
        jug = DatosJugador(1, 1, 0, [("itm_poci\u00f3n", False)])
        guardar(ruta, cab, jug, [])
        with ArchivoGuardado(ruta) as a:
            assert a.cabecera == cab and a.leer_jugador() == jug
            assert a.leer_todas() == [] and a.leer_sala(1) is None
    con_archivo(caso)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_"):
            fn()
            print("OK ", nombre)
    print("Todas las pruebas pasaron")
