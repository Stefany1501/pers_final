from fastapi import APIRouter, HTTPException, Query, Depends
from odmantic import ObjectId, AIOEngine
from typing import List
from models import Aeronave, Cia
from database import get_engine
from datetime import datetime

router = APIRouter(
    prefix="/aeronaves",  # Prefixo para todas as rotas
    tags=["Aeronaves"],   # Tag para documentação automática
)

engine = get_engine()

# Create
@router.post("/", response_model=Aeronave)
async def create_aeronave(aeronave_data: Aeronave):
    # Verificar se as datas de last_check e next_check estão no formato correto
    if isinstance(aeronave_data.last_check, str):
        aeronave_data.last_check = datetime.fromisoformat(aeronave_data.last_check.replace("Z", "+00:00"))
    if isinstance(aeronave_data.next_check, str):
        aeronave_data.next_check = datetime.fromisoformat(aeronave_data.next_check.replace("Z", "+00:00"))
    
    # Verificar se a companhia aérea existe
    cia = await engine.find_one(Cia, Cia.id == ObjectId(aeronave_data.cia))
    if not cia:
        raise HTTPException(status_code=404, detail="Companhia aérea não encontrada")

    # Atribuir o ID da cia à aeronave
    aeronave_data.cia = cia.id
    
    # Salvar a aeronave no banco de dados
    await engine.save(aeronave_data)
    return aeronave_data


# Listar todas as aeronaves com paginação
@router.get("/read", response_model=List[Aeronave])
async def listar_aeronvaes(
    offset: int = Query(0, ge=0, description="Número de itens a pular"),
    limit: int = Query(10, gt=0, le=100, description="Número máximo de itens a retornar")
):
    return await engine.find(Aeronave, skip=offset, limit=limit)

# Update
@router.put("/{id}", response_model=Aeronave)
async def update_aeronave(id: str, aeronave_data: Aeronave):
    # Buscar a aeronave pelo ID
    aeronave = await engine.find_one(Aeronave, Aeronave.id == ObjectId(id))
    if not aeronave:
        raise HTTPException(status_code=404, detail="Aeronave não encontrada")
    
    # Atualizar os dados da aeronave
    aeronave.modelo = aeronave_data.modelo
    aeronave.capacidade = aeronave_data.capacidade
    aeronave.last_check = aeronave_data.last_check
    aeronave.next_check = aeronave_data.next_check
    aeronave.cia = ObjectId(aeronave_data.cia)
    
    # Salvar as alterações
    await engine.save(aeronave)
    return aeronave

# Delete
@router.delete("/{id}", response_model=Aeronave)
async def delete_aeronave(id: str):
    # Buscar a aeronave pelo ID
    aeronave = await engine.find_one(Aeronave, Aeronave.id == ObjectId(id))
    if not aeronave:
        raise HTTPException(status_code=404, detail="Aeronave não encontrada")
    
    # Deletar a aeronave
    await engine.delete(aeronave)
    return aeronave


# Read (com filtros)
@router.get("/filtros", response_model=list[Aeronave])
async def read_aeronaves_filtro(
    id: str = None,
    modelo: str = None,
    capacidade: int = None,
    cia_id: str = None,
    last_check_start: datetime = Query(
        None, description="Início do intervalo de last_check (ISO format)"
    ),
    last_check_end: datetime = Query(
        None, description="Fim do intervalo de last_check (ISO format)"
    ),
    next_check_start: datetime = Query(
        None, description="Início do intervalo de next_check (ISO format)"
    ),
    next_check_end: datetime = Query(
        None, description="Fim do intervalo de next_check (ISO format)"
    )
):
    filters = {}
    
    if id:
        filters["_id"] = ObjectId(id)
    if modelo:
        filters["modelo"] = {"$regex": modelo, "$options": "i"}
    if capacidade:
        filters["capacidade"] = capacidade
    if cia_id:
        filters["cia"] = ObjectId(cia_id)
    
    if last_check_start or last_check_end:
        filters["last_check"] = {}
        if last_check_start:
            filters["last_check"]["$gte"] = last_check_start
        if last_check_end:
            filters["last_check"]["$lte"] = last_check_end
        if not filters["last_check"]:
            del filters["last_check"]
    
    if next_check_start or next_check_end:
        filters["next_check"] = {}
        if next_check_start:
            filters["next_check"]["$gte"] = next_check_start
        if next_check_end:
            filters["next_check"]["$lte"] = next_check_end
        if not filters["next_check"]:
            del filters["next_check"]
    
    aeronaves = await engine.find(Aeronave, filters)
    if not aeronaves:
        raise HTTPException(status_code=404, detail="Aeronave não encontrada")
    
    return aeronaves


# Consultar aeronaves com informações completas (incluindo companhia aérea e voos)
@router.get("/completa", response_model=list[dict])
async def aeronaves_completas(
    id: str = None,  # Torna o 'id' opcional
    offset: int = Query(0, ge=0, description="Número de itens a pular"),
    limit: int = Query(10, gt=0, le=100, description="Número máximo de itens a retornar")
):
    # Se 'id' for fornecido, buscar a aeronave específica
    if id:
        aeronave = await engine.find_one(Aeronave, Aeronave.id == ObjectId(id))
        
        if not aeronave:
            raise HTTPException(status_code=404, detail="Aeronave não encontrada")
        
        # Obter informações da companhia aérea
        cia = await engine.find_one(Cia, Cia.id == aeronave.cia)
        
        # Retorno com as informações completas da aeronave
        return [{
            "id": str(aeronave.id),
            "modelo": aeronave.modelo,
            "capacidade": aeronave.capacidade,
            "last_check": aeronave.last_check,
            "next_check": aeronave.next_check,
            "cia": {
                "id": str(cia.id) if cia else None,
                "nome": cia.nome if cia else None,
                "cod_iata": cia.cod_iata if cia else None
            }
        }]
    
    # Se 'id' não for fornecido, retorna todas as aeronaves com paginação
    aeronaves = await engine.find(Aeronave, skip=offset, limit=limit)
    
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
                "id": str(cia.id) if cia else None,
                "nome": cia.nome if cia else None,
                "cod_iata": cia.cod_iata if cia else None
            }
        })
    
    return resultado