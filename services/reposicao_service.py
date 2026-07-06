"""Serviço de negócio para Reposição de Estoque.

Os itens do pedido ficam EMBUTIDOS no documento da reposição (array
``itens``). A lógica que no PostgreSQL era feita pelas funções
insere_pedido_reposicao(), recebe_reposicao() e altera_status_reposicao(),
e pelo gatilho trg_atualiza_total_reposicao, agora é feita aqui.
"""

import datetime
import re

from database import get_db, get_next_id
from models.documento import Documento

# "JOINs" da listagem: nomes do fornecedor e da filial de destino.
_LOOKUPS = [
    {
        "$lookup": {
            "from": "fornecedores",
            "localField": "id_fornecedor",
            "foreignField": "_id",
            "as": "fornecedor_doc",
        }
    },
    {
        "$lookup": {
            "from": "filiais",
            "localField": "id_filial_destino",
            "foreignField": "_id",
            "as": "filial_doc",
        }
    },
    {
        "$addFields": {
            "fornecedor": {
                "$ifNull": [{"$arrayElemAt": ["$fornecedor_doc.nome_fantasia", 0]}, None]
            },
            "filial": {
                "$ifNull": [{"$arrayElemAt": ["$filial_doc.nome_fantasia", 0]}, None]
            },
        }
    },
    {"$project": {"fornecedor_doc": 0, "filial_doc": 0}},
]


def _para_objeto(doc: dict) -> Documento:
    doc = dict(doc)
    doc["id_reposicao"] = doc.pop("_id")
    return Documento(doc)


def _soma_anos(data: datetime.datetime, anos: int) -> datetime.datetime:
    """Equivalente a data + INTERVAL 'n years' (trata 29/02)."""
    try:
        return data.replace(year=data.year + anos)
    except ValueError:
        return data.replace(year=data.year + anos, day=28)


class ReposicaoService:
    """Operações sobre pedidos de reposição."""

    @staticmethod
    def listar_todos():
        """Retorna todos os pedidos de reposição com fornecedor e filial."""
        pipeline = _LOOKUPS + [{"$sort": {"_id": -1}}]
        return [_para_objeto(d) for d in get_db().reposicoes.aggregate(pipeline)]

    @staticmethod
    def buscar(termo: str):
        """Busca reposições por número de pedido ou fornecedor."""
        regex = {"$regex": re.escape(termo), "$options": "i"}
        pipeline = _LOOKUPS + [
            {"$addFields": {"pedido_str": {"$toString": "$numero_pedido"}}},
            {"$match": {"$or": [{"pedido_str": regex}, {"fornecedor": regex}]}},
            {"$sort": {"_id": -1}},
        ]
        return [_para_objeto(d) for d in get_db().reposicoes.aggregate(pipeline)]

    @staticmethod
    def buscar_itens(id_reposicao: int):
        """Retorna os itens de um pedido de reposição (produto e lote)."""
        db = get_db()
        reposicao = db.reposicoes.find_one({"_id": id_reposicao})
        if not reposicao:
            return []

        itens = reposicao.get("itens", [])
        produtos = {
            p["_id"]: p
            for p in db.produtos.find(
                {"_id": {"$in": [i["id_produto"] for i in itens]}}
            )
        }
        lotes = {
            l["_id"]: l
            for l in db.lotes.find({"_id": {"$in": [i["id_lote"] for i in itens]}})
        }

        resultado = []
        for item in itens:
            produto = produtos.get(item["id_produto"])
            lote = lotes.get(item["id_lote"])
            resultado.append(Documento({
                "id_item_reposicao": item["id_item_reposicao"],
                "nome_produto": produto["nome_produto"] if produto else "",
                "numero_lote": lote["numero_lote"] if lote else "",
                "quantidade": item["quantidade"],
                "valor_unitario": item["valor_unitario"],
                "valor_total": item["valor_total"],
            }))
        return resultado

    @staticmethod
    def insere_pedido(id_fornecedor, id_filial_destino, itens):
        """Insere um pedido de reposição (antes função SQL insere_pedido_reposicao).

        O número do pedido é gerado automaticamente, o lote de cada item é
        resolvido a partir do produto (lote com validade mais recente; se o
        produto não tem lote, um novo é criado) e o valor total do pedido é
        calculado a partir dos itens (antes gatilho trg_atualiza_total_reposicao).
        """
        db = get_db()
        data_pedido = datetime.datetime.now()

        ultimo = db.reposicoes.find_one(sort=[("numero_pedido", -1)])
        numero_pedido = (ultimo["numero_pedido"] if ultimo else 0) + 1

        itens_doc = []
        valor_total = 0.0
        for seq, item in enumerate(itens, start=1):
            id_produto = item["id_produto"]
            quantidade = int(item["quantidade"])
            valor_unitario = float(item["valor_unitario"])

            # Lote do produto com a validade mais recente; se não houver, cria.
            lote = db.lotes.find_one(
                {"id_produto": id_produto}, sort=[("data_validade", -1)]
            )
            if lote is None:
                ultimo_lote = db.lotes.find_one(sort=[("numero_lote", -1)])
                lote = {
                    "_id": get_next_id("lotes"),
                    "id_produto": id_produto,
                    "id_fornecedor": id_fornecedor,
                    "numero_lote": (ultimo_lote["numero_lote"] if ultimo_lote else 0) + 1,
                    "data_fabricacao": data_pedido,
                    "data_validade": _soma_anos(data_pedido, 2),
                    "quantidade": 0,
                }
                db.lotes.insert_one(lote)

            subtotal = round(quantidade * valor_unitario, 2)
            itens_doc.append({
                "id_item_reposicao": seq,
                "id_produto": id_produto,
                "id_lote": lote["_id"],
                "id_recebido": None,
                "quantidade": quantidade,
                "valor_unitario": valor_unitario,
                "valor_total": subtotal,
            })
            valor_total += subtotal

        db.reposicoes.insert_one({
            "_id": get_next_id("reposicoes"),
            "id_fornecedor": id_fornecedor,
            "id_filial_destino": id_filial_destino,
            "numero_pedido": numero_pedido,
            "data_pedido": data_pedido,
            "status": "PENDENTE",
            "valor_total": round(valor_total, 2),
            "itens": itens_doc,
        })
        return (
            f"Pedido {numero_pedido} inserido com sucesso. "
            "Totais processados automaticamente."
        )

    @staticmethod
    def receber(id_reposicao, divergencia=None):
        """Recebe um pedido de reposição (antes função SQL recebe_reposicao).

        Todos os itens do pedido entram no estoque da filial de destino com
        suas próprias quantidades e o recebimento é registrado na coleção
        *recebidos*.
        """
        db = get_db()
        reposicao = db.reposicoes.find_one({"_id": id_reposicao})
        if reposicao is None:
            raise ValueError(f"Reposição {id_reposicao} não encontrada.")

        if reposicao["status"] not in ("APROVADO", "ENVIADO"):
            raise ValueError(
                "Só é possível receber um pedido APROVADO ou ENVIADO "
                f"(status atual: {reposicao['status']})."
            )

        id_filial = reposicao["id_filial_destino"]
        itens = reposicao.get("itens", [])
        total = 0
        for item in itens:
            resultado = db.estoques.update_one(
                {"id_produto": item["id_produto"], "id_filial": id_filial},
                {"$inc": {"quantidade": item["quantidade"]}},
            )
            # Produto sem linha de estoque na filial (produto novo): cria.
            if resultado.matched_count == 0:
                db.estoques.insert_one({
                    "_id": get_next_id("estoques"),
                    "id_lote": item["id_lote"],
                    "id_produto": item["id_produto"],
                    "id_filial": id_filial,
                    "estoque_maximo": 0,
                    "estoque_minimo": 0,
                    "quantidade": item["quantidade"],
                })
            total += item["quantidade"]

        id_recebido = get_next_id("recebidos")
        db.recebidos.insert_one({
            "_id": id_recebido,
            "id_reposicao": id_reposicao,
            "quantidade": total,
            "data": datetime.datetime.now(),
            "divergencia": divergencia,
        })

        # Marca como RECEBIDO e liga os itens da reposição a este recebimento.
        for item in itens:
            item["id_recebido"] = id_recebido
        db.reposicoes.update_one(
            {"_id": id_reposicao},
            {"$set": {"status": "RECEBIDO", "itens": itens}},
        )
        return f"Reposição recebida: {total} unidades adicionadas ao estoque."

    # ── Transições de status ─────────────────────────────────────────────

    @staticmethod
    def _altera_status(id_reposicao, novo_status):
        """Valida e aplica a transição de status (antes função SQL).

        PENDENTE -> APROVADO -> ENVIADO -> (RECEBIDO via receber)
        PENDENTE/APROVADO/ENVIADO -> CANCELADO
        RECEBIDO e CANCELADO são estados finais.
        """
        db = get_db()
        reposicao = db.reposicoes.find_one({"_id": id_reposicao})
        if reposicao is None:
            raise ValueError(f"Reposição {id_reposicao} não encontrada.")

        status_atual = reposicao["status"]
        if novo_status == "APROVADO":
            if status_atual != "PENDENTE":
                raise ValueError(
                    "Só é possível aprovar um pedido PENDENTE "
                    f"(status atual: {status_atual})."
                )
        elif novo_status == "ENVIADO":
            if status_atual != "APROVADO":
                raise ValueError(
                    "Só é possível enviar um pedido APROVADO "
                    f"(status atual: {status_atual})."
                )
        elif novo_status == "CANCELADO":
            if status_atual in ("RECEBIDO", "CANCELADO"):
                raise ValueError(
                    f"Não é possível cancelar um pedido com status {status_atual}."
                )
        else:
            raise ValueError(
                f"Status inválido para esta operação: {novo_status}. "
                "Use APROVADO, ENVIADO ou CANCELADO."
            )

        db.reposicoes.update_one(
            {"_id": id_reposicao}, {"$set": {"status": novo_status}}
        )
        return (
            f"Pedido {id_reposicao}: status alterado de "
            f"{status_atual} para {novo_status}."
        )

    @staticmethod
    def aprovar(id_reposicao):
        """Marca o pedido como APROVADO (apenas se estiver PENDENTE)."""
        return ReposicaoService._altera_status(id_reposicao, "APROVADO")

    @staticmethod
    def enviar(id_reposicao):
        """Marca o pedido como ENVIADO (apenas se estiver APROVADO)."""
        return ReposicaoService._altera_status(id_reposicao, "ENVIADO")

    @staticmethod
    def cancelar(id_reposicao):
        """Cancela o pedido (se não estiver RECEBIDO nem CANCELADO)."""
        return ReposicaoService._altera_status(id_reposicao, "CANCELADO")
