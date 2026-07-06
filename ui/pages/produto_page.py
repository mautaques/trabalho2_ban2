"""Página de CRUD para Produtos."""

from services.produto_service import ProdutoService
from ui.pages.crud_page import CrudPage


class ProdutoPage(CrudPage):
    def __init__(self, parent=None):
        super().__init__(parent)

        categorias = [
            ("Medicamento", "Medicamento"),
            ("Cosmético", "Cosmético"),
            ("Higiene Pessoal", "Higiene Pessoal"),
            ("Conveniência", "Conveniência"),
        ]

        self.init_page(
            title="Produtos",
            columns=[
                {"key": "id_produto", "label": "ID"},
                {"key": "codigo_de_barras", "label": "Cód. Barras"},
                {"key": "nome_produto", "label": "Nome"},
                {"key": "categoria", "label": "Categoria"},
                {"key": "fabricante", "label": "Fabricante"},
                {"key": "principio_ativo", "label": "Princípio Ativo"},
                {"key": "preco_custo", "label": "Preço Custo"},
                {"key": "preco_venda", "label": "Preço Venda"},
                {"key": "margem_lucro", "label": "Margem Lucro"},
            ],
            form_fields=[
                {"name": "codigo_de_barras", "label": "Código de Barras",
                 "type": "text", "required": True, "max_length": 20},
                {"name": "nome_produto", "label": "Nome do Produto",
                 "type": "text", "required": True, "max_length": 150},
                {"name": "categoria", "label": "Categoria",
                 "type": "combobox", "options": categorias},
                {"name": "fabricante", "label": "Fabricante",
                 "type": "text", "required": True, "max_length": 150},
                {"name": "principio_ativo", "label": "Princípio Ativo",
                 "type": "text", "max_length": 50},
                {"name": "preco_custo", "label": "Preço de Custo (R$)",
                 "type": "float", "decimals": 2, "min": 0.0, "max": 99999.99},
                {"name": "preco_venda", "label": "Preço de Venda (R$)",
                 "type": "float", "decimals": 2, "min": 0.0, "max": 99999.99},
                {"name": "descricao", "label": "Descrição", "type": "textarea"},
            ],
            service=ProdutoService,
            id_key="id_produto",
        )
