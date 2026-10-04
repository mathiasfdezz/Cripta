from bench import bench_guardado, bench_ordenamientos


def principal():
    print("### Ordenamientos")
    bench_ordenamientos.principal()
    print("\n### Guardado binario vs JSON")
    bench_guardado.principal()


if __name__ == "__main__":
    principal()