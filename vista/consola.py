class Consola:

    def mostrar_mensaje(self, texto):
        print(texto)

    def mostrar_objeto_actual(self, objeto):
        if objeto is None:
            print("No hay objeto seleccionado.")
            return
        print(f"Objeto actual: {objeto.nombre} | Peso: {objeto.peso} | Valor: {objeto.valor}")

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

    def mostrar_inventario_detallado(self, pares):
        print("\n--- Inventario ---")
        for objeto, equipado in pares:
            marca = " [equipado]" if equipado else ""
            print(f"{objeto.nombre}{marca} | Peso: {objeto.peso} | Valor: {objeto.valor}")
        print("------------------")

    def mostrar_bitacora(self, mensajes):
        print("\n--- Ultimos mensajes ---")
        for mensaje in mensajes:
            print(mensaje)
        print("------------------------")