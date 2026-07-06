"""Janela principal do sistema — barra lateral de navegação + páginas."""

import os

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont, QMovie
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# Caminho do GIF exibido no topo da barra lateral (raiz do projeto / assets).
GIF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "assets", "farmacia_gif.gif"
)

from ui.pages.cliente_page import ClientePage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.estoque_page import EstoquePage
from ui.pages.filial_page import FilialPage
from ui.pages.fornecedor_page import FornecedorPage
from ui.pages.produto_page import ProdutoPage
from ui.pages.devolucao_page import DevolucaoPage
from ui.pages.recebido_page import RecebidoPage
from ui.pages.reposicao_page import ReposicaoPage
from ui.pages.venda_page import VendaPage
from ui.pages.vendedor_page import VendedorPage


class MainWindow(QMainWindow):
    """Janela raiz com sidebar de navegação e QStackedWidget de páginas."""

    _PAGES = [
        ("📊  Dashboard", DashboardPage),
        ("👤  Clientes", ClientePage),
        ("📦  Produtos", ProdutoPage),
        ("🏷️  Vendedores", VendedorPage),
        ("🏢  Fornecedores", FornecedorPage),
        ("🏪  Filiais", FilialPage),
        ("🛒  Vendas", VendaPage),
        ("📥  Estoque", EstoquePage),
        ("📋  Reposição", ReposicaoPage),
        ("📦  Recebidos", RecebidoPage),
        ("🔄  Devoluções", DevolucaoPage),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gerência de Farmácia")
        self.setMinimumSize(1100, 650)
        self._setup_ui()
        self._check_connection()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────
        # Painel lateral: GIF no topo + lista de navegação embaixo.
        side_panel = QWidget()
        side_panel.setFixedWidth(200)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)

        # GIF acima da seção "Dashboard"
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._movie = QMovie(GIF_PATH)
        if self._movie.isValid():
            self._movie.setScaledSize(QSize(180, 150))
            self.gif_label.setMovie(self._movie)
            self._movie.start()
            side_layout.addWidget(self.gif_label)

        self.sidebar = QListWidget()
        self.sidebar.setFont(QFont("", 11))
        self.sidebar.setSpacing(2)

        for label, _cls in self._PAGES:
            item = QListWidgetItem(label)
            item.setSizeHint(QSize(0, 40))
            self.sidebar.addItem(item)

        self.sidebar.currentRowChanged.connect(self._on_page_changed)
        side_layout.addWidget(self.sidebar)

        main_layout.addWidget(side_panel)

        # ── Stack de páginas ─────────────────────────────────────────────
        self.stack = QStackedWidget()
        for _label, page_cls in self._PAGES:
            self.stack.addWidget(page_cls())
        main_layout.addWidget(self.stack)

        # Seleciona Dashboard por padrão
        self.sidebar.setCurrentRow(0)

    def _on_page_changed(self, index: int):
        self.stack.setCurrentIndex(index)
        page = self.stack.currentWidget()
        if hasattr(page, "load_data"):
            page.load_data()

    def _check_connection(self):
        from database import test_connection

        if test_connection():
            self.statusBar().showMessage("✓ Conectado ao MongoDB")
        else:
            self.statusBar().showMessage("✗ Falha na conexão com o MongoDB")
