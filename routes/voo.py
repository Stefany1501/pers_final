from fastapi import APIRouter, HTTPException, Query
from odmantic import ObjectId
from typing import List, Dict
from models import Voo, Aeronave, Cia
from database import get_engine
from datetime import datetime

router = APIRouter(
    prefix="/voos",
    tags=["Voos"],
)

engine = get_engine()

# Create
@router.post("/", response_model=Voo)
async def create_voo(voo_data: Voo):
    # Conversão de datas caso sejam strings
    if isinstance(voo_data.hr_partida, str):
        voo_data.hr_partida = datetime.fromisoformat(voo_data.hr_partida.replace("Z", "+00:00"))
    if isinstance(voo_data.hr_chegada, str):
        voo_data.hr_chegada = datetime.fromisoformat(voo_data.hr_chegada.replace("Z", "+00:00"))

    await engine.save(voo_data)
    return voo_data


# Read - Listagem Paginada
@router.get("/read", response_model=List[Voo])
async def listar_voos(
    offset: int = Query(0, ge=0, description="Número de itens a pular"),
    limit: int = Query(10, gt=0, le=100, description="Número máximo de itens a retornar")
):
    return await engine.find(Voo, skip=offset, limit=limit)


# Update
@router.put("/{id}", response_model=Voo)
async def update_voo(id: str, voo_data: Voo):
    voo = await engine.find_one(Voo, Voo.id == ObjectId(id))
    if not voo:
        raise HTTPException(status_code=404, detail="Voo não encontrado")

    # Atualizando os campos
    voo.numero_voo = voo_data.numero_voo
    voo.origem = voo_data.origem
    voo.destino = voo_data.destino
    voo.hr_partida = voo_data.hr_partida
    voo.hr_chegada = voo_data.hr_chegada
    voo.status = voo_data.status
    voo.aeronave = voo_data.aeronave
    voo.cia = voo_data.cia

    await engine.save(voo)
    return voo


# Delete
@router.delete("/{id}", response_model=Dict[str, str])
async def delete_voo(id: str):
    voo = await engine.find_one(Voo, Voo.id == ObjectId(id))
    if not voo:
        raise HTTPException(status_code=404, detail="Voo não encontrado")

    await engine.delete(voo)
    return {"message": "Voo excluído com sucesso"}

# Read - Filtros
@router.get("/filtros", response_model=List[Voo])
async def read_voos_filtro(
    id: str = None,
    data_inicio: str = None,
    data_fim: str = None,
    busca_texto: str = None,
    ordenacao: str = Query(None, description="Ordenar por 'hr_partida' ou 'hr_chegada'")
):
    filtros = {}

    if id:
        filtros["_id"] = ObjectId(id)
    
    if data_inicio:
        data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
        filtros["hr_partida"] = {"$gte": data_inicio_dt}
    
    if data_fim:
        data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
        filtros.setdefault("hr_partida", {})["$lte"] = data_fim_dt
    
    if busca_texto:
        filtros["$or"] = [
            {"origem": {"$regex": busca_texto, "$options": "i"}},
            {"destino": {"$regex": busca_texto, "$options": "i"}}
        ]

    voos = await engine.find(Voo, filtros)
    
    if ordenacao:
        voos = sorted(voos, key=lambda x: getattr(x, ordenacao, None))
    
    return voos


# Read - Consulta Completa de Voos (com Companhia e Aeronave)
@router.get("/completo", response_model=list[dict])
async def voos_completos(
    id: str = None,  # ID opcional
    offset: int = Query(0, ge=0, description="Número de itens a pular"),
    limit: int = Query(10, gt=0, le=100, description="Número máximo de itens a retornar")
):
    # buscar voo específico
    if id:
        voo = await engine.find_one(Voo, Voo.id == ObjectId(id))
        
        if not voo:
            raise HTTPException(status_code=404, detail="Voo não encontrado")
        
        # Obter informações da companhia e da aeronave
        cia = await engine.find_one(Cia, Cia.id == voo.cia)
        aeronave = await engine.find_one(Aeronave, Aeronave.id == voo.aeronave)

        return [{
            "id": str(voo.id),
            "numero_voo": voo.numero_voo,
            "origem": voo.origem,
            "destino": voo.destino,
            "hr_partida": voo.hr_partida,
            "hr_chegada": voo.hr_chegada,
            "status": voo.status,
            "cia": {
                "id": str(cia.id) if cia else None,
                "nome": cia.nome if cia else None,
                "cod_iata": cia.cod_iata if cia else None
            },
            "aeronave": {
                "id": str(aeronave.id) if aeronave else None,
                "modelo": aeronave.modelo if aeronave else None,
                "capacidade": aeronave.capacidade if aeronave else None
            }
        }]

    # Se id não for fornecido retorna todos os voos com paginação
    voos = await engine.find(Voo, skip=offset, limit=limit)

    resultado = []
    for voo in voos:
        cia = await engine.find_one(Cia, Cia.id == voo.cia)
        aeronave = await engine.find_one(Aeronave, Aeronave.id == voo.aeronave)
        
        resultado.append({
            "id": str(voo.id),
            "numero_voo": voo.numero_voo,
            "origem": voo.origem,
            "destino": voo.destino,
            "hr_partida": voo.hr_partida,
            "hr_chegada": voo.hr_chegada,
            "status": voo.status,
            "cia": {
                "id": str(cia.id) if cia else None,
                "nome": cia.nome if cia else None,
                "cod_iata": cia.cod_iata if cia else None
            },
            "aeronave": {
                "id": str(aeronave.id) if aeronave else None,
                "modelo": aeronave.modelo if aeronave else None,
                "capacidade": aeronave.capacidade if aeronave else None
            }
        })

    return resultado
