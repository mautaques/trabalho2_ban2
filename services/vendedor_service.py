"""Serviço de negócio para a entidade Vendedor."""

import re

from database import get_db, get_next_id, para_datetime
from models.documento import Documento

_CAMPOS = (
    "id_filial", "nome", "cpf", "matricula", "cargo",
    "data_admissao", "comissao_percentual",
)

# "JOIN" com a filial: traz o nome fantasia para exibição nas tabelas.
_LOOKUP_FILIAL = [
    {
        "$lookup": {
            "from": "filiais",
            "localField": "id_filial",
            "foreignField": "_id",
            "as": "filial",
        }
    },
    {"$addFields": {"filial": {"$ifNull": [{"$arrayElemAt": ["$filial", 0]}, None]}}},
]


def _para_objeto(doc: dict) -> Documento:
    doc = dict(doc)
    doc["id_vendedor"] = doc.pop("_id")
    if doc.get("data_admissao"):
        doc["data_admissao"] = doc["data_admissao"].date()
    filial = doc.pop("filial", None)
    doc["filial_nome"] = filial["nome_fantasia"] if filial else ""
    return Documento(doc)


class VendedorService:
    """CRUD e buscas para a coleção *vendedores*."""

    @staticmethod
    def listar_todos():
        """Retorna todos os vendedores (com a filial) ordenados por nome."""
        pipeline = _LOOKUP_FILIAL + [{"$sort": {"nome": 1}}]
        return [_para_objeto(d) for d in get_db().vendedores.aggregate(pipeline)]

    @staticmethod
    def buscar_por_id(id_vendedor: int):
        """Retorna um vendedor pelo ID."""
        doc = get_db().vendedores.find_one({"_id": id_vendedor})
        return _para_objeto(doc) if doc else None

    @staticmethod
    def listar_por_filial(id_filial: int):
        """Retorna os vendedores de uma filial, ordenados por nome."""
        return [
            _para_objeto(d)
            for d in get_db().vendedores.find({"id_filial": id_filial}).sort("nome", 1)
        ]

    @staticmethod
    def buscar(termo: str):
        """Busca vendedores por nome, CPF ou cargo."""
        regex = {"$regex": re.escape(termo), "$options": "i"}
        pipeline = [
            {"$match": {"$or": [{"nome": regex}, {"cpf": regex}, {"cargo": regex}]}},
        ] + _LOOKUP_FILIAL + [{"$sort": {"nome": 1}}]
        return [_para_objeto(d) for d in get_db().vendedores.aggregate(pipeline)]

    @staticmethod
    def criar(
        nome,
        cpf,
        matricula,
        cargo,
        data_admissao,
        id_filial,
        comissao_percentual=None,
    ):
        """Cria um novo vendedor. Valida unicidade de CPF e matrícula."""
        if not nome or not cpf or not cargo:
            raise ValueError("Nome, CPF e cargo são obrigatórios.")
        if not matricula:
            raise ValueError("Matrícula é obrigatória.")
        if not data_admissao:
            raise ValueError("Data de admissão é obrigatória.")
        if not id_filial:
            raise ValueError("Filial é obrigatória.")

        db = get_db()
        if db.vendedores.find_one({"cpf": cpf}):
            raise ValueError(f"CPF '{cpf}' já cadastrado.")
        if db.vendedores.find_one({"matricula": int(matricula)}):
            raise ValueError(f"Matrícula '{matricula}' já cadastrada.")

        doc = {
            "_id": get_next_id("vendedores"),
            "id_filial": id_filial,
            "nome": nome,
            "cpf": cpf,
            "matricula": int(matricula),
            "cargo": cargo,
            "data_admissao": para_datetime(data_admissao),
            "comissao_percentual": comissao_percentual,
        }
        db.vendedores.insert_one(doc)
        return _para_objeto(doc)

    @staticmethod
    def atualizar(id_vendedor: int, **dados):
        """Atualiza os campos de um vendedor existente."""
        atualizacoes = {
            campo: para_datetime(valor) if campo == "data_admissao" else valor
            for campo, valor in dados.items()
            if campo in _CAMPOS
        }
        resultado = get_db().vendedores.update_one(
            {"_id": id_vendedor}, {"$set": atualizacoes}
        )
        if resultado.matched_count == 0:
            raise ValueError("Vendedor não encontrado.")
        return VendedorService.buscar_por_id(id_vendedor)

    @staticmethod
    def excluir(id_vendedor: int):
        """Exclui um vendedor pelo ID."""
        if get_db().vendedores.delete_one({"_id": id_vendedor}).deleted_count == 0:
            raise ValueError("Vendedor não encontrado.")
