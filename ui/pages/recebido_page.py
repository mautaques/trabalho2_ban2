"""Página de Recebidos — produtos que já foram recebidos das reposições."""

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.recebido_service import RecebidoService


class RecebidoPage(QWidget):
    """Tabela com todos os produtos recebidos até o momento."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recebidos: list = []
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Recebidos")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Buscar por produto, fornecedor, filial ou nº pedido…"
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input, stretch=1)

        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.clicked.connect(self.load_data)
        toolbar.addWidget(btn_atualizar)

        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID Receb.", "Nº Pedido", "Produto", "Quantidade",
            "Fornecedor", "Filial", "Data", "Divergência",
        ])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def load_data(self):
        """Carrega todos os produtos recebidos."""
        try:
            self._recebidos = RecebidoService.listar_todos()
            self._populate()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _on_search(self, text: str):
        try:
            if text.strip():
                self._recebidos = RecebidoService.buscar(text)
            else:
                self._recebidos = RecebidoService.listar_todos()
            self._populate()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _populate(self):
        self.table.setRowCount(len(self._recebidos))
        for row, r in enumerate(self._recebidos):
            data_str = r.data.strftime("%d/%m/%Y %H:%M") if r.data else ""
            valores = [
                str(r.id_recebido),
                str(r.numero_pedido),
                r.nome_produto or "",
                str(r.quantidade),
                r.fornecedor or "",
                r.filial or "",
                data_str,
                r.divergencia or "—",
            ]
            for col, valor in enumerate(valores):
                self.table.setItem(row, col, QTableWidgetItem(valor))
        self.table.resizeColumnsToContents()
