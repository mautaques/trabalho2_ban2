"""Serviço de negócio para consulta de Recebimentos.

Lista os produtos efetivamente recebidos: cada documento de *recebidos* está
ligado a um pedido de reposição, cujos itens (produtos) ficam embutidos no
documento da reposição. A agregação junta tudo para mostrar, por produto,
o que já entrou no estoque.
"""

import re

from database import get_db
from models.documento import Documento

# Pipeline base reaproveitado por listar_todos() e buscar().
_PIPELINE_BASE = [
    {
        "$lookup": {
            "from": "reposicoes",
            "localField": "id_reposicao",
            "foreignField": "_id",
            "as": "rep",
        }
    },
    {"$unwind": "$rep"},
    # Uma linha por item do pedido (equivalente ao JOIN com item_reposicao).
    {"$unwind": "$rep.itens"},
    {
        "$lookup": {
            "from": "produtos",
            "localField": "rep.itens.id_produto",
            "foreignField": "_id",
            "as": "produto",
        }
    },
    {
        "$lookup": {
            "from": "fornecedores",
            "localField": "rep.id_fornecedor",
            "foreignField": "_id",
            "as": "fornecedor_doc",
        }
    },
    {
        "$lookup": {
            "from": "filiais",
            "localField": "rep.id_filial_destino",
            "foreignField": "_id",
            "as": "filial_doc",
        }
    },
    {
        "$project": {
            "_id": 0,
            "id_recebido": "$_id",
            "numero_pedido": "$rep.numero_pedido",
            "nome_produto": {
                "$ifNull": [{"$arrayElemAt": ["$produto.nome_produto", 0]}, None]
            },
            "quantidade": "$rep.itens.quantidade",
            "fornecedor": {
                "$ifNull": [{"$arrayElemAt": ["$fornecedor_doc.nome_fantasia", 0]}, None]
            },
            "filial": {
                "$ifNull": [{"$arrayElemAt": ["$filial_doc.nome_fantasia", 0]}, None]
            },
            "data": 1,
            "divergencia": 1,
        }
    },
]

_ORDENACAO = [{"$sort": {"data": -1, "nome_produto": 1}}]


class RecebidoService:
    """Consultas sobre produtos recebidos (somente leitura)."""

    @staticmethod
    def listar_todos():
        """Retorna todos os produtos recebidos, mais recentes primeiro."""
        pipeline = _PIPELINE_BASE + _ORDENACAO
        return [Documento(d) for d in get_db().recebidos.aggregate(pipeline)]

    @staticmethod
    def buscar(termo: str):
        """Busca por produto, fornecedor, filial ou número do pedido."""
        regex = {"$regex": re.escape(termo), "$options": "i"}
        pipeline = _PIPELINE_BASE + [
            {"$addFields": {"pedido_str": {"$toString": "$numero_pedido"}}},
            {
                "$match": {
                    "$or": [
                        {"nome_produto": regex},
                        {"fornecedor": regex},
                        {"filial": regex},
                        {"pedido_str": regex},
                    ]
                }
            },
        ] + _ORDENACAO
        return [Documento(d) for d in get_db().recebidos.aggregate(pipeline)]
