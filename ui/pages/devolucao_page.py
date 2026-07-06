"""Página de Devoluções — master-detail (Devoluções ↔ Itens)."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services.devolucao_service import DevolucaoService
from services.venda_service import VendaService


class DevolucaoPage(QWidget):
    """Painel master-detail: lista de devoluções + itens devolvidos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._devolucoes: list = []
        self._itens: list = []
        self._selected_dev = None
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Devoluções")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por cupom fiscal, cliente ou motivo…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input, stretch=1)

        for text, slot in [
            ("Nova Devolução", self._on_nova_devolucao),
            ("Atualizar", self.load_data),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            toolbar.addWidget(btn)

        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.dev_table = self._make_table(
            ["ID", "Venda", "Cupom Fiscal", "Cliente",
             "Data Devolução", "Motivo", "Tipo"]
        )
        self.dev_table.selectionModel().selectionChanged.connect(
            self._on_dev_selected
        )
        splitter.addWidget(self.dev_table)

        items_panel = QWidget()
        items_layout = QVBoxLayout(items_panel)
        items_layout.setContentsMargins(0, 8, 0, 0)

        self.items_title = QLabel("Itens Devolvidos")
        self.items_title.setFont(QFont("", 12, QFont.Weight.Bold))
        items_layout.addWidget(self.items_title)

        self.items_table = self._make_table(
            ["ID", "Produto", "Quantidade"]
        )
        items_layout.addWidget(self.items_table)

        splitter.addWidget(items_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

    @staticmethod
    def _make_table(headers: list[str]) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.horizontalHeader().setStretchLastSection(True)
        t.verticalHeader().setVisible(False)
        return t

    def load_data(self):
        """Carrega todas as devoluções."""
        try:
            self._devolucoes = DevolucaoService.listar_todos()
            self._populate_devolucoes()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _on_search(self, text: str):
        try:
            if text.strip():
                self._devolucoes = DevolucaoService.buscar(text)
            else:
                self._devolucoes = DevolucaoService.listar_todos()
            self._populate_devolucoes()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _populate_devolucoes(self):
        self.dev_table.setRowCount(len(self._devolucoes))
        for row, d in enumerate(self._devolucoes):
            self.dev_table.setItem(row, 0, QTableWidgetItem(str(d.id_devolucao)))
            self.dev_table.setItem(row, 1, QTableWidgetItem(str(d.id_venda)))
            self.dev_table.setItem(row, 2, QTableWidgetItem(str(d.cupom_fiscal)))
            self.dev_table.setItem(row, 3, QTableWidgetItem(d.cliente or ""))
            data_str = d.data_devolucao.strftime("%d/%m/%Y %H:%M") if d.data_devolucao else ""
            self.dev_table.setItem(row, 4, QTableWidgetItem(data_str))
            self.dev_table.setItem(row, 5, QTableWidgetItem(d.motivo or ""))
            self.dev_table.setItem(row, 6, QTableWidgetItem(d.tipo or ""))
        self.dev_table.resizeColumnsToContents()
        self.items_table.setRowCount(0)
        self._selected_dev = None
        self.items_title.setText("Itens Devolvidos")

    def _on_dev_selected(self):
        rows = self.dev_table.selectionModel().selectedRows()
        if not rows:
            return
        dev = self._devolucoes[rows[0].row()]
        self._selected_dev = dev
        self.items_title.setText(f"Itens — Devolução #{dev.id_devolucao}")
        try:
            self._itens = DevolucaoService.buscar_itens(dev.id_devolucao)
            self._populate_itens()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _populate_itens(self):
        self.items_table.setRowCount(len(self._itens))
        for row, it in enumerate(self._itens):
            self.items_table.setItem(row, 0, QTableWidgetItem(str(it.id_item_devolucao)))
            self.items_table.setItem(row, 1, QTableWidgetItem(it.nome_produto or ""))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(it.quantidade)))
        self.items_table.resizeColumnsToContents()

    def _on_nova_devolucao(self):
        dlg = _NovaDevolucaoDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            vals = dlg.get_values()
            if not vals["itens"]:
                QMessageBox.warning(self, "Aviso", "Selecione ao menos um item para devolver.")
                return
            try:
                msg = DevolucaoService.devolver(**vals)
                QMessageBox.information(self, "Sucesso", msg)
                self.load_data()
            except Exception as exc:
                QMessageBox.critical(self, "Erro ao Devolver", str(exc))


class _NovaDevolucaoDialog(QDialog):
    """Formulário para registro de nova devolução."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nova Devolução")
        self.setMinimumWidth(520)
        self._item_rows: list = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.cmb_venda = QComboBox()
        try:
            vendas = VendaService.listar_todos()
            for v in vendas:
                nome_cli = v.cliente.nome if v.cliente else "?"
                self.cmb_venda.addItem(
                    f"Cupom {v.cupom_fiscal} — {nome_cli}", v.id_venda
                )
        except Exception:
            pass
        self.cmb_venda.currentIndexChanged.connect(self._on_venda_changed)
        form.addRow("Venda *:", self.cmb_venda)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Reembolso", "REEMBOLSO")
        self.cmb_tipo.addItem("Troca", "TROCA")
        form.addRow("Tipo *:", self.cmb_tipo)

        self.txt_motivo = QTextEdit()
        self.txt_motivo.setMaximumHeight(60)
        self.txt_motivo.setPlaceholderText("Motivo da devolução…")
        form.addRow("Motivo *:", self.txt_motivo)

        layout.addLayout(form)

        itens_label = QLabel("Itens para Devolver")
        itens_label.setFont(QFont("", 11, QFont.Weight.Bold))
        layout.addWidget(itens_label)

        self._itens_container = QVBoxLayout()
        layout.addLayout(self._itens_container)

        self._on_venda_changed()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_venda_changed(self):
        """Carrega os itens da venda selecionada."""
        while self._itens_container.count():
            child = self._itens_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._item_rows.clear()

        id_venda = self.cmb_venda.currentData()
        if not id_venda:
            return

        try:
            itens = DevolucaoService.buscar_itens_venda(id_venda)
        except Exception:
            return

        for it in itens:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)

            cb = QCheckBox(f"{it.nome_produto} (vendido: {it.quantidade})")
            row_layout.addWidget(cb)

            spn = QSpinBox()
            spn.setRange(1, it.quantidade)
            spn.setValue(1)
            spn.setEnabled(False)
            cb.toggled.connect(spn.setEnabled)
            row_layout.addWidget(spn)

            self._item_rows.append((cb, spn, it.id_produto))
            self._itens_container.addWidget(row_widget)

    def _validate_and_accept(self):
        if not self.txt_motivo.toPlainText().strip():
            QMessageBox.warning(self, "Campo Obrigatório", "Informe o motivo da devolução.")
            return
        selected = [r for r in self._item_rows if r[0].isChecked()]
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione ao menos um item para devolver.")
            return
        self.accept()

    def get_values(self) -> dict:
        itens = []
        for cb, spn, id_produto in self._item_rows:
            if cb.isChecked():
                itens.append({
                    "id_produto": id_produto,
                    "quantidade": spn.value(),
                })
        return {
            "id_venda": self.cmb_venda.currentData(),
            "itens": itens,
            "motivo": self.txt_motivo.toPlainText().strip(),
            "tipo": self.cmb_tipo.currentData(),
        }
