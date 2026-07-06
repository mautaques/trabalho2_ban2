"""Página Dashboard — visão geral com contadores."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class DashboardPage(QWidget):
    """Exibe cards com totais de cada entidade do sistema."""

    _CARDS = [
        ("clientes", "Clientes", "clientes"),
        ("produtos", "Produtos", "produtos"),
        ("vendedores", "Vendedores", "vendedores"),
        ("fornecedores", "Fornecedores", "fornecedores"),
        ("filiais", "Filiais", "filiais"),
        ("vendas", "Vendas", "vendas"),
        ("reposicoes", "Reposições", "reposicoes"),
        ("devolucoes", "Devoluções", "devolucoes"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._labels: dict[str, QLabel] = {}
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Dashboard")
        title.setFont(QFont("", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel("Visão geral do sistema de gerência de farmácia")
        subtitle.setFont(QFont("", 10))
        layout.addWidget(subtitle)
        layout.addSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(16)

        for i, (key, display, _table) in enumerate(self._CARDS):
            card = self._make_card(key, display)
            grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(grid)
        layout.addStretch()

    def _make_card(self, key: str, display: str) -> QGroupBox:
        group = QGroupBox(display)
        group.setMinimumSize(200, 120)
        vbox = QVBoxLayout(group)

        count_lbl = QLabel("—")
        count_lbl.setFont(QFont("", 28, QFont.Weight.Bold))
        count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(count_lbl)

        desc_lbl = QLabel("registros")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(desc_lbl)

        self._labels[key] = count_lbl
        return group

    def load_data(self):
        """Consulta o banco e atualiza os contadores."""
        from database import get_db

        try:
            db = get_db()
            for key, _display, colecao in self._CARDS:
                total = db[colecao].count_documents({})
                self._labels[key].setText(str(total))
        except Exception:
            for lbl in self._labels.values():
                lbl.setText("?")
