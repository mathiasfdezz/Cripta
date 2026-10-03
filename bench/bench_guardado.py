import json
import os
import random
import tempfile
import time

from adaptadores.guardado_binario import (
    ArchivoGuardado, DatosCabecera, DatosJugador, DatosSala, guardar)


def estado_sintetico(n_salas, azar):
    salas = []
    for i in range(1, n_salas + 1):
        salas.append(DatosSala(
            i, azar.choice([-1, 0, 250, 1000]),
            [("N", True), ("E", False)],
            ["itm_antorcha"] * azar.randrange(3),
            [("e-%d" % (i * 10 + k), "ent_rata_gigante", azar.randrange(1, 13),
              azar.randrange(0, 5000), bool(k % 2)) for k in range(azar.randrange(4))],
            [("t-%d" % i, "trp_dardos", bool(i % 2))]))
    jugador = DatosJugador(23, 1, 1450, [("itm_daga_oxidada", True),
                                         ("itm_pocion_menor", False)])
    cab = DatosCabecera("cripta-01", "a3f91c", "cat-2026-08-01", 12345, 1450)
    return cab, jugador, salas


def a_json(cab, jug, salas):
    return json.dumps({
        "cabecera": {"cripta_id": cab.cripta_id, "cripta_version": cab.cripta_version,
                     "catalogo_version": cab.catalogo_version,
                     "semilla": cab.semilla, "reloj": cab.reloj},
        "jugador": {"vida": jug.vida, "sala": jug.sala,
                    "tiempo_siguiente": jug.tiempo_siguiente,
                    "inventario": [list(x) for x in jug.inventario]},
        "salas": [{"id": s.id, "rastro": s.rastro,
                   "puertas": [list(p) for p in s.puertas], "objetos": s.objetos,
                   "enemigos": [list(e) for e in s.enemigos],
                   "trampas": [list(t) for t in s.trampas]} for s in salas]})


def mejor(fn, reps):
    m = None
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        dt = time.perf_counter() - t0
        m = dt if m is None or dt < m else m
    return m * 1000.0


def principal():
    carpeta = tempfile.mkdtemp()
    print("%8s | %10s %10s | %12s %12s | %14s %14s" % (
        "salas", "bin (B)", "json (B)", "carga bin ms", "carga json ms",
        "1 sala bin ms", "1 sala json ms"))
    for n in (20, 200, 2000, 20000):
        azar = random.Random(7)
        cab, jug, salas = estado_sintetico(n, azar)
        rb = os.path.join(carpeta, "p%d.sav" % n)
        rj = os.path.join(carpeta, "p%d.json" % n)
        guardar(rb, cab, jug, salas)
        with open(rj, "w", encoding="utf-8") as f:
            f.write(a_json(cab, jug, salas))
        reps = 20 if n <= 2000 else 3
        objetivo = n // 2

        def carga_bin():
            with ArchivoGuardado(rb) as a:
                a.leer_jugador()
                a.leer_todas()

        def carga_json():
            with open(rj, "r", encoding="utf-8") as f:
                json.load(f)

        def una_bin():
            with ArchivoGuardado(rb) as a:
                a.leer_sala(objetivo)

        def una_json():          # JSON obliga a cargar todo para ver una sala
            with open(rj, "r", encoding="utf-8") as f:
                datos = json.load(f)
            for s in datos["salas"]:
                if s["id"] == objetivo:
                    break

        print("%8d | %10d %10d | %12.3f %12.3f | %14.4f %14.3f" % (
            n, os.path.getsize(rb), os.path.getsize(rj), mejor(carga_bin, reps),
            mejor(carga_json, reps), mejor(una_bin, reps * 5), mejor(una_json, reps)))


if __name__ == "__main__":
    principal()
