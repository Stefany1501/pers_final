from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
import os

#carregando variaveis do arquivo .env
load_dotenv()

#conectando ao banco de dados
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.gerenc_voos
engine = AIOEngine(client=client, database="gerenc_voos")

def get_engine() -> AIOEngine:
    return engine

def get_db() -> AIOEngine:
    return engine  # Ou retorna a conexão com o MongoDB