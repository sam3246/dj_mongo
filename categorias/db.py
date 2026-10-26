from django.conf import settings
from pymongo import MongoClient


if not settings.MONGO_URI:
    raise RuntimeError(
        "Falta configurar MONGO_URI en el archivo .env"
    )


cliente = MongoClient(
    settings.MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = cliente[settings.MONGO_DB]

coleccion_categorias = db["categorias"]
