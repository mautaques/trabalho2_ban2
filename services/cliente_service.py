"""Serviço de negócio para a entidade Cliente."""

import re

from database import get_db, get_next_id, para_datetime
from models.documento import Documento

_CAMPOS = ("nome", "cpf", "telefone", "mail", "data_nascimento")


def _para_objeto(doc: dict) -> Documento:
    doc = dict(doc)
    doc["id_cliente"] = doc.pop("_id")
    if doc.get("data_nascimento"):
        doc["data_nascimento"] = doc["data_nascimento"].date()
    return Documento(doc)


class ClienteService:
    """CRUD e buscas para a coleção *clientes*."""

    @staticmethod
    def listar_todos():
        """Retorna todos os clientes ordenados por nome."""
        return [_para_objeto(d) for d in get_db().clientes.find().sort("nome", 1)]

    @staticmethod
    def buscar_por_id(id_cliente: int):
        """Retorna um cliente pelo ID."""
        doc = get_db().clientes.find_one({"_id": id_cliente})
        return _para_objeto(doc) if doc else None

    @staticmethod
    def buscar(termo: str):
        """Busca clientes por nome, CPF ou e-mail."""
        regex = {"$regex": re.escape(termo), "$options": "i"}
        filtro = {"$or": [{"nome": regex}, {"cpf": regex}, {"mail": regex}]}
        return [
            _para_objeto(d) for d in get_db().clientes.find(filtro).sort("nome", 1)
        ]

    @staticmethod
    def criar(nome, cpf, telefone=None, mail=None, data_nascimento=None):
        """Cria um novo cliente. Valida campos obrigatórios e unicidade do CPF."""
        if not nome or not cpf:
            raise ValueError("Nome e CPF são obrigatórios.")

        db = get_db()
        if db.clientes.find_one({"cpf": cpf}):
            raise ValueError(f"CPF '{cpf}' já cadastrado.")

        doc = {
            "_id": get_next_id("clientes"),
            "nome": nome,
            "cpf": cpf,
            "telefone": telefone,
            "mail": mail,
            "data_nascimento": para_datetime(data_nascimento),
        }
        db.clientes.insert_one(doc)
        return _para_objeto(doc)

    @staticmethod
    def atualizar(id_cliente: int, **dados):
        """Atualiza os campos de um cliente existente."""
        atualizacoes = {
            campo: para_datetime(valor) if campo == "data_nascimento" else valor
            for campo, valor in dados.items()
            if campo in _CAMPOS
        }
        resultado = get_db().clientes.update_one(
            {"_id": id_cliente}, {"$set": atualizacoes}
        )
        if resultado.matched_count == 0:
            raise ValueError("Cliente não encontrado.")
        return ClienteService.buscar_por_id(id_cliente)

    @staticmethod
    def excluir(id_cliente: int):
        """Exclui um cliente pelo ID."""
        if get_db().clientes.delete_one({"_id": id_cliente}).deleted_count == 0:
            raise ValueError("Cliente não encontrado.")
