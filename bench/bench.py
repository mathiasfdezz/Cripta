from bench import bench_estructuras, bench_guardado, bench_ordenamientos


def principal():
    print("### Estructuras (cache, inventario, agenda)")
    bench_estructuras.principal()
    print("\n### Ordenamientos")
    bench_ordenamientos.principal()
    print("\n### Guardado binario vs JSON")
    bench_guardado.principal()


if __name__ == "__main__":
    principal()