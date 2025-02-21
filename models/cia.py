from odmantic import Model, Field, Reference
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .aeronave import Aeronave
    from .voo import Voo

class CiaBase(Model):
    nome: str
    cod_iata: str

class Cia(CiaBase):
    aeronaves: list["Aeronave"] = Reference()  # Relacionamento com aeronaves
    voos: list["Voo"] = Reference()  # Relacionamento com voos