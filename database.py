import os
from dotenv import load_dotenv
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient


# Carregar variáveis do .env
load_dotenv()

# Conexão MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.gerenc_voos
engine = AIOEngine(client=client, database="gerenc_voos")

def get_engine() -> AIOEngine:
    return engine