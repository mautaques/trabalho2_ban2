"""Página CRUD genérica reutilizável.

Subclasses só precisam chamar ``init_page(...)`` no ``__init__`` informando
título, colunas da tabela, campos do formulário, serviço e chave primária.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
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

from ui.widgets.form_dialog import FormDialog


class CrudPage(QWidget):
    """Widget base para páginas de listagem + CRUD de uma entidade."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list = []

    def init_page(self, *, title: str, columns: list[dict], form_fields: list[dict],
                  service, id_key: str):
        """Configura e monta a página.

        Args:
            title: Título exibido no topo.
            columns: ``[{"key": "nome_coluna", "label": "Rótulo"}, ...]``
            form_fields: Definições para o FormDialog.
            service: Classe de serviço com métodos estáticos
                     ``listar_todos``, ``buscar``, ``criar``, ``atualizar``, ``excluir``.
            id_key: Nome do atributo da chave primária (ex.: ``"id_cliente"``).
        """
        self._title = title
        self._columns = columns
        self._form_fields = form_fields
        self._service = service
        self._id_key = id_key
        self._setup_ui()
        self.load_data()

    # ── UI ───────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Título
        lbl = QLabel(self._title)
        lbl.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(lbl)

        # Barra de ferramentas
        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input, stretch=1)

        for text, slot in [
            ("Novo", self._on_novo),
            ("Editar", self._on_editar),
            ("Excluir", self._on_excluir),
            ("Atualizar", self.load_data),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            toolbar.addWidget(btn)

        layout.addLayout(toolbar)

        # Tabela
        self.table = QTableWidget()
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setAlternatingRowColors(True)
        self.table.setColumnCount(len(self._columns))
        self.table.setHorizontalHeaderLabels(
            [c["label"] for c in self._columns]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(lambda _: self._on_editar())
        layout.addWidget(self.table)

    # ── Dados ────────────────────────────────────────────────────────────

    def load_data(self):
        """Recarrega a tabela com todos os registros."""
        try:
            self._populate(self._service.listar_todos())
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _on_search(self, text: str):
        try:
            if text.strip():
                self._populate(self._service.buscar(text))
            else:
                self._populate(self._service.listar_todos())
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _populate(self, items: list):
        self._data = items
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            for col, col_def in enumerate(self._columns):
                value = getattr(item, col_def["key"], "")
                cell = QTableWidgetItem(str(value) if value is not None else "")
                cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, cell)
        self.table.resizeColumnsToContents()

    # ── CRUD ─────────────────────────────────────────────────────────────

    def _get_selected(self):
        """Retorna o item selecionado ou exibe aviso."""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Aviso", "Selecione um registro.")
            return None
        return self._data[rows[0].row()]

    def _on_novo(self):
        dlg = FormDialog(f"Novo — {self._title}", self._form_fields, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._service.criar(**dlg.get_values())
                self.load_data()
            except Exception as exc:
                QMessageBox.critical(self, "Erro ao Criar", str(exc))

    def _on_editar(self):
        item = self._get_selected()
        if item is None:
            return
        initial = {
            f["name"]: getattr(item, f["name"], None) for f in self._form_fields
        }
        dlg = FormDialog(
            f"Editar — {self._title}", self._form_fields,
            initial_values=initial, parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._service.atualizar(getattr(item, self._id_key), **dlg.get_values())
                self.load_data()
            except Exception as exc:
                QMessageBox.critical(self, "Erro ao Editar", str(exc))

    def _on_excluir(self):
        item = self._get_selected()
        if item is None:
            return
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            "Deseja realmente excluir este registro?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._service.excluir(getattr(item, self._id_key))
                self.load_data()
            except Exception as exc:
                QMessageBox.critical(self, "Erro ao Excluir", str(exc))
