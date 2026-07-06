"""Serviço de negócio para a entidade Fornecedor."""

import re

from database import get_db, get_next_id
from models.documento import Documento

_CAMPOS = (
    "cnpj", "razao_social", "nome_fantasia", "mail", "telefone",
    "condicoes_pagamento", "endereco",
)


def _para_objeto(doc: dict) -> Documento:
    doc = dict(doc)
    doc["id_fornecedor"] = doc.pop("_id")
    return Documento(doc)


class FornecedorService:
    """CRUD e buscas para a coleção *fornecedores*."""

    @staticmethod
    def listar_todos():
        """Retorna todos os fornecedores ordenados por nome fantasia."""
        return [
            _para_objeto(d)
            for d in get_db().fornecedores.find().sort("nome_fantasia", 1)
        ]

    @staticmethod
    def buscar_por_id(id_fornecedor: int):
        """Retorna um fornecedor pelo ID."""
        doc = get_db().fornecedores.find_one({"_id": id_fornecedor})
        return _para_objeto(doc) if doc else None

    @staticmethod
    def buscar(termo: str):
        """Busca fornecedores por nome fantasia, razão social ou CNPJ."""
        regex = {"$regex": re.escape(termo), "$options": "i"}
        filtro = {
            "$or": [
                {"nome_fantasia": regex},
                {"razao_social": regex},
                {"cnpj": regex},
            ]
        }
        return [
            _para_objeto(d)
            for d in get_db().fornecedores.find(filtro).sort("nome_fantasia", 1)
        ]

    @staticmethod
    def criar(
        cnpj,
        razao_social,
        nome_fantasia,
        mail=None,
        telefone=None,
        condicoes_pagamento=None,
        endereco=None,
    ):
        """Cria um novo fornecedor. Valida unicidade de CNPJ e razão social."""
        if not cnpj or not razao_social or not nome_fantasia:
            raise ValueError("CNPJ, razão social e nome fantasia são obrigatórios.")

        db = get_db()
        if db.fornecedores.find_one({"cnpj": cnpj}):
            raise ValueError(f"CNPJ '{cnpj}' já cadastrado.")
        if db.fornecedores.find_one({"razao_social": razao_social}):
            raise ValueError(f"Razão social '{razao_social}' já cadastrada.")

        doc = {
            "_id": get_next_id("fornecedores"),
            "cnpj": cnpj,
            "razao_social": razao_social,
            "nome_fantasia": nome_fantasia,
            "mail": mail,
            "telefone": telefone,
            "condicoes_pagamento": condicoes_pagamento,
            "endereco": endereco,
        }
        db.fornecedores.insert_one(doc)
        return _para_objeto(doc)

    @staticmethod
    def atualizar(id_fornecedor: int, **dados):
        """Atualiza os campos de um fornecedor existente."""
        atualizacoes = {c: v for c, v in dados.items() if c in _CAMPOS}
        resultado = get_db().fornecedores.update_one(
            {"_id": id_fornecedor}, {"$set": atualizacoes}
        )
        if resultado.matched_count == 0:
            raise ValueError("Fornecedor não encontrado.")
        return FornecedorService.buscar_por_id(id_fornecedor)

    @staticmethod
    def excluir(id_fornecedor: int):
        """Exclui um fornecedor pelo ID."""
        if get_db().fornecedores.delete_one({"_id": id_fornecedor}).deleted_count == 0:
            raise ValueError("Fornecedor não encontrado.")
