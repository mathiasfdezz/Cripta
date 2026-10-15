from bench import (bench_agenda, bench_bitacora, bench_busqueda_cache, bench_ciclo,
                   bench_estructuras, bench_fichas_liberadas, bench_guardado, bench_ordenamientos,
                   bench_rastro, bench_retroceso, bench_umbral)


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
    print("\n### Presupuesto de procesamiento (5.2)")
    bench_ciclo.principal()


if __name__ == "__main__":
    principal()