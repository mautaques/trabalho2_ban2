"""Página de Vendas — master-detail (Venda ↔ Itens da Venda)."""

import datetime

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
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
    QVBoxLayout,
    QWidget,
)

from services.cliente_service import ClienteService
from services.filial_service import FilialService
from services.produto_service import ProdutoService
from services.venda_service import VendaService
from services.vendedor_service import VendedorService


class VendaPage(QWidget):
    """Painel master-detail: lista de vendas + itens da venda selecionada."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vendas: list = []
        self._itens: list = []
        self._selected_venda = None
        self._setup_ui()
        self.load_data()

    # ── UI ───────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Vendas")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Barra de ferramentas
        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por cupom fiscal ou cliente…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input, stretch=1)

        for text, slot in [
            ("Nova Venda", self._on_nova_venda),
            ("Excluir Venda", self._on_excluir_venda),
            ("Atualizar", self.load_data),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            toolbar.addWidget(btn)

        layout.addLayout(toolbar)

        # Splitter vertical: vendas em cima, itens embaixo
        splitter = QSplitter(Qt.Orientation.Vertical)

        # ── Tabela de Vendas ─────────────────────────────────────────────
        self.vendas_table = self._make_table(
            ["ID", "Cupom Fiscal", "Filial", "Vendedor", "Cliente",
             "Data/Hora", "Forma Pgto", "Valor Total (R$)"]
        )
        self.vendas_table.selectionModel().selectionChanged.connect(
            self._on_venda_selected
        )
        splitter.addWidget(self.vendas_table)

        # ── Painel de Itens ──────────────────────────────────────────────
        items_panel = QWidget()
        items_layout = QVBoxLayout(items_panel)
        items_layout.setContentsMargins(0, 8, 0, 0)

        self.items_title = QLabel("Itens da Venda")
        self.items_title.setFont(QFont("", 12, QFont.Weight.Bold))
        items_layout.addWidget(self.items_title)

        self.items_table = self._make_table(
            ["ID", "Produto", "Quantidade", "Preço Unit. (R$)",
             "Desconto", "Valor Total (R$)"]
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

    # ── Dados ────────────────────────────────────────────────────────────

    def load_data(self):
        """Carrega todas as vendas na tabela."""
        try:
            self._vendas = VendaService.listar_todos()
            self._populate_vendas()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _on_search(self, text: str):
        try:
            if text.strip():
                self._vendas = VendaService.buscar(text)
            else:
                self._vendas = VendaService.listar_todos()
            self._populate_vendas()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _populate_vendas(self):
        self.vendas_table.setRowCount(len(self._vendas))
        for row, v in enumerate(self._vendas):
            self.vendas_table.setItem(row, 0, QTableWidgetItem(str(v.id_venda)))
            self.vendas_table.setItem(row, 1, QTableWidgetItem(str(v.cupom_fiscal)))
            self.vendas_table.setItem(
                row, 2,
                QTableWidgetItem(v.filial.nome_fantasia if v.filial else ""),
            )
            self.vendas_table.setItem(
                row, 3,
                QTableWidgetItem(v.vendedor.nome if v.vendedor else ""),
            )
            self.vendas_table.setItem(
                row, 4,
                QTableWidgetItem(v.cliente.nome if v.cliente else ""),
            )
            data_str = v.data_hora.strftime("%d/%m/%Y %H:%M") if v.data_hora else ""
            self.vendas_table.setItem(row, 5, QTableWidgetItem(data_str))
            self.vendas_table.setItem(
                row, 6, QTableWidgetItem(v.forma_pagamento or "")
            )
            valor = f"{v.valor_total:.2f}" if v.valor_total else "0.00"
            self.vendas_table.setItem(row, 7, QTableWidgetItem(valor))
        self.vendas_table.resizeColumnsToContents()
        self.items_table.setRowCount(0)
        self._selected_venda = None
        self.items_title.setText("Itens da Venda")

    def _on_venda_selected(self):
        rows = self.vendas_table.selectionModel().selectedRows()
        if not rows:
            return
        venda = self._vendas[rows[0].row()]
        self._selected_venda = venda
        self.items_title.setText(f"Itens da Venda #{venda.cupom_fiscal}")
        try:
            self._itens = VendaService.buscar_itens(venda.id_venda)
            self._populate_itens()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _populate_itens(self):
        self.items_table.setRowCount(len(self._itens))
        for row, it in enumerate(self._itens):
            self.items_table.setItem(
                row, 0, QTableWidgetItem(str(it.id_item_venda))
            )
            nome_prod = it.produto.nome_produto if it.produto else str(it.id_produto)
            self.items_table.setItem(row, 1, QTableWidgetItem(nome_prod))
            self.items_table.setItem(
                row, 2, QTableWidgetItem(str(it.quantidade))
            )
            self.items_table.setItem(
                row, 3, QTableWidgetItem(f"{it.preco_unitario:.2f}")
            )
            desc = f"{float(it.desconto) * 100:.0f}%" if it.desconto else "—"
            self.items_table.setItem(row, 4, QTableWidgetItem(desc))
            vtotal = f"{it.valor_total:.2f}" if it.valor_total else "—"
            self.items_table.setItem(row, 5, QTableWidgetItem(vtotal))
        self.items_table.resizeColumnsToContents()

    # ── CRUD Venda ───────────────────────────────────────────────────────

    def _on_nova_venda(self):
        dlg = _NovaVendaDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            vals = dlg.get_values()
            try:
                msg = VendaService.inserir_pedido(**vals)
                self.load_data()
                if msg:
                    QMessageBox.information(self, "Sucesso", msg)
            except Exception as exc:
                QMessageBox.critical(self, "Erro ao Criar Venda", str(exc))

    def _on_excluir_venda(self):
        if not self._selected_venda:
            QMessageBox.warning(self, "Aviso", "Selecione uma venda.")
            return
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Excluir venda #{self._selected_venda.cupom_fiscal} e todos seus itens?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                VendaService.excluir(self._selected_venda.id_venda)
                self.load_data()
            except Exception as exc:
                QMessageBox.critical(self, "Erro ao Excluir", str(exc))


# ── Diálogos auxiliares ──────────────────────────────────────────────────


class _NovaVendaDialog(QDialog):
    """Formulário para criação de uma nova venda, com itens (produtos)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nova Venda")
        self.setMinimumWidth(620)
        self._itens_widgets: list = []

        # Produtos carregados uma vez; preço sugerido = preço de venda.
        try:
            self._produtos = ProdutoService.listar_todos()
        except Exception:
            self._produtos = []
        self._preco_por_produto = {
            p.id_produto: float(p.preco_venda or 0) for p in self._produtos
        }

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Filial
        self.cmb_filial = QComboBox()
        try:
            for f in FilialService.listar_todos():
                self.cmb_filial.addItem(
                    f"{f.codigo_filial} — {f.nome_fantasia}", f.id_filial
                )
        except Exception:
            pass
        form.addRow("Filial *:", self.cmb_filial)

        # Vendedor — só os da filial selecionada (cada vendedor é de uma filial).
        self.cmb_vendedor = QComboBox()
        form.addRow("Vendedor *:", self.cmb_vendedor)
        self.cmb_filial.currentIndexChanged.connect(self._atualiza_vendedores)
        self._atualiza_vendedores()

        # Cliente (opcional)
        self.cmb_cliente = QComboBox()
        self.cmb_cliente.addItem("— Sem cliente —", None)
        try:
            for c in ClienteService.listar_todos():
                self.cmb_cliente.addItem(f"{c.nome} ({c.cpf})", c.id_cliente)
        except Exception:
            pass
        form.addRow("Cliente:", self.cmb_cliente)

        # Cupom fiscal — gerado automaticamente (aleatório) pelo sistema.
        lbl_cupom = QLabel("Gerado automaticamente ao salvar.")
        lbl_cupom.setStyleSheet("color: gray;")
        form.addRow("Cupom Fiscal:", lbl_cupom)

        # Data da venda — calendário; não permite data futura (máximo: hoje).
        self.dt_venda = QDateEdit()
        self.dt_venda.setCalendarPopup(True)
        self.dt_venda.setDisplayFormat("dd/MM/yyyy")
        self.dt_venda.setDate(QDate.currentDate())
        self.dt_venda.setMaximumDate(QDate.currentDate())
        form.addRow("Data da Venda *:", self.dt_venda)

        # Forma de pagamento
        self.cmb_pgto = QComboBox()
        for val, label in [
            ("Pix", "Pix"),
            ("Cartão de Crédito", "Cartão de Crédito"),
            ("Cartão de Débito", "Cartão de Débito"),
        ]:
            self.cmb_pgto.addItem(label, val)
        form.addRow("Forma de Pagamento:", self.cmb_pgto)

        layout.addLayout(form)

        # ── Itens da venda ───────────────────────────────────────────────
        itens_label = QLabel("Itens da Venda")
        itens_label.setFont(QFont("", 11, QFont.Weight.Bold))
        layout.addWidget(itens_label)

        self.lbl_total = QLabel()
        self.lbl_total.setFont(QFont("", 11, QFont.Weight.Bold))

        self._itens_container = QVBoxLayout()
        layout.addLayout(self._itens_container)
        self._add_item_row()

        btn_add = QPushButton("+ Adicionar Item")
        btn_add.clicked.connect(self._add_item_row)
        layout.addWidget(btn_add)

        layout.addWidget(self.lbl_total)

        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _atualiza_vendedores(self):
        """Recarrega o combo de vendedores conforme a filial selecionada."""
        self.cmb_vendedor.clear()
        id_filial = self.cmb_filial.currentData()
        if id_filial is None:
            return
        try:
            for v in VendedorService.listar_por_filial(id_filial):
                self.cmb_vendedor.addItem(
                    f"{v.matricula} — {v.nome}", v.id_vendedor
                )
        except Exception:
            pass

    def _add_item_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        cmb_produto = QComboBox()
        cmb_produto.setMinimumWidth(180)
        for p in self._produtos:
            cmb_produto.addItem(p.nome_produto, p.id_produto)
        row_layout.addWidget(cmb_produto)

        spn_qtd = QSpinBox()
        spn_qtd.setRange(1, 9999)
        spn_qtd.setValue(1)
        spn_qtd.setPrefix("Qtd: ")
        spn_qtd.valueChanged.connect(self._atualiza_total)
        row_layout.addWidget(spn_qtd)

        spn_preco = QDoubleSpinBox()
        spn_preco.setRange(0.01, 99999.99)
        spn_preco.setDecimals(2)
        spn_preco.setPrefix("R$ ")
        spn_preco.valueChanged.connect(self._atualiza_total)
        row_layout.addWidget(spn_preco)

        spn_desc = QDoubleSpinBox()
        spn_desc.setRange(0.0, 1.0)
        spn_desc.setDecimals(2)
        spn_desc.setSingleStep(0.05)
        spn_desc.setPrefix("Desc: ")
        spn_desc.setToolTip("Desconto em fração: 0.10 = 10%")
        spn_desc.valueChanged.connect(self._atualiza_total)
        row_layout.addWidget(spn_desc)

        # Ao trocar o produto, preenche o preço com o preço de venda.
        cmb_produto.currentIndexChanged.connect(
            lambda _i, c=cmb_produto, p=spn_preco: self._preencher_preco(c, p)
        )

        self._itens_widgets.append((cmb_produto, spn_qtd, spn_preco, spn_desc))
        self._itens_container.addWidget(row_widget)

        self._preencher_preco(cmb_produto, spn_preco)
        self._atualiza_total()

    def _preencher_preco(self, cmb_produto, spn_preco):
        """Preenche o preço unitário com o preço de venda do produto."""
        preco = self._preco_por_produto.get(cmb_produto.currentData(), 0)
        spn_preco.setValue(preco if preco > 0 else spn_preco.minimum())

    def _atualiza_total(self):
        """Soma quantidade × preço × (1 - desconto) de todos os itens."""
        total = sum(
            spn_qtd.value() * spn_preco.value() * (1 - spn_desc.value())
            for _cmb, spn_qtd, spn_preco, spn_desc in self._itens_widgets
        )
        self.lbl_total.setText(f"Total da Venda: R$ {total:.2f}")

    def get_values(self) -> dict:
        qd = self.dt_venda.date()
        # Combina a data escolhida com a hora atual para um timestamp realista.
        data_hora = datetime.datetime.combine(
            datetime.date(qd.year(), qd.month(), qd.day()),
            datetime.datetime.now().time(),
        )
        itens = []
        for cmb, spn_qtd, spn_preco, spn_desc in self._itens_widgets:
            if cmb.currentData() is None:
                continue
            itens.append({
                "id_produto": cmb.currentData(),
                "quantidade": spn_qtd.value(),
                "preco_unitario": spn_preco.value(),
                "desconto": spn_desc.value(),
            })
        return {
            "id_filial": self.cmb_filial.currentData(),
            "id_vendedor": self.cmb_vendedor.currentData(),
            "id_cliente": self.cmb_cliente.currentData(),
            "forma_pagamento": self.cmb_pgto.currentData(),
            "itens": itens,
            "data_hora": data_hora,
        }
