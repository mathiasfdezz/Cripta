from modelo.movimiento import MovimientoInvalido
from modelo.punto_de_control import PuntoDeControl

CADA_POR_DEFECTO = 10
FUERA_DE_RANGO = "fuera_de_rango"

# operaciones que se anotan (la primera posición de cada tupla)
CONTENIDO = "contenido"
INICIAR = "iniciar"
ACCION = "accion"
AVANZAR = "avanzar"
CURSOR = "cursor"
PERGAMINO = "pergamino"
SIGUIENTE = "siguiente"


class LineaTiempo:
    """Historia consultable de la partida (§3.6), reconstruida hacia adelante.

    Se anota cada operación que cambia la partida: acciones del jugador con su
    argumento, avances del reloj, llegada de contenido y movimientos del cursor.
    Cada K acciones se guarda un punto de control (copia completa con el azar).
    Consultar copia el punto anterior más cercano y re-aplica a lo sumo K acciones;
    no toca la partida en curso."""

    def __init__(self, cada=CADA_POR_DEFECTO, primera=1):
        if cada < 1:
            raise ValueError("K debe ser 1 o mayor")
        self.cada = cada
        # número de la primera acción anotada (1, salvo que la línea empiece a mitad de
        # partida porque un guardado no la pudo reconstruir)
        self.primera = primera
        self.operaciones = []
        self.inicio_accion = []   # posición en operaciones donde empieza la acción k (k-1)
        self.decisiones = []      # reloj al decidir la acción k (k-1); nunca decrece
        self.puntos = []          # el i-ésimo, justo antes de la acción i*K + 1

    # ------------------------------------------------------------ anotar

    def anotar(self, operacion):
        self.operaciones.append(operacion)

    def antes_de_accion(self, estado, nombre, argumento):
        """El jugador va a hacer una acción: si toca, punto de control; después se
        anota cuándo decidió y qué hizo."""
        numero = self.primera + len(self.decisiones)
        if len(self.puntos) * self.cada + self.primera == numero:
            self.puntos.append(PuntoDeControl(numero, len(self.operaciones), estado.copiar()))
        self.inicio_accion.append(len(self.operaciones))
        self.decisiones.append(estado.tiempo)
        self.operaciones.append((ACCION, nombre, argumento))

    def recortar(self, numero):
        """Un pergamino revirtió la acción 'numero': deja de existir en la línea. Solo
        se recorre la cola de esa acción; la llegada de contenido no se deshace."""
        posicion = numero - self.primera
        if posicion < 0 or posicion >= len(self.inicio_accion):
            return
        inicio = self.inicio_accion[posicion]
        conservar = [op for op in self.operaciones[inicio:] if op[0] == CONTENIDO]
        del self.operaciones[inicio:]
        self.operaciones.extend(conservar)
        del self.inicio_accion[posicion:]
        del self.decisiones[posicion:]
        while self.puntos and self.puntos[-1].accion >= numero:
            self.puntos.pop()

    # ------------------------------------------------------------ consultar

    def acciones(self):
        return self.primera - 1 + len(self.decisiones)

    def estado_antes_de(self, actual, numero):
        """Estado justo antes de la acción 'numero' (1 = la primera). 'actual' es la
        partida en curso; con numero = acciones + 1 se devuelve ella misma, sin copiar."""
        actual_numero = self.acciones() + 1
        if numero < self.primera or numero > actual_numero:
            desde = "" if self.primera == 1 else f" (la línea empieza en la #{self.primera})"
            raise MovimientoInvalido(FUERA_DE_RANGO,
                                     f"la acción #{numero} no existe: la actual es la "
                                     f"#{actual_numero}{desde}")
        if numero == actual_numero:
            return actual
        punto = self.puntos[(numero - self.primera) // self.cada]
        estado = punto.estado.copiar()
        for posicion in range(punto.operacion, self.inicio_accion[numero - self.primera]):
            aplicar(estado, self.operaciones[posicion])
        return estado

    def estado_en(self, actual, t):
        """Estado después de todos los eventos con tiempo <= t; si a t le corresponde
        una decisión del jugador, justo antes de tomarla."""
        if t < 0 or t > actual.tiempo:
            raise MovimientoInvalido(FUERA_DE_RANGO,
                                     f"el instante {t} no existe todavía: el reloj va en "
                                     f"{actual.tiempo}")
        cuantas = self._ultima_decision_hasta(t)
        if cuantas > 0 and self.decisiones[cuantas - 1] == t:
            return self.estado_antes_de(actual, self.primera + cuantas - 1)
        if t == actual.tiempo:
            # ya es el presente: la partida en curso, sin copiar
            return actual
        if cuantas == 0:
            if self.primera == 1 and not self.decisiones:
                return actual
            raise MovimientoInvalido(FUERA_DE_RANGO,
                                     f"el instante {t} es anterior al inicio de la línea de tiempo")
        estado = self.estado_antes_de(actual, self.primera + cuantas - 1)
        # se hace la acción y luego solo los eventos hasta t
        posicion = self.inicio_accion[cuantas - 1]
        fin = (self.inicio_accion[cuantas] if cuantas < len(self.inicio_accion)
               else len(self.operaciones))
        while posicion < fin and self.operaciones[posicion][0] not in (AVANZAR, SIGUIENTE):
            aplicar(estado, self.operaciones[posicion])
            posicion += 1
        estado.avanzar_hasta_tiempo(t)
        return estado

    def _ultima_decision_hasta(self, t):
        """Cuántas decisiones anotadas ocurrieron en un instante <= t. Búsqueda binaria
        propia sobre los tiempos de decisión (no decrecientes)."""
        bajo, alto = 0, len(self.decisiones)
        while bajo < alto:
            medio = (bajo + alto) // 2
            if self.decisiones[medio] <= t:
                bajo = medio + 1
            else:
                alto = medio
        return bajo


def aplicar(estado, operacion):
    """Repite una operación anotada sobre otro estado (una copia o una partida que se
    está reconstruyendo)."""
    tipo = operacion[0]
    if tipo == ACCION:
        metodo = getattr(estado, operacion[1])
        if operacion[2] is None:
            metodo()
        else:
            metodo(operacion[2])
    elif tipo == AVANZAR:
        estado.avanzar_hasta_turno_jugador()
    elif tipo == CONTENIDO:
        estado.cargar_contenido(operacion[1])
    elif tipo == CURSOR:
        estado.mover_cursor(operacion[1])
    elif tipo == PERGAMINO:
        estado.consumir_pergamino()
    elif tipo == INICIAR:
        estado.iniciar()
    elif tipo == SIGUIENTE:
        estado.ejecutar_siguiente()
    else:
        raise ValueError(f"operación desconocida en la línea de tiempo: {tipo}")
