from odmantic import Model, Reference, Field
from typing import List
from datetime import datetime

# Modelo de Companhia Aérea (Cia)
class Cia(Model):
    nome: str
    cod_iata: str
    aeronaves: List["Aeronave"] = Field(default_factory=list)  # Referência correta
    voos: List["Voo"] = Field(default_factory=list)  # Referência correta

# Modelo de Aeronave
class Aeronave(Model):
    modelo: str
    capacidade: int
    last_check: datetime = Field(default_factory=datetime.utcnow)
    next_check: datetime = Field(default_factory=datetime.utcnow)
    cia: "Cia" = Reference()  # Relação com Cia
    voos: List["Voo"] = Field(default_factory=list)  # Relação com Voos

# Modelo de Voo
class Voo(Model):
    numero_voo: int
    origem: str
    destino: str
    hr_partida: datetime
    hr_chegada: datetime
    status: str
    aeronave: "Aeronave" = Reference()  # Relação com Aeronave
    cia: "Cia" = Reference()  # Relação com Cia

# Resolver referências circulares
Cia.update_forward_refs()
Aeronave.update_forward_refs()
Voo.update_forward_refs()