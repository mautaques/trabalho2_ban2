"""Serviço de negócio para Vendas.

No modelo de documentos, os itens da venda ficam EMBUTIDOS no próprio
documento da venda (array ``itens``). A lógica que no PostgreSQL era feita
por funções e gatilhos agora é feita aqui:

- geração do cupom fiscal aleatório e único (função insere_pedido_venda);
- baixa do estoque por lote com validade mais próxima (trg_baixa_estoque_venda);
- cálculo do valor total dos itens e da venda (trg_atualiza_total_venda e a
  coluna gerada valor_total de item_venda);
- validação de que o vendedor pertence à filial da venda
  (trg_valida_vendedor_filial).
"""

import datetime
import random
import re

from database import get_db, get_next_id
from models.documento import Documento

# "JOINs" da listagem: filial, vendedor e cliente da venda.
_LOOKUPS = [
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
            "from": "vendedores",
            "localField": "id_vendedor",
            "foreignField": "_id",
            "as": "vendedor",
        }
    },
    {
        "$lookup": {
            "from": "clientes",
            "localField": "id_cliente",
            "foreignField": "_id",
            "as": "cliente",
        }
    },
    {
        "$addFields": {
            "filial": {"$ifNull": [{"$arrayElemAt": ["$filial", 0]}, None]},
            "vendedor": {"$ifNull": [{"$arrayElemAt": ["$vendedor", 0]}, None]},
            "cliente": {"$ifNull": [{"$arrayElemAt": ["$cliente", 0]}, None]},
        }
    },
]


def _para_objeto(doc: dict) -> Documento:
    doc = dict(doc)
    doc["id_venda"] = doc.pop("_id")
    return Documento(doc)


def _baixa_estoque(db, id_filial: int, id_produto: int, quantidade: int):
    """Dá baixa no estoque usando o lote com vencimento mais próximo.

    Equivalente ao gatilho trg_baixa_estoque_venda (FIFO por validade).
    """
    candidatos = list(
        db.estoques.aggregate([
            {
                "$match": {
                    "id_produto": id_produto,
                    "id_filial": id_filial,
                    "quantidade": {"$gte": quantidade},
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
            {"$addFields": {"lote": {"$arrayElemAt": ["$lote", 0]}}},
            {"$sort": {"lote.data_validade": 1}},
            {"$limit": 1},
        ])
    )
    if not candidatos:
        raise ValueError(
            f"Estoque insuficiente ou produto não encontrado para o ID "
            f"{id_produto} na filial {id_filial}"
        )
    db.estoques.update_one(
        {"_id": candidatos[0]["_id"]}, {"$inc": {"quantidade": -quantidade}}
    )


class VendaService:
    """Consultas e registro de vendas (itens embutidos no documento)."""

    # ── Venda ────────────────────────────────────────────────────────────

    @staticmethod
    def listar_todos():
        """Retorna todas as vendas com filial, vendedor e cliente carregados."""
        pipeline = _LOOKUPS + [{"$sort": {"_id": -1}}]
        return [_para_objeto(d) for d in get_db().vendas.aggregate(pipeline)]

    @staticmethod
    def buscar(termo: str):
        """Busca vendas por cupom fiscal ou nome do cliente.

        Vendas sem cliente também aparecem (filtradas pelo cupom fiscal).
        """
        regex = {"$regex": re.escape(termo), "$options": "i"}
        pipeline = _LOOKUPS + [
            {"$addFields": {"cupom_str": {"$toString": "$cupom_fiscal"}}},
            {"$match": {"$or": [{"cupom_str": regex}, {"cliente.nome": regex}]}},
            {"$sort": {"_id": -1}},
        ]
        return [_para_objeto(d) for d in get_db().vendas.aggregate(pipeline)]

    @staticmethod
    def inserir_pedido(id_filial, id_vendedor, id_cliente,
                       forma_pagamento, itens, data_hora=None):
        """Registra uma venda completa (com itens).

        O cupom fiscal é gerado automaticamente (aleatório e único), o estoque
        é baixado por item e os totais são calculados — tudo que no modelo
        relacional era feito pela função insere_pedido_venda() e pelos
        gatilhos do banco.
        """
        if not id_filial or not id_vendedor:
            raise ValueError("Filial e vendedor são obrigatórios.")
        if not itens:
            raise ValueError("Adicione ao menos um produto à venda.")

        db = get_db()

        # Validação vendedor × filial (antes feita por trg_valida_vendedor_filial)
        vendedor = db.vendedores.find_one({"_id": id_vendedor})
        if vendedor is None:
            raise ValueError("Vendedor não encontrado.")
        if vendedor["id_filial"] != id_filial:
            raise ValueError(
                f"O vendedor {id_vendedor} pertence à filial "
                f"{vendedor['id_filial']} e não pode vender na filial {id_filial}."
            )

        # Cupom fiscal aleatório (6 dígitos) e único.
        while True:
            cupom_fiscal = random.randint(100000, 999999)
            if db.vendas.find_one({"cupom_fiscal": cupom_fiscal}) is None:
                break

        itens_doc = []
        valor_total = 0.0
        for seq, item in enumerate(itens, start=1):
            quantidade = int(item["quantidade"])
            preco_unitario = float(item["preco_unitario"])
            desconto = float(item.get("desconto") or 0)

            _baixa_estoque(db, id_filial, item["id_produto"], quantidade)

            bruto = quantidade * preco_unitario
            subtotal = round(bruto - bruto * desconto, 2)
            itens_doc.append({
                "id_item_venda": seq,
                "id_produto": item["id_produto"],
                "id_prescricao": item.get("id_prescricao"),
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
                "desconto": desconto,
                "valor_total": subtotal,
            })
            valor_total += subtotal

        db.vendas.insert_one({
            "_id": get_next_id("vendas"),
            "id_filial": id_filial,
            "id_vendedor": id_vendedor,
            "id_cliente": id_cliente,
            "cupom_fiscal": cupom_fiscal,
            "data_hora": data_hora or datetime.datetime.now(),
            "forma_pagamento": forma_pagamento,
            "valor_total": round(valor_total, 2),
            "itens": itens_doc,
        })
        return (
            f"Venda inserida com sucesso. Cupom fiscal gerado: {cupom_fiscal}. "
            "Estoque baixado e totais calculados."
        )

    @staticmethod
    def excluir(id_venda: int):
        """Exclui uma venda e todos os seus itens (embutidos no documento)."""
        if get_db().vendas.delete_one({"_id": id_venda}).deleted_count == 0:
            raise ValueError("Venda não encontrada.")

    # ── Itens da Venda ───────────────────────────────────────────────────

    @staticmethod
    def buscar_itens(id_venda: int):
        """Retorna os itens de uma venda com os produtos carregados."""
        db = get_db()
        venda = db.vendas.find_one({"_id": id_venda})
        if not venda:
            return []

        ids_produtos = [i["id_produto"] for i in venda.get("itens", [])]
        produtos = {
            p["_id"]: p for p in db.produtos.find({"_id": {"$in": ids_produtos}})
        }

        itens = []
        for item in venda.get("itens", []):
            item = dict(item)
            item["produto"] = produtos.get(item["id_produto"])
            itens.append(Documento(item))
        return itens
