"""Serviço de negócio para Devoluções.

Os itens devolvidos ficam EMBUTIDOS no documento da devolução (array
``itens``). A lógica que no PostgreSQL era feita pela função SQL
devolver_produtos() — validações e retorno dos itens ao estoque — agora é
feita aqui.
"""

import datetime
import re

from database import get_db, get_next_id
from models.documento import Documento

# Pipeline base: junta a venda (cupom fiscal) e o cliente da venda.
_PIPELINE_BASE = [
    {
        "$lookup": {
            "from": "vendas",
            "localField": "id_venda",
            "foreignField": "_id",
            "as": "venda",
        }
    },
    {"$unwind": "$venda"},
    {
        "$lookup": {
            "from": "clientes",
            "localField": "venda.id_cliente",
            "foreignField": "_id",
            "as": "cliente_doc",
        }
    },
    {
        "$project": {
            "_id": 0,
            "id_devolucao": "$_id",
            "id_venda": 1,
            "cupom_fiscal": "$venda.cupom_fiscal",
            "cliente": {
                "$ifNull": [{"$arrayElemAt": ["$cliente_doc.nome", 0]}, None]
            },
            "data_devolucao": 1,
            "motivo": 1,
            "tipo": 1,
        }
    },
]

_ORDENACAO = [{"$sort": {"id_devolucao": -1}}]


class DevolucaoService:
    """Operações sobre devoluções de vendas."""

    @staticmethod
    def listar_todos():
        """Retorna todas as devoluções com dados da venda e cliente."""
        pipeline = _PIPELINE_BASE + _ORDENACAO
        return [Documento(d) for d in get_db().devolucoes.aggregate(pipeline)]

    @staticmethod
    def buscar(termo: str):
        """Busca devoluções por cupom fiscal, cliente ou motivo."""
        regex = {"$regex": re.escape(termo), "$options": "i"}
        pipeline = _PIPELINE_BASE + [
            {"$addFields": {"cupom_str": {"$toString": "$cupom_fiscal"}}},
            {
                "$match": {
                    "$or": [
                        {"cupom_str": regex},
                        {"cliente": regex},
                        {"motivo": regex},
                    ]
                }
            },
        ] + _ORDENACAO
        return [Documento(d) for d in get_db().devolucoes.aggregate(pipeline)]

    @staticmethod
    def buscar_itens(id_devolucao: int):
        """Retorna os itens de uma devolução."""
        db = get_db()
        devolucao = db.devolucoes.find_one({"_id": id_devolucao})
        if not devolucao:
            return []

        itens = devolucao.get("itens", [])
        produtos = {
            p["_id"]: p
            for p in db.produtos.find(
                {"_id": {"$in": [i["id_produto"] for i in itens]}}
            )
        }
        return [
            Documento({
                "id_item_devolucao": item["id_item_devolucao"],
                "nome_produto": (
                    produtos[item["id_produto"]]["nome_produto"]
                    if item["id_produto"] in produtos
                    else ""
                ),
                "quantidade": item["quantidade"],
            })
            for item in itens
        ]

    @staticmethod
    def buscar_itens_venda(id_venda: int):
        """Retorna os itens de uma venda para seleção na devolução."""
        db = get_db()
        venda = db.vendas.find_one({"_id": id_venda})
        if not venda:
            return []

        itens = venda.get("itens", [])
        produtos = {
            p["_id"]: p
            for p in db.produtos.find(
                {"_id": {"$in": [i["id_produto"] for i in itens]}}
            )
        }
        return [
            Documento({
                "id_item_venda": item["id_item_venda"],
                "id_produto": item["id_produto"],
                "nome_produto": (
                    produtos[item["id_produto"]]["nome_produto"]
                    if item["id_produto"] in produtos
                    else ""
                ),
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })
            for item in itens
        ]

    @staticmethod
    def devolver(id_venda, itens, motivo, tipo):
        """Registra a devolução e devolve os itens ao estoque.

        Antes função SQL devolver_produtos(). As validações acontecem ANTES
        de qualquer escrita, para não deixar dados pela metade.
        """
        db = get_db()
        venda = db.vendas.find_one({"_id": id_venda})
        if venda is None:
            raise ValueError(f"Venda {id_venda} não encontrada.")

        if tipo not in ("REEMBOLSO", "TROCA"):
            raise ValueError(
                f"Tipo de devolução inválido: {tipo}. Use REEMBOLSO ou TROCA."
            )

        vendidos = {
            item["id_produto"]: item["quantidade"]
            for item in venda.get("itens", [])
        }

        total_itens = 0
        itens_doc = []
        for seq, item in enumerate(itens, start=1):
            id_produto = item["id_produto"]
            quantidade = int(item["quantidade"])

            if id_produto not in vendidos:
                raise ValueError(
                    f"Produto {id_produto} não consta na venda {id_venda}. "
                    "Não pode ser devolvido."
                )
            if quantidade > vendidos[id_produto]:
                raise ValueError(
                    f"Quantidade devolvida ({quantidade}) maior que a vendida "
                    f"({vendidos[id_produto]}) para o produto {id_produto}."
                )

            itens_doc.append({
                "id_item_devolucao": seq,
                "id_produto": id_produto,
                "quantidade": quantidade,
            })
            total_itens += quantidade

        id_devolucao = get_next_id("devolucoes")
        db.devolucoes.insert_one({
            "_id": id_devolucao,
            "id_venda": id_venda,
            "data_devolucao": datetime.datetime.now(),
            "motivo": motivo,
            "tipo": tipo,
            "itens": itens_doc,
        })

        # Devolve os itens ao estoque da filial da venda (se houver linha).
        for item in itens_doc:
            db.estoques.update_one(
                {"id_produto": item["id_produto"], "id_filial": venda["id_filial"]},
                {"$inc": {"quantidade": item["quantidade"]}},
            )

        return (
            f"Devolução {id_devolucao} registrada. Venda: {id_venda}. "
            f"Tipo: {tipo}. Total de itens devolvidos: {total_itens}."
        )
