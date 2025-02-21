from odmantic import Model, Field, Reference
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .cia import Cia
    from .aeronave import Aeronave

class VooBase(Model):
    numero_voo: int
    origem: str
    destino: str
    hr_partida: datetime
    hr_chegada: datetime
    status: str

class Voo(VooBase):
    aeronave: "Aeronave" = Reference()  # Relacionamento com Aeronave
    cia: "Cia" = Reference()  # Relacionamento com Cia