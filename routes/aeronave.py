from fastapi import APIRouter, HTTPException
from odmantic import ObjectId
from models import Aeronave
from models import Cia
from models import Voo
from database import get_engine
from typing import List
from datetime import datetime

router = APIRouter(
    prefix="/aeronaves",  # Prefixo para todas as rotas
    tags=["Aeronaves"],   # Tag para documentação automática
)

engine = get_engine()

# Create
@router.post("/", response_model=Aeronave)
async def create_aeronave(aeronave_data: Aeronave) -> Aeronave:
    if isinstance(aeronave_data.last_check, str):
        aeronave_data.last_check = datetime.fromisoformat(aeronave_data.last_check.replace("Z", "+00:00"))
    if isinstance(aeronave_data.next_check, str):
        aeronave_data.next_check = datetime.fromisoformat(aeronave_data.next_check.replace("Z", "+00:00"))
    
    cia = await engine.find_one(Cia, Cia.id == aeronave_data.cia)
    if not cia:
        raise HTTPException(status_code=404, detail="Companhia aérea não encontrada")
    
    aeronave_data.cia = cia
    await engine.save(aeronave_data)
    return aeronave_data

# Read (com filtros)
@router.get("/", response_model=List[Aeronave])
async def read_aeronaves_filtro(modelo: str = None, capacidade: int = None, cia_id: str = None) -> List[Aeronave]:
    query = {}
    if modelo:
        query["modelo"] = {"$regex": modelo, "$options": "i"}
    if capacidade:
        query["capacidade"] = capacidade
    if cia_id:
        query["cia"] = ObjectId(cia_id)  # Garantir que o ObjectId seja utilizado corretamente
    
    aeronaves = await engine.find(Aeronave, query)
    if not aeronaves:
        raise HTTPException(status_code=404, detail="Nenhuma aeronave encontrada")
    return aeronaves

# Listar todas as aeronaves
@router.get("/all", response_model=List[Aeronave])  # Renomeado para evitar sobrecarga de caminhos
async def get_all_aeronaves() -> List[Aeronave]:
    aeronaves = await engine.find(Aeronave)
    return aeronaves

# Aeronave por id
@router.get("/{aeronave_id}", response_model=Aeronave)
async def get_aeronave_by_id(aeronave_id: str) -> Aeronave:
    aeronave = await engine.find_one(Aeronave, Aeronave.id == ObjectId(aeronave_id))  # Converter para ObjectId
    if not aeronave:
        raise HTTPException(status_code=404, detail="Aeronave não encontrada")
    return aeronave

# Excluir aeronave
@router.delete("/{aeronave_id}")
async def delete_aeronave(aeronave_id: str) -> dict:
    aeronave = await engine.find_one(Aeronave, Aeronave.id == ObjectId(aeronave_id))  # Usando ObjectId
    if not aeronave:
        raise HTTPException(status_code=404, detail="Aeronave não encontrada")
    await engine.delete(aeronave)
    return {"message": "Aeronave deletada"}

# Update
@router.put("/{id}", response_model=Aeronave)
async def update_aeronave(id: str, aeronave_data: Aeronave) -> Aeronave:
    aeronave = await engine.find_one(Aeronave, Aeronave.id == ObjectId(id))
    if not aeronave:
        raise HTTPException(status_code=404, detail="Aeronave não encontrada")
    
    # Atualizando os campos da aeronave
    aeronave.modelo = aeronave_data.modelo
    aeronave.capacidade = aeronave_data.capacidade
    aeronave.last_check = aeronave_data.last_check
    aeronave.next_check = aeronave_data.next_check
    aeronave.cia = aeronave_data.cia
    
    await engine.save(aeronave)
    return aeronave

# Contar aeronaves por voos
@router.get("/contagem-aeronaves-por-voos", response_model=dict)
async def contar_aeronaves_por_voos() -> dict:
    aeronaves = await engine.find(Aeronave)
    resultado = {}
    for aeronave in aeronaves:
        total_voos = await engine.count(Voo, Voo.aeronave == aeronave.id)
        resultado[aeronave.modelo] = total_voos
    return resultado

# Informações completas das aeronaves
@router.get("/aeronaves-completas", response_model=List[dict])
async def aeronaves_completas() -> List[dict]:
    aeronaves = await engine.find(Aeronave)
    resultado = []
    for aeronave in aeronaves:
        cia = await engine.find_one(Cia, Cia.id == aeronave.cia)
        resultado.append({
            "id": str(aeronave.id),
            "modelo": aeronave.modelo,
            "capacidade": aeronave.capacidade,
            "last_check": aeronave.last_check,
            "next_check": aeronave.next_check,
            "cia": {
                "id": str(cia.id),
                "nome": cia.nome,
                "cod_iata": cia.cod_iata,
            } if cia else None
        })
    return resultado

Aeronave.model_rebuild()
Cia.model_rebuild()
