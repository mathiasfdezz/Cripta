class Consola:

    def mostrar_objeto_actual(self, objeto):
        if objeto is None:
            print("No hay objeto seleccionado.")
            return

        print(
            f"Objeto actual: {objeto.nombre} "
            f"| Peso: {objeto.peso} "
            f"| Valor: {objeto.valor}"
        )

    def mostrar_objeto_soltado(self, objeto):
        if objeto is None:
            print("No hay objeto para soltar.")
            return

        print(f"Objeto soltado: {objeto.nombre}")

    def mostrar_objeto_equipado(self, objeto):
        if objeto is None:
            print("No hay objeto para equipar.")
            return

        print(f"Objeto equipado: {objeto.nombre}")

    def mostrar_inventario(self, objetos):
        print("\n--- Inventario ---")

        for objeto in objetos:
            print(
                f"{objeto.nombre} | "
                f"Peso: {objeto.peso} | "
                f"Valor: {objeto.valor}"
            )

        print("------------------")