"""Serviço de negócio para a entidade Filial."""

import re

from database import get_db, get_next_id
from models.documento import Documento

_CAMPOS = (
    "codigo_filial", "cnpj", "nome_fantasia", "nome_gerente", "telefone", "endereco",
)


def _para_objeto(doc: dict) -> Documento:
    doc = dict(doc)
    doc["id_filial"] = doc.pop("_id")
    return Documento(doc)


class FilialService:
    """CRUD e buscas para a coleção *filiais*."""

    @staticmethod
    def listar_todos():
        """Retorna todas as filiais ordenadas por código."""
        return [
            _para_objeto(d) for d in get_db().filiais.find().sort("codigo_filial", 1)
        ]

    @staticmethod
    def buscar_por_id(id_filial: int):
        """Retorna uma filial pelo ID."""
        doc = get_db().filiais.find_one({"_id": id_filial})
        return _para_objeto(doc) if doc else None

    @staticmethod
    def buscar(termo: str):
        """Busca filiais por nome fantasia, código ou gerente."""
        regex = {"$regex": re.escape(termo), "$options": "i"}
        filtro = {
            "$or": [
                {"nome_fantasia": regex},
                {"codigo_filial": regex},
                {"nome_gerente": regex},
            ]
        }
        return [
            _para_objeto(d)
            for d in get_db().filiais.find(filtro).sort("codigo_filial", 1)
        ]

    @staticmethod
    def criar(
        codigo_filial,
        cnpj,
        nome_fantasia,
        nome_gerente,
        telefone=None,
        endereco=None,
    ):
        """Cria uma nova filial. Valida unicidade de código e CNPJ."""
        if not codigo_filial or not cnpj or not nome_fantasia or not nome_gerente:
            raise ValueError(
                "Código, CNPJ, nome fantasia e gerente são obrigatórios."
            )

        db = get_db()
        if db.filiais.find_one({"codigo_filial": codigo_filial}):
            raise ValueError(f"Código '{codigo_filial}' já cadastrado.")
        if db.filiais.find_one({"cnpj": cnpj}):
            raise ValueError(f"CNPJ '{cnpj}' já cadastrado.")

        doc = {
            "_id": get_next_id("filiais"),
            "codigo_filial": codigo_filial,
            "cnpj": cnpj,
            "nome_fantasia": nome_fantasia,
            "nome_gerente": nome_gerente,
            "telefone": telefone,
            "endereco": endereco,
        }
        db.filiais.insert_one(doc)
        return _para_objeto(doc)

    @staticmethod
    def atualizar(id_filial: int, **dados):
        """Atualiza os campos de uma filial existente."""
        atualizacoes = {c: v for c, v in dados.items() if c in _CAMPOS}
        resultado = get_db().filiais.update_one(
            {"_id": id_filial}, {"$set": atualizacoes}
        )
        if resultado.matched_count == 0:
            raise ValueError("Filial não encontrada.")
        return FilialService.buscar_por_id(id_filial)

    @staticmethod
    def excluir(id_filial: int):
        """Exclui uma filial pelo ID."""
        if get_db().filiais.delete_one({"_id": id_filial}).deleted_count == 0:
            raise ValueError("Filial não encontrada.")
