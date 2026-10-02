from dataclasses import dataclass


@dataclass(frozen=True)
class FichaCatalogo:
    id: str
    nombre: str
    clase: str
    # enemigos
    vida_max: int | None = None
    ataque: int | None = None
    defensa: int | None = None
    velocidad: int | None = None
    comportamiento: str | None = None
    suelta: tuple = ()
    regeneracion: int | None = None
    # objetos
    peso: int | None = None
    valor: int | None = None
    ataque_bonus: int | None = None
    defensa_bonus: int | None = None
    cura: int | None = None
    modificador_velocidad: int | None = None
    duracion: int | None = None
    abre: str | None = None
    # trampas
    dano: int | None = None
    rearme: int | None = None