"""Página de Reposição de Estoque — master-detail (Pedidos ↔ Itens)."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QComboBox,
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services.filial_service import FilialService
from services.fornecedor_service import FornecedorService
from services.produto_service import ProdutoService
from services.reposicao_service import ReposicaoService


class ReposicaoPage(QWidget):
    """Painel master-detail: lista de pedidos de reposição + itens."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._reposicoes: list = []
        self._itens: list = []
        self._selected_rep = None
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Reposição de Estoque")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nº pedido ou fornecedor…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input, stretch=1)

        for text, slot in [
            ("Novo Pedido", self._on_novo_pedido),
            ("Aprovar", self._on_aprovar),
            ("Enviar", self._on_enviar),
            ("Receber Pedido", self._on_receber),
            ("Cancelar", self._on_cancelar),
            ("Atualizar", self.load_data),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            toolbar.addWidget(btn)

        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.rep_table = self._make_table(
            ["ID", "Nº Pedido", "Fornecedor", "Filial Destino",
             "Data Pedido", "Status", "Valor Total (R$)"]
        )
        self.rep_table.selectionModel().selectionChanged.connect(
            self._on_rep_selected
        )
        splitter.addWidget(self.rep_table)

        items_panel = QWidget()
        items_layout = QVBoxLayout(items_panel)
        items_layout.setContentsMargins(0, 8, 0, 0)

        self.items_title = QLabel("Itens do Pedido")
        self.items_title.setFont(QFont("", 12, QFont.Weight.Bold))
        items_layout.addWidget(self.items_title)

        self.items_table = self._make_table(
            ["ID", "Produto", "Lote", "Quantidade",
             "Valor Unit. (R$)", "Valor Total (R$)"]
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
        """Carrega todos os pedidos de reposição."""
        try:
            self._reposicoes = ReposicaoService.listar_todos()
            self._populate_reposicoes()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _on_search(self, text: str):
        try:
            if text.strip():
                self._reposicoes = ReposicaoService.buscar(text)
            else:
                self._reposicoes = ReposicaoService.listar_todos()
            self._populate_reposicoes()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _populate_reposicoes(self):
        self.rep_table.setRowCount(len(self._reposicoes))
        for row, r in enumerate(self._reposicoes):
            self.rep_table.setItem(row, 0, QTableWidgetItem(str(r.id_reposicao)))
            self.rep_table.setItem(row, 1, QTableWidgetItem(str(r.numero_pedido)))
            self.rep_table.setItem(row, 2, QTableWidgetItem(r.fornecedor or ""))
            self.rep_table.setItem(row, 3, QTableWidgetItem(r.filial or ""))
            data_str = r.data_pedido.strftime("%d/%m/%Y %H:%M") if r.data_pedido else ""
            self.rep_table.setItem(row, 4, QTableWidgetItem(data_str))
            self.rep_table.setItem(row, 5, QTableWidgetItem(r.status or ""))
            valor = f"{r.valor_total:.2f}" if r.valor_total else "0.00"
            self.rep_table.setItem(row, 6, QTableWidgetItem(valor))
        self.rep_table.resizeColumnsToContents()
        self.items_table.setRowCount(0)
        self._selected_rep = None
        self.items_title.setText("Itens do Pedido")

    def _on_rep_selected(self):
        rows = self.rep_table.selectionModel().selectedRows()
        if not rows:
            return
        rep = self._reposicoes[rows[0].row()]
        self._selected_rep = rep
        self.items_title.setText(f"Itens do Pedido #{rep.numero_pedido}")
        try:
            self._itens = ReposicaoService.buscar_itens(rep.id_reposicao)
            self._populate_itens()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _populate_itens(self):
        self.items_table.setRowCount(len(self._itens))
        for row, it in enumerate(self._itens):
            self.items_table.setItem(row, 0, QTableWidgetItem(str(it.id_item_reposicao)))
            self.items_table.setItem(row, 1, QTableWidgetItem(it.nome_produto or ""))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(it.numero_lote)))
            self.items_table.setItem(row, 3, QTableWidgetItem(str(it.quantidade)))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{it.valor_unitario:.2f}"))
            vtotal = f"{it.valor_total:.2f}" if it.valor_total else "—"
            self.items_table.setItem(row, 5, QTableWidgetItem(vtotal))
        self.items_table.resizeColumnsToContents()

    def _on_novo_pedido(self):
        dlg = _NovoPedidoReposicaoDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            vals = dlg.get_values()
            try:
                msg = ReposicaoService.insere_pedido(**vals)
                QMessageBox.information(self, "Sucesso", msg)
                self.load_data()
            except Exception as exc:
                QMessageBox.critical(self, "Erro ao Criar Pedido", str(exc))

    def _on_receber(self):
        if not self._selected_rep:
            QMessageBox.warning(self, "Aviso", "Selecione um pedido.")
            return
        if self._selected_rep.status == "RECEBIDO":
            QMessageBox.warning(self, "Aviso", "Este pedido já foi recebido.")
            return
        dlg = _ReceberReposicaoDialog(self._selected_rep, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            vals = dlg.get_values()
            try:
                msg = ReposicaoService.receber(**vals)
                QMessageBox.information(self, "Sucesso", msg)
                self.load_data()
            except Exception as exc:
                QMessageBox.critical(self, "Erro ao Receber", str(exc))

    def _on_aprovar(self):
        self._mudar_status(ReposicaoService.aprovar, "aprovar")

    def _on_enviar(self):
        self._mudar_status(ReposicaoService.enviar, "enviar")

    def _on_cancelar(self):
        self._mudar_status(ReposicaoService.cancelar, "cancelar")

    def _mudar_status(self, acao_service, verbo: str):
        """Confirma e aplica uma transição de status no pedido selecionado."""
        if not self._selected_rep:
            QMessageBox.warning(self, "Aviso", "Selecione um pedido.")
            return
        reply = QMessageBox.question(
            self, "Confirmar",
            f"Deseja {verbo} o pedido #{self._selected_rep.numero_pedido}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            msg = acao_service(self._selected_rep.id_reposicao)
            QMessageBox.information(self, "Sucesso", msg)
            self.load_data()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))


class _NovoPedidoReposicaoDialog(QDialog):
    """Formulário para criação de novo pedido de reposição."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Pedido de Reposição")
        self.setMinimumWidth(520)
        self._itens_widgets: list = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.cmb_fornecedor = QComboBox()
        try:
            for f in FornecedorService.listar_todos():
                self.cmb_fornecedor.addItem(f.nome_fantasia, f.id_fornecedor)
        except Exception:
            pass
        form.addRow("Fornecedor *:", self.cmb_fornecedor)

        self.cmb_filial = QComboBox()
        try:
            for f in FilialService.listar_todos():
                self.cmb_filial.addItem(
                    f"{f.codigo_filial} — {f.nome_fantasia}", f.id_filial
                )
        except Exception:
            pass
        form.addRow("Filial Destino *:", self.cmb_filial)

        layout.addLayout(form)

        # Carrega os produtos uma única vez; o valor unitário de cada item é
        # preenchido automaticamente a partir do preço de custo do produto.
        try:
            self._produtos = ProdutoService.listar_todos()
        except Exception:
            self._produtos = []
        self._preco_por_produto = {
            p.id_produto: float(p.preco_custo or 0) for p in self._produtos
        }

        itens_label = QLabel("Itens do Pedido")
        itens_label.setFont(QFont("", 11, QFont.Weight.Bold))
        layout.addWidget(itens_label)

        # Criado antes da primeira linha de item, pois _add_item_row já o atualiza.
        self.lbl_total = QLabel()
        self.lbl_total.setFont(QFont("", 11, QFont.Weight.Bold))

        self._itens_container = QVBoxLayout()
        layout.addLayout(self._itens_container)
        self._add_item_row()

        btn_add = QPushButton("+ Adicionar Item")
        btn_add.clicked.connect(self._add_item_row)
        layout.addWidget(btn_add)

        layout.addWidget(self.lbl_total)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

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
        spn_qtd.setRange(1, 99999)
        spn_qtd.setValue(1)
        spn_qtd.setPrefix("Qtd: ")
        row_layout.addWidget(spn_qtd)

        # Caixa de valor: somente leitura, mostra o subtotal da linha
        # (quantidade × preço de custo). Não é editável manualmente.
        spn_valor = QDoubleSpinBox()
        spn_valor.setRange(0.00, 999_999_999.99)
        spn_valor.setDecimals(2)
        spn_valor.setPrefix("R$ ")
        spn_valor.setReadOnly(True)
        spn_valor.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        spn_valor.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        spn_valor.setToolTip("Subtotal = quantidade × preço de custo")
        row_layout.addWidget(spn_valor)

        # Recalcula o subtotal da linha ao mudar a quantidade ou o produto.
        spn_qtd.valueChanged.connect(
            lambda _v, c=cmb_produto, q=spn_qtd, s=spn_valor: self._atualiza_linha(c, q, s)
        )
        cmb_produto.currentIndexChanged.connect(
            lambda _i, c=cmb_produto, q=spn_qtd, s=spn_valor: self._atualiza_linha(c, q, s)
        )

        self._itens_widgets.append((cmb_produto, spn_qtd, spn_valor))
        self._itens_container.addWidget(row_widget)

        # Calcula o subtotal do produto inicialmente selecionado.
        self._atualiza_linha(cmb_produto, spn_qtd, spn_valor)

    def _atualiza_linha(self, cmb_produto, spn_qtd, spn_valor):
        """Atualiza o subtotal da linha (quantidade × preço de custo) e o total."""
        unitario = self._preco_por_produto.get(cmb_produto.currentData(), 0)
        spn_valor.setValue(unitario * spn_qtd.value())
        self._atualiza_total()

    def _atualiza_total(self):
        """Soma os subtotais de todos os itens e exibe o total do pedido."""
        total = sum(spn_valor.value() for _cmb, _qtd, spn_valor in self._itens_widgets)
        self.lbl_total.setText(f"Total do Pedido: R$ {total:.2f}")

    def get_values(self) -> dict:
        itens = []
        for cmb, spn_qtd, _spn_valor in self._itens_widgets:
            # valor_unitario é o preço de custo do produto; a caixa exibe o
            # subtotal (quantidade × preço), por isso não é usada aqui.
            id_produto = cmb.currentData()
            itens.append({
                "id_produto": id_produto,
                "quantidade": spn_qtd.value(),
                "valor_unitario": self._preco_por_produto.get(id_produto, 0),
            })
        return {
            "id_fornecedor": self.cmb_fornecedor.currentData(),
            "id_filial_destino": self.cmb_filial.currentData(),
            "itens": itens,
        }


class _ReceberReposicaoDialog(QDialog):
    """Formulário para registrar recebimento de reposição."""

    def __init__(self, reposicao, parent=None):
        super().__init__(parent)
        self._reposicao = reposicao
        self.setWindowTitle(f"Receber Pedido #{reposicao.numero_pedido}")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)

        info = QLabel(
            "Todos os itens do pedido entrarão no estoque com as quantidades "
            "pedidas."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray;")
        layout.addRow(info)

        self.txt_divergencia = QTextEdit()
        self.txt_divergencia.setMaximumHeight(80)
        self.txt_divergencia.setPlaceholderText(
            "Ex: 5 unidades com embalagem danificada"
        )
        layout.addRow("Divergência:", self.txt_divergencia)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_values(self) -> dict:
        div = self.txt_divergencia.toPlainText().strip()
        return {
            "id_reposicao": self._reposicao.id_reposicao,
            "divergencia": div if div else None,
        }
