from odmantic import Model, Field, Reference
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .cia import Cia
    from .voo import Voo

class AeronaveBase(Model):
    modelo: str
    capacidade: int
    last_check: datetime = Field(default_factory=datetime.utcnow)
    next_check: datetime = Field(default_factory=datetime.utcnow)

class Aeronave(AeronaveBase):
    cia: "Cia" = Reference()  # Referência para Cia
    voos: list["Voo"] = Reference()  # Referência para Voo