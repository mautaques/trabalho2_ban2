"""Configuração de conexão com o MongoDB via PyMongo.

Os parâmetros de conexão são lidos de variáveis de ambiente (com valores
padrão para desenvolvimento local). Um MongoDB local normalmente não exige
usuário/senha, mas MONGO_URL permite apontar para qualquer servidor.
"""

import datetime
import os

from pymongo import MongoClient, ReturnDocument

# --- Conexão --------------------------------------------------------------
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "farmacia")

_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Retorna o cliente MongoDB (criado uma única vez, conexão preguiçosa)."""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
    return _client


def get_db():
    """Retorna o banco de dados do projeto.

    Exemplo de uso:
        db = get_db()
        cliente = db.clientes.find_one({"_id": 1})
    """
    return get_client()[MONGO_DB]


def get_next_id(colecao: str) -> int:
    """Gera o próximo ID inteiro sequencial para uma coleção.

    O MongoDB não possui SERIAL/sequences como o PostgreSQL; o padrão usual
    é manter uma coleção de contadores incrementada atomicamente com $inc.
    """
    doc = get_db().contadores.find_one_and_update(
        {"_id": colecao},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return doc["seq"]


def ensure_indexes():
    """Cria os índices únicos equivalentes às constraints UNIQUE do esquema SQL."""
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
    """Converte datetime.date em datetime.datetime (BSON só armazena datetime)."""
    if valor is None or isinstance(valor, datetime.datetime):
        return valor
    if isinstance(valor, datetime.date):
        return datetime.datetime.combine(valor, datetime.time.min)
    return valor


def test_connection() -> bool:
    """Verifica se a conexão com o banco está funcionando."""
    try:
        get_client().admin.command("ping")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Falha ao conectar no MongoDB: {exc}")
        return False


if __name__ == "__main__":
    if test_connection():
        print("Conexão com o MongoDB OK!")
