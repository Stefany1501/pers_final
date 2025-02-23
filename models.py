from odmantic import Model, Reference, Field, ObjectId
from typing import List, Optional
from datetime import datetime

# Modelo de Companhia Aérea (Cia)
class Cia(Model):
    nome: str
    cod_iata: str
    aeronaves: List[ObjectId] = Field(default_factory=list)  # Armazena apenas IDs
    voos: List[ObjectId] = Field(default_factory=list)  # Armazena apenas IDs

# Modelo de Aeronave
class Aeronave(Model):
    modelo: str
    capacidade: int
    last_check: datetime = Field(default_factory=datetime.utcnow)
    next_check: datetime = Field(default_factory=datetime.utcnow)
    cia: ObjectId  # Referência para Companhia Aérea
    voos: Optional[List[ObjectId]] = []  # Lista de referências para Voo

# Modelo de Voo
class Voo(Model):
    numero_voo: int
    origem: str
    destino: str
    hr_partida: datetime
    hr_chegada: datetime
    status: str
    aeronave: ObjectId  # Relação com Aeronave
    cia: ObjectId  # Relação com Cia

# Resolver referências circulares
Aeronave.model_rebuild()
Voo.model_rebuild()
Cia.model_rebuild()

# Resolver referências circulares
Cia.update_forward_refs()
Aeronave.update_forward_refs()
Voo.update_forward_refs()