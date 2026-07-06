import os
import sys

from PyQt6.QtWidgets import QApplication

# Garante que o diretório do projeto esteja no sys.path
cur_path = os.path.realpath(__file__)
base_path = os.path.dirname(cur_path)
if base_path not in sys.path:
    sys.path.insert(0, base_path)

app = QApplication(sys.argv)
app.setApplicationName("Sistema de Gerência de Farmácia")

from ui.main_window import MainWindow  # noqa: E402

window = MainWindow()
window.show()

sys.exit(app.exec())