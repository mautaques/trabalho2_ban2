"""Serviço de negócio para a entidade Produto."""

import re

from database import get_db, get_next_id
from models.documento import Documento

_CAMPOS = (
    "codigo_de_barras", "nome_produto", "categoria", "fabricante",
    "principio_ativo", "preco_custo", "preco_venda", "descricao",
)


def _margem_lucro(preco_custo, preco_venda):
    """Equivalente à coluna gerada margem_lucro (preco_venda - preco_custo)."""
    if preco_custo is None or preco_venda is None:
        return None
    return round(float(preco_venda) - float(preco_custo), 2)


def _para_objeto(doc: dict) -> Documento:
    doc = dict(doc)
    doc["id_produto"] = doc.pop("_id")
    return Documento(doc)


class ProdutoService:
    """CRUD e buscas para a coleção *produtos*."""

    @staticmethod
    def listar_todos():
        """Retorna todos os produtos ordenados por nome."""
        return [
            _para_objeto(d) for d in get_db().produtos.find().sort("nome_produto", 1)
        ]

    @staticmethod
    def buscar_por_id(id_produto: int):
        """Retorna um produto pelo ID."""
        doc = get_db().produtos.find_one({"_id": id_produto})
        return _para_objeto(doc) if doc else None

    @staticmethod
    def buscar(termo: str):
        """Busca produtos por nome, fabricante, código de barras ou categoria."""
        regex = {"$regex": re.escape(termo), "$options": "i"}
        filtro = {
            "$or": [
                {"nome_produto": regex},
                {"fabricante": regex},
                {"categoria": regex},
                # codigo_de_barras é numérico: converte para texto antes do regex.
                {
                    "$expr": {
                        "$regexMatch": {
                            "input": {"$toString": "$codigo_de_barras"},
                            "regex": re.escape(termo),
                            "options": "i",
                        }
                    }
                },
            ]
        }
        return [
            _para_objeto(d)
            for d in get_db().produtos.find(filtro).sort("nome_produto", 1)
        ]

    @staticmethod
    def criar(
        codigo_de_barras,
        nome_produto,
        categoria,
        fabricante,
        principio_ativo=None,
        preco_custo=None,
        preco_venda=None,
        descricao=None,
    ):
        """Cria um novo produto. Valida campos obrigatórios e unicidade do código."""
        if not nome_produto or not fabricante:
            raise ValueError("Nome do produto e fabricante são obrigatórios.")
        if not codigo_de_barras:
            raise ValueError("Código de barras é obrigatório.")

        db = get_db()
        if db.produtos.find_one({"codigo_de_barras": int(codigo_de_barras)}):
            raise ValueError(
                f"Código de barras '{codigo_de_barras}' já cadastrado."
            )

        doc = {
            "_id": get_next_id("produtos"),
            "codigo_de_barras": int(codigo_de_barras),
            "nome_produto": nome_produto,
            "categoria": categoria,
            "fabricante": fabricante,
            "principio_ativo": principio_ativo,
            "preco_custo": preco_custo,
            "preco_venda": preco_venda,
            "margem_lucro": _margem_lucro(preco_custo, preco_venda),
            "descricao": descricao,
        }
        db.produtos.insert_one(doc)
        return _para_objeto(doc)

    @staticmethod
    def atualizar(id_produto: int, **dados):
        """Atualiza os campos de um produto existente, recalculando a margem."""
        db = get_db()
        produto = db.produtos.find_one({"_id": id_produto})
        if not produto:
            raise ValueError("Produto não encontrado.")

        # Não permitir alterar margem_lucro diretamente (campo calculado)
        dados.pop("margem_lucro", None)
        atualizacoes = {c: v for c, v in dados.items() if c in _CAMPOS}
        if "codigo_de_barras" in atualizacoes:
            atualizacoes["codigo_de_barras"] = int(atualizacoes["codigo_de_barras"])

        novo = {**produto, **atualizacoes}
        atualizacoes["margem_lucro"] = _margem_lucro(
            novo.get("preco_custo"), novo.get("preco_venda")
        )
        db.produtos.update_one({"_id": id_produto}, {"$set": atualizacoes})
        return ProdutoService.buscar_por_id(id_produto)

    @staticmethod
    def excluir(id_produto: int):
        """Exclui um produto pelo ID."""
        if get_db().produtos.delete_one({"_id": id_produto}).deleted_count == 0:
            raise ValueError("Produto não encontrado.")
