from fastapi import APIRouter, HTTPException, Depends, Query
from odmantic import ObjectId
from database import get_engine, get_db
from models import Cia, Aeronave, Voo
from typing import List

router = APIRouter(
    prefix="/cias",  # Prefixo para todas as rotas
    tags=["Cias"],   # Tag para documentação automática
)

engine = get_engine()

# Criar uma nova companhia aérea
@router.post("/", response_model=Cia)
async def criar_cia(cia: Cia):
    return await engine.save(cia)

# Listar todas as companhias aéreas com paginação
@router.get("/", response_model=List[Cia])
async def listar_cias(
    offset: int = Query(0, ge=0, description="Número de itens a pular"),
    limit: int = Query(10, gt=0, le=100, description="Número máximo de itens a retornar")
):
    return await engine.find(Cia, skip=offset, limit=limit)


# Rota de atualização de cia
@router.put("/{cia_id}", response_model=Cia)
async def atualizar_cia(cia_id: str, cia_data: Cia, db: engine = Depends(get_db)):
    cia_existente = await db.find_one(Cia, Cia.id == ObjectId(cia_id))
    
    if not cia_existente:
        raise HTTPException(status_code=404, detail="Companhia não encontrada")

    # Atualiza os campos com base nos dados enviados, sem precisar de uma classe separada
    cia_existente.nome = cia_data.nome or cia_existente.nome
    cia_existente.cod_iata = cia_data.cod_iata or cia_existente.cod_iata
    cia_existente.aeronaves = cia_data.aeronaves or cia_existente.aeronaves
    cia_existente.voos = cia_data.voos or cia_existente.voos

    await db.save(cia_existente)
    return cia_existente

# Deletar uma companhia aérea
@router.delete("/{cia_id}")
async def deletar_cia(cia_id: str):
    cia = await engine.find_one(Cia, Cia.id == ObjectId(cia_id))
    if not cia:
        raise HTTPException(status_code=404, detail="Companhia aérea não encontrada")
    await engine.delete(cia)
    return {"message": "Companhia aérea deletada com sucesso"}

@router.get("/filtros", response_model=list[Cia])
async def read_cias(
    id: str = Query(None, description="Buscar por ID"),
    cod_iata: str = Query(None, description="Filtrar por código iata"),
    busca_texto: str = Query(None, description="Filtrar por nome da companhia aérea (parcial)"),
    ordenacao: str = Query(None, description="Campo para ordenação: 'nome'"),
    offset: int = Query(0, ge=0, description="Número de itens a pular"),
    limit: int = Query(10, gt=0, le=100, description="Número máximo de itens a retornar")
):
    filters = {}

    # Filtro por ID da companhia aérea
    if id:
        filters["_id"] = ObjectId(id)

    # Filtro por código IATA
    if cod_iata:
        filters["cod_iata"] = {"$regex": cod_iata, "$options": "i"}

    # Filtro por nome (case insensitive)
    if busca_texto:
        filters["nome"] = {"$regex": busca_texto, "$options": "i"}

    # Busca com paginação
    cias = await engine.find(Cia, filters, skip=offset, limit=limit)

    # Ordenação
    if ordenacao == "nome":
        cias = sorted(cias, key=lambda x: x.nome)

    # Verifica se encontrou alguma companhia
    if not cias:
        raise HTTPException(status_code=404, detail="Companhia aérea não encontrada")

    return cias

# Contagem de aeronaves por companhia aérea
@router.get("/{cia_id}/aeronaves/count", response_model=int)
async def count_aeronaves(cia_id: str):
    cia = await engine.find_one(Cia, Cia.id == ObjectId(cia_id))
    if not cia:
        raise HTTPException(status_code=404, detail="Companhia aérea não encontrada")

    aeronaves = await engine.find(Aeronave, Aeronave.cia == cia.id)
    return len(aeronaves)

# Contagem de voos por companhia aérea
@router.get("/{cia_id}/voos/count", response_model=int)
async def count_voos(cia_id: str):
    # Se houver uma coleção de voos, o código seria semelhante ao de aeronaves
    cia = await engine.find_one(Cia, Cia.id == ObjectId(cia_id))
    if not cia:
        raise HTTPException(status_code=404, detail="Companhia aérea não encontrada")

    # Supondo que há uma coleção de voos
    voos = await engine.find(Voo, Voo.cia == cia.id)
    return len(voos)

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

 # Consultar companhias aéreas com informações completas (incluindo aeronaves e voos)
@router.get("/cia_completa", response_model=list[dict])
async def cias_completas(
    id: str = None,  # Torna o 'id' opcional
    offset: int = Query(0, ge=0, description="Número de itens a pular"),
    limit: int = Query(10, gt=0, le=100, description="Número máximo de itens a retornar")
):
    if id:
        cia = await engine.find_one(Cia, Cia.id == ObjectId(id))
        if not cia:
            raise HTTPException(status_code=404, detail="Companhia aérea não encontrada")
        
        # Obter as aeronaves associadas à companhia
        aeronaves = await engine.find(Aeronave, Aeronave.id.in_(cia.aeronaves)) if cia.aeronaves else []
        # Obter os voos associados à companhia
        voos = await engine.find(Voo, Voo.id.in_(cia.voos)) if cia.voos else []
        
        return [{
            "id": str(cia.id),
            "nome": cia.nome,
            "cod_iata": cia.cod_iata,
            "aeronaves": [{
                "id": str(aero.id),
                "modelo": aero.modelo,
                "capacidade": aero.capacidade,
                "last_check": aero.last_check,
                "next_check": aero.next_check
            } for aero in aeronaves],
            "voos": [{
                "id": str(voo.id),
                "numero_voo": voo.numero_voo,
                "origem": voo.origem,
                "destino": voo.destino,
                "hr_partida": voo.hr_partida,
                "hr_chegada": voo.hr_chegada,
                "status": voo.status
            } for voo in voos]
        }]
    
    # Se 'id' não for fornecido, retorna todas as companhias com paginação
    cias = await engine.find(Cia, skip=offset, limit=limit)
    
    resultado = []
    for cia in cias:
        aeronaves = await engine.find(Aeronave, Aeronave.id.in_(cia.aeronaves)) if cia.aeronaves else []
        voos = await engine.find(Voo, Voo.id.in_(cia.voos)) if cia.voos else []
        resultado.append({
            "id": str(cia.id),
            "nome": cia.nome,
            "cod_iata": cia.cod_iata,
            "aeronaves": [{
                "id": str(aero.id),
                "modelo": aero.modelo,
                "capacidade": aero.capacidade,
                "last_check": aero.last_check,
                "next_check": aero.next_check
            } for aero in aeronaves],
            "voos": [{
                "id": str(voo.id),
                "numero_voo": voo.numero_voo,
                "origem": voo.origem,
                "destino": voo.destino,
                "hr_partida": voo.hr_partida,
                "hr_chegada": voo.hr_chegada,
                "status": voo.status
            } for voo in voos]
        })
    
    return resultado