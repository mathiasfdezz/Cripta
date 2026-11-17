from bench import (bench_agenda, bench_bitacora, bench_busqueda_cache, bench_cazadores, bench_ciclo,
                   bench_estructuras, bench_fichas_liberadas, bench_guardado, bench_mapa,
                   bench_linea_tiempo, bench_ordenamientos, bench_rastro, bench_resolubilidad,
                   bench_retroceso, bench_umbral)


def principal():
    print("### Agenda de eventos (4.1)")
    bench_agenda.principal()
    print("\n### Busqueda en la cache (4.3 y 4.4)")
    bench_busqueda_cache.principal()
    print()
    bench_fichas_liberadas.principal()
    print("\n### Estructuras (cache, inventario, agenda)")
    bench_estructuras.principal()
    print("\n### Retroceso (4.6)")
    bench_retroceso.principal()
    print("\n### Rastro (4.7)")
    bench_rastro.principal()
    print("\n### Bitacora en pantalla (4.8)")
    bench_bitacora.principal()
    print("\n### Ordenamientos (4.9)")
    bench_ordenamientos.principal()
    print()
    bench_umbral.principal()
    print("\n### Guardado binario vs JSON (4.10)")
    bench_guardado.principal()
    print("\n### Presupuesto de procesamiento (P1 5.2 y P2 6.1, con la carga nueva)")
    bench_ciclo.principal()
    print("\n### Segunda parte: ruta del cazador e invalidación (P2 5.1 y 5.2)")
    bench_cazadores.principal()
    print("\n### Segunda parte: mapa conocido e ir a (P2 5.3)")
    bench_mapa.principal()
    print("\n### Segunda parte: verificación de resolubilidad (P2 5.4)")
    bench_resolubilidad.principal()
    print("\n### Segunda parte: línea de tiempo y puntos de control (P2 5.5)")
    bench_linea_tiempo.principal()


if __name__ == "__main__":
    principal()