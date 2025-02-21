from fastapi import FastAPI
from routes import aeronave, voo, cia

# Inicializa o aplicativo FastAPI
app = FastAPI()

# Rotas para Endpoints
app.include_router(aeronave.router)
app.include_router(voo.router)
app.include_router(cia.router)