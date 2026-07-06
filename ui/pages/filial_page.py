"""Página de CRUD para Filiais."""

from services.filial_service import FilialService
from ui.pages.crud_page import CrudPage


class FilialPage(CrudPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_page(
            title="Filiais",
            columns=[
                {"key": "id_filial", "label": "ID"},
                {"key": "codigo_filial", "label": "Código"},
                {"key": "cnpj", "label": "CNPJ"},
                {"key": "nome_fantasia", "label": "Nome Fantasia"},
                {"key": "nome_gerente", "label": "Gerente"},
                {"key": "telefone", "label": "Telefone"},
                {"key": "endereco", "label": "Endereço"},
            ],
            form_fields=[
                {"name": "codigo_filial", "label": "Código da Filial", "type": "text",
                 "required": True, "max_length": 10},
                {"name": "cnpj", "label": "CNPJ", "type": "text",
                 "required": True, "max_length": 20},
                {"name": "nome_fantasia", "label": "Nome Fantasia", "type": "text",
                 "required": True, "max_length": 150},
                {"name": "nome_gerente", "label": "Nome do Gerente", "type": "text",
                 "required": True, "max_length": 150},
                {"name": "telefone", "label": "Telefone", "type": "text",
                 "max_length": 20},
                {"name": "endereco", "label": "Endereço", "type": "textarea"},
            ],
            service=FilialService,
            id_key="id_filial",
        )
