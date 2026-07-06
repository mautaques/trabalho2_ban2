import datetime
import os

from pymongo import MongoClient, ReturnDocument

# ----------------------- Conexão com o DB --------------------------------
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "farmacia")

_client: MongoClient | None = None


def get_client() -> MongoClient:
    
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
    return _client


def get_db():
    
    return get_client()[MONGO_DB]


def get_next_id(colecao: str) -> int:
    
    doc = get_db().contadores.find_one_and_update(
        {"_id": colecao},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return doc["seq"]


def ensure_indexes():
    
    db = get_db()
    db.clientes.create_index("cpf", unique=True)
    db.vendedores.create_index("cpf", unique=True)
    db.vendedores.create_index("matricula", unique=True)
    db.filiais.create_index("codigo_filial", unique=True)
    db.filiais.create_index("cnpj", unique=True)
    db.fornecedores.create_index("cnpj", unique=True)
    db.fornecedores.create_index("razao_social", unique=True)
    db.produtos.create_index("codigo_de_barras", unique=True)
    db.lotes.create_index("numero_lote", unique=True)
    db.vendas.create_index("cupom_fiscal", unique=True)
    db.reposicoes.create_index("numero_pedido", unique=True)


def para_datetime(valor):
    #Converte datetime.date para datetime.datetime (BSON só armazena datetime).
    if valor is None or isinstance(valor, datetime.datetime):
        return valor
    if isinstance(valor, datetime.date):
        return datetime.datetime.combine(valor, datetime.time.min)
    return valor


def test_connection() -> bool:
    
    try:
        get_client().admin.command("ping")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Falha ao conectar no MongoDB: {exc}")
        return False


if __name__ == "__main__":
    if test_connection():
        print("Conexão com o MongoDB OK!")
