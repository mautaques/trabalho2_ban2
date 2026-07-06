"""Página de CRUD para Fornecedores."""

from services.fornecedor_service import FornecedorService
from ui.pages.crud_page import CrudPage


class FornecedorPage(CrudPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_page(
            title="Fornecedores",
            columns=[
                {"key": "id_fornecedor", "label": "ID"},
                {"key": "cnpj", "label": "CNPJ"},
                {"key": "razao_social", "label": "Razão Social"},
                {"key": "nome_fantasia", "label": "Nome Fantasia"},
                {"key": "telefone", "label": "Telefone"},
                {"key": "mail", "label": "E-mail"},
                {"key": "condicoes_pagamento", "label": "Cond. Pgto"},
            ],
            form_fields=[
                {"name": "cnpj", "label": "CNPJ", "type": "text",
                 "required": True, "max_length": 20},
                {"name": "razao_social", "label": "Razão Social", "type": "text",
                 "required": True, "max_length": 150},
                {"name": "nome_fantasia", "label": "Nome Fantasia", "type": "text",
                 "required": True, "max_length": 150},
                {"name": "mail", "label": "E-mail", "type": "text",
                 "max_length": 100},
                {"name": "telefone", "label": "Telefone", "type": "text",
                 "max_length": 20},
                {"name": "condicoes_pagamento", "label": "Condições de Pagamento",
                 "type": "text", "max_length": 50},
                {"name": "endereco", "label": "Endereço", "type": "textarea"},
            ],
            service=FornecedorService,
            id_key="id_fornecedor",
        )
