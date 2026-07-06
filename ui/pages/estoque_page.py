"""Página de Estoque — consulta de quantidades com aviso de nível crítico."""

from PyQt6.QtGui import QBrush, QColor, QFont
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

from services.estoque_service import EstoqueService

# Cores do realce de linha crítica (fundo vermelho claro, texto vermelho escuro).
_COR_CRITICO_FUNDO = QColor(255, 224, 224)
_COR_CRITICO_TEXTO = QColor(150, 0, 0)


class EstoquePage(QWidget):
    """Tabela de estoque por produto/filial/lote com indicador de situação."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._estoques: list = []
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Estoque")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por produto ou filial…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input, stretch=1)

        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.clicked.connect(self.load_data)
        toolbar.addWidget(btn_atualizar)

        layout.addLayout(toolbar)

        # Aviso resumido de itens críticos.
        self.alerta_label = QLabel()
        self.alerta_label.setFont(QFont("", 11, QFont.Weight.Bold))
        layout.addWidget(self.alerta_label)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Produto", "Filial", "Lote", "Validade",
            "Quantidade", "Mínimo", "Situação",
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
        """Carrega todo o estoque."""
        try:
            self._estoques = EstoqueService.listar_todos()
            self._populate()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _on_search(self, text: str):
        try:
            if text.strip():
                self._estoques = EstoqueService.buscar(text)
            else:
                self._estoques = EstoqueService.listar_todos()
            self._populate()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _populate(self):
        self.table.setRowCount(len(self._estoques))
        criticos = 0

        for row, e in enumerate(self._estoques):
            critico = bool(e.critico)
            if critico:
                criticos += 1

            validade = e.data_validade.strftime("%d/%m/%Y") if e.data_validade else ""
            situacao = "⚠ CRÍTICO" if critico else "OK"

            valores = [
                str(e.id_estoque),
                e.nome_produto or "",
                e.filial or "",
                str(e.numero_lote),
                validade,
                str(e.quantidade),
                str(e.estoque_minimo),
                situacao,
            ]

            for col, valor in enumerate(valores):
                cell = QTableWidgetItem(valor)
                if critico:
                    cell.setBackground(QBrush(_COR_CRITICO_FUNDO))
                    cell.setForeground(QBrush(_COR_CRITICO_TEXTO))
                self.table.setItem(row, col, cell)

        self.table.resizeColumnsToContents()
        self._atualiza_alerta(criticos)

    def _atualiza_alerta(self, criticos: int):
        if criticos > 0:
            plural = "itens" if criticos > 1 else "item"
            self.alerta_label.setText(
                f"⚠ {criticos} {plural} em nível crítico de estoque."
            )
            self.alerta_label.setStyleSheet("color: #960000;")
        else:
            self.alerta_label.setText("✓ Nenhum item em nível crítico.")
            self.alerta_label.setStyleSheet("color: #1b7a1b;")
