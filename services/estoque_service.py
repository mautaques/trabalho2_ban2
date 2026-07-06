"""Serviço de negócio para consulta de Estoque.

Expõe o estoque por produto/filial/lote junto de um indicador de situação:
CRÍTICO quando a quantidade está no nível mínimo (ou abaixo), caso contrário OK.
"""

import re

from database import get_db
from models.documento import Documento

# Pipeline base reaproveitado por listar_todos() e buscar(). O campo "critico"
# é calculado na agregação: True quando quantidade <= estoque_minimo.
_PIPELINE_BASE = [
    {
        "$lookup": {
            "from": "produtos",
            "localField": "id_produto",
            "foreignField": "_id",
            "as": "produto",
        }
    },
    {
        "$lookup": {
            "from": "filiais",
            "localField": "id_filial",
            "foreignField": "_id",
            "as": "filial",
        }
    },
    {
        "$lookup": {
            "from": "lotes",
            "localField": "id_lote",
            "foreignField": "_id",
            "as": "lote",
        }
    },
    {
        "$project": {
            "_id": 0,
            "id_estoque": "$_id",
            "nome_produto": {
                "$ifNull": [{"$arrayElemAt": ["$produto.nome_produto", 0]}, None]
            },
            "filial": {
                "$ifNull": [{"$arrayElemAt": ["$filial.nome_fantasia", 0]}, None]
            },
            "numero_lote": {
                "$ifNull": [{"$arrayElemAt": ["$lote.numero_lote", 0]}, None]
            },
            "data_validade": {
                "$ifNull": [{"$arrayElemAt": ["$lote.data_validade", 0]}, None]
            },
            "quantidade": 1,
            "estoque_minimo": 1,
            "estoque_maximo": 1,
            "critico": {"$lte": ["$quantidade", "$estoque_minimo"]},
        }
    },
]

_ORDENACAO = [{"$sort": {"critico": -1, "nome_produto": 1}}]


class EstoqueService:
    """Consultas sobre o estoque (somente leitura)."""

    @staticmethod
    def listar_todos():
        """Retorna todo o estoque, com os críticos primeiro."""
        pipeline = _PIPELINE_BASE + _ORDENACAO
        return [Documento(d) for d in get_db().estoques.aggregate(pipeline)]

    @staticmethod
    def buscar(termo: str):
        """Busca o estoque por produto ou filial."""
        regex = {"$regex": re.escape(termo), "$options": "i"}
        pipeline = _PIPELINE_BASE + [
            {"$match": {"$or": [{"nome_produto": regex}, {"filial": regex}]}},
        ] + _ORDENACAO
        return [Documento(d) for d in get_db().estoques.aggregate(pipeline)]

    @staticmethod
    def contar_criticos() -> int:
        """Conta quantos itens de estoque estão em nível crítico."""
        return get_db().estoques.count_documents(
            {"$expr": {"$lte": ["$quantidade", "$estoque_minimo"]}}
        )
