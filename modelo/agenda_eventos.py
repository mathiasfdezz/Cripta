from estructuras.min_heap import MinHeap
from modelo.evento import Evento


class AgendaEventos:
    def __init__(self):
        self._heap = MinHeap()
        self._siguiente_secuencia = 1
        # cuántos eventos cancelados siguen dentro del heap sin haber sido descartados
        self._cancelados_en_heap = 0

    def programar(self, tiempo, evento):
        secuencia = self._siguiente_secuencia
        self._siguiente_secuencia += 1
        evento.tiempo_siguiente = tiempo
        evento.secuencia = secuencia
        evento.en_agenda = True
        # la secuencia nunca se repite, así que nunca se llega a comparar el evento
        self._heap.insertar((tiempo, secuencia, evento))
        return secuencia

    def cancelar(self, evento):
        # no se busca en el heap: solo se marca, y se descarta al llegar a la raíz
        if evento.cancelado or not evento.en_agenda:
            return False
        evento.cancelado = True
        self._cancelados_en_heap += 1
        return True

    def reprogramar(self, evento, tiempo):
        # la versión anterior queda cancelada y la nueva entra con secuencia nueva
        self.cancelar(evento)
        nuevo = Evento(evento.tipo, evento.objetivo)
        secuencia = self.programar(tiempo, nuevo)
        return secuencia, nuevo

    @staticmethod
    def calcular_tiempo_por_velocidad(tiempo_siguiente, t, velocidad_anterior, velocidad_nueva):
        if velocidad_anterior <= 0 or velocidad_nueva <= 0:
            raise ValueError("las velocidades deben ser mayores que 0")
        restante_nuevo = max(1, (tiempo_siguiente - t) * velocidad_anterior // velocidad_nueva)
        return t + restante_nuevo

    def cambiar_velocidad(self, evento, t, velocidad_anterior, velocidad_nueva):
        if evento.tiempo_siguiente is None:
            raise ValueError("el evento no está programado en la agenda")
        tiempo = self.calcular_tiempo_por_velocidad(
            evento.tiempo_siguiente, t, velocidad_anterior, velocidad_nueva)
        return self.reprogramar(evento, tiempo)

    def _descartar_cancelados(self):
        # saca de la raíz los eventos cancelados hasta encontrar uno válido o vaciar el heap
        while not self._heap.esta_vacio() and self._heap.ver_minimo()[2].cancelado:
            _, _, evento = self._heap.extraer_minimo()
            evento.en_agenda = False
            self._cancelados_en_heap -= 1

    def ver_siguiente(self):
        self._descartar_cancelados()
        return self._heap.ver_minimo()

    def sacar_siguiente(self):
        self._descartar_cancelados()
        entrada = self._heap.extraer_minimo()
        entrada[2].en_agenda = False
        return entrada

    def esta_vacia(self):
        self._descartar_cancelados()
        return self._heap.esta_vacio()

    def tamano(self):
        return self._heap.tamano() - self._cancelados_en_heap