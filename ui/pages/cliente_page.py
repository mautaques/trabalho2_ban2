"""Página de CRUD para Clientes."""

from services.cliente_service import ClienteService
from ui.pages.crud_page import CrudPage


class ClientePage(CrudPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_page(
            title="Clientes",
            columns=[
                {"key": "id_cliente", "label": "ID"},
                {"key": "nome", "label": "Nome"},
                {"key": "cpf", "label": "CPF"},
                {"key": "telefone", "label": "Telefone"},
                {"key": "mail", "label": "E-mail"},
                {"key": "data_nascimento", "label": "Data Nasc."},
            ],
            form_fields=[
                {"name": "nome", "label": "Nome", "type": "text",
                 "required": True, "max_length": 150},
                {"name": "cpf", "label": "CPF", "type": "text",
                 "required": True, "max_length": 12},
                {"name": "telefone", "label": "Telefone", "type": "text",
                 "max_length": 20},
                {"name": "mail", "label": "E-mail", "type": "text",
                 "max_length": 100},
                {"name": "data_nascimento", "label": "Data de Nascimento",
                 "type": "date"},
            ],
            service=ClienteService,
            id_key="id_cliente",
        )
