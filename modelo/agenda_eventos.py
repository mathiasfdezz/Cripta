from estructuras.min_heap import MinHeap
from modelo.evento import Evento


class AgendaEventos:
    def __init__(self):
        self._heap = MinHeap()
        self._siguiente_secuencia = 1
        # cuántos eventos cancelados siguen dentro del heap sin haber sido descartados
        self._cancelados_en_heap = 0
        # recibe cómo deshacer cada cambio de la agenda (lo conecta el historial del retroceso)
        self.registrar = None

    def programar(self, tiempo, evento):
        secuencia = self._siguiente_secuencia
        self._siguiente_secuencia += 1
        evento.tiempo_siguiente = tiempo
        evento.secuencia = secuencia
        evento.en_agenda = True
        # la secuencia nunca se repite, así que nunca se llega a comparar el evento
        self._heap.insertar((tiempo, secuencia, evento))
        self._anotar(lambda: self._anular(evento))
        return secuencia

    def cancelar(self, evento):
        # no se busca en el heap: solo se marca, y se descarta al llegar a la raíz
        if evento.cancelado or not evento.en_agenda:
            return False
        evento.cancelado = True
        self._cancelados_en_heap += 1
        self._anotar(lambda: self._descancelar(evento))
        return True

    def reprogramar(self, evento, tiempo):
        # la versión anterior queda cancelada y la nueva entra con secuencia nueva
        self.cancelar(evento)
        nuevo = Evento(evento.tipo, evento.objetivo, evento.dato)
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
            entrada = self._heap.extraer_minimo()
            entrada[2].en_agenda = False
            self._cancelados_en_heap -= 1
            self._anotar(lambda: self._reinsertar(entrada, True))

    def ver_siguiente(self):
        self._descartar_cancelados()
        return self._heap.ver_minimo()

    def sacar_siguiente(self):
        self._descartar_cancelados()
        entrada = self._heap.extraer_minimo()
        entrada[2].en_agenda = False
        self._anotar(lambda: self._reinsertar(entrada, False))
        return entrada

    def esta_vacia(self):
        self._descartar_cancelados()
        return self._heap.esta_vacio()

    def tamano(self):
        return self._heap.tamano() - self._cancelados_en_heap

    # ------------------------------------------------ para guardar y cargar

    def pendientes(self):
        """(tiempo, secuencia, evento) de los eventos vigentes, en cualquier orden."""
        return [entrada for entrada in self._heap._datos if not entrada[2].cancelado]

    def siguiente_secuencia(self):
        return self._siguiente_secuencia

    def restaurar(self, tiempo, secuencia, evento, siguiente_secuencia):
        """Vuelve a meter un evento guardado con su misma secuencia, así el orden
        de los empates es el mismo que antes de guardar."""
        evento.tiempo_siguiente = tiempo
        evento.secuencia = secuencia
        evento.en_agenda = True
        self._heap.insertar((tiempo, secuencia, evento))
        self._siguiente_secuencia = max(self._siguiente_secuencia, siguiente_secuencia)

    # -------------------------------------------- para deshacer (retroceso)
    # la secuencia no se rebobina: los eventos restaurados conservan la suya
    # y los nuevos siguen recibiendo números mayores, así nunca se repiten

    def _anotar(self, deshacer):
        if self.registrar is not None:
            self.registrar(deshacer)

    def _anular(self, evento):
        # deshace programar: queda en el heap como cancelado y se ignora al llegar
        evento.cancelado = True
        self._cancelados_en_heap += 1

    def _descancelar(self, evento):
        evento.cancelado = False
        self._cancelados_en_heap -= 1

    def _reinsertar(self, entrada, cancelado):
        self._heap.insertar(entrada)
        entrada[2].en_agenda = True
        if cancelado:
            self._cancelados_en_heap += 1
