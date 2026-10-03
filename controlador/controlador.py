class Controlador:

    def __init__(self, inventario, vista):
        self.inventario = inventario
        self.vista = vista

    def avanzar_inventario(self):
        objeto = self.inventario.avanzar()
        self.vista.mostrar_objeto_actual(objeto)

    def retroceder_inventario(self):
        objeto = self.inventario.retroceder()
        self.vista.mostrar_objeto_actual(objeto)

    def soltar_objeto(self):
        objeto = self.inventario.soltar_actual()
        self.vista.mostrar_objeto_soltado(objeto)

    def equipar_objeto(self):
        objeto = self.inventario.equipar_actual()
        self.vista.mostrar_objeto_equipado(objeto)

    def mostrar_inventario_por_peso(self):
        objetos = self.inventario.vista_por_peso()
        self.vista.mostrar_inventario(objetos)

    def mostrar_inventario_por_valor(self):
        objetos = self.inventario.vista_por_valor()
        self.vista.mostrar_inventario(objetos)

    def mostrar_inventario_por_nombre(self):
        objetos = self.inventario.vista_por_nombre()
        self.vista.mostrar_inventario(objetos)