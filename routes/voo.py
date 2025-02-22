from fastapi import APIRouter, HTTPException, Depends, Query
from odmantic import ObjectId
from database import engine
from models import Voo
from models import Aeronave
from models import Cia
from datetime import datetime
from typing import List

router = APIRouter(
    prefix="/voos",
    tags=["Voos"],
)

# Create
@router.post("/", response_model=Voo)
async def create_voo(voo_data: Voo):
    if isinstance(voo_data.hr_partida, str):
        voo_data.hr_partida = datetime.fromisoformat(voo_data.hr_partida.replace("Z", "+00:00"))
    if isinstance(voo_data.hr_chegada, str):
        voo_data.hr_chegada = datetime.fromisoformat(voo_data.hr_chegada.replace("Z", "+00:00"))

    await engine.save(voo_data)
    return voo_data

# Update
@router.put("/{id}", response_model=Voo)
async def update_voo(id: str, voo_data: Voo):
    voo = await engine.find_one(Voo, Voo.id == ObjectId(id))
    if not voo:
        raise HTTPException(status_code=404, detail="Voo não encontrado")

    voo.numero_voo = voo_data.numero_voo
    voo.origem = voo_data.origem
    voo.destino = voo_data.destino
    voo.hr_partida = voo_data.hr_partida
    voo.hr_chegada = voo_data.hr_chegada
    voo.status = voo_data.status
    voo.aeronave_id = voo_data.aeronave_id
    voo.cia_id = voo_data.cia_id

    await engine.save(voo)
    return voo

# Delete
@router.delete("/{id}")
async def delete_voo(id: str):
    voo = await engine.find_one(Voo, Voo.id == ObjectId(id))
    if not voo:
        raise HTTPException(status_code=404, detail="Voo não encontrado")

    await engine.delete(voo)
    return {"message": "Voo excluído com sucesso"}

# Read (Listagem e Filtros)
@router.get("/", response_model=List[Voo])
async def read_voos(
    id: str = Query(None, description="Buscar por ID"),
    data_inicio: str = Query(None, description="Data de início (YYYY-MM-DD)"),
    data_fim: str = Query(None, description="Data de fim (YYYY-MM-DD)"),
    companhia_nome: str = Query(None, description="Filtrar por nome da companhia"),
    busca_texto: str = Query(None, description="Filtrar por origem ou destino"),
    ordenacao: str = Query(None, description="Ordenar por 'hr_partida' ou 'hr_chegada'"),
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

# Contagem de Voos por Companhia
@router.get("/contagem-por-companhia", response_model=dict)
async def contar_voos_por_companhia():
    pipeline = [
        {"$group": {"_id": "$cia_id", "total_voos": {"$sum": 1}}}
    ]
    resultados = await engine.database["voo"].aggregate(pipeline).to_list(None)
    
    contagem = {str(result["_id"]): result["total_voos"] for result in resultados}
    return contagem

# Consulta Completa de Voos (com Cia e Aeronave)
@router.get("/voos-completo", response_model=List[dict])
async def voos_completo():
    voos = await engine.find(Voo)

    voos_completos = []
    for voo in voos:
        cia = await engine.find_one(Cia, Cia.id == voo.cia_id)
        aeronave = await engine.find_one(Aeronave, Aeronave.id == voo.aeronave_id)

        voos_completos.append({
            "id": str(voo.id),
            "numero_voo": voo.numero_voo,
            "origem": voo.origem,
            "destino": voo.destino,
            "hr_partida": voo.hr_partida,
            "hr_chegada": voo.hr_chegada,
            "status": voo.status,
            "cia": {
                "id": str(cia.id),
                "nome": cia.nome,
                "cod_iata": cia.cod_iata
            } if cia else None,
            "aeronave": {
                "id": str(aeronave.id),
                "modelo": aeronave.modelo,
                "capacidade": aeronave.capacidade
            } if aeronave else None
        })

    return voos_completos