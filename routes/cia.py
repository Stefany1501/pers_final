from fastapi import APIRouter

# Criando o router para o módulo 'Cia'
router = APIRouter()

@router.get("/cia")
def get_cia():
    return {"message": "Detalhes da companhia aérea"}
