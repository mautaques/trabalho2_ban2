"""Diálogo de formulário genérico para inserção/edição de registros.

Gera campos automaticamente a partir de uma lista de definições:
    fields = [
        {"name": "nome",  "label": "Nome",  "type": "text",  "required": True},
        {"name": "cpf",   "label": "CPF",   "type": "text",  "required": True, "max_length": 12},
        {"name": "data",  "label": "Data",  "type": "date"},
        {"name": "valor", "label": "Valor", "type": "float", "decimals": 2},
        {"name": "cat",   "label": "Cat.",  "type": "combobox", "options": [("A","Op A"), ...]},
        {"name": "obs",   "label": "Obs.",  "type": "textarea"},
    ]
"""

import datetime

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QWidget,
)


class FormDialog(QDialog):
    """Diálogo genérico que constrói um formulário a partir de *fields*."""

    def __init__(self, title: str, fields: list, initial_values: dict | None = None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self._fields = fields
        self._widgets: dict[str, QWidget] = {}
        self._initial = initial_values or {}
        self._setup_ui()

    # ── Construção do formulário ─────────────────────────────────────────

    def _setup_ui(self):
        layout = QFormLayout(self)

        for field in self._fields:
            name = field["name"]
            label = field.get("label", name)
            required = field.get("required", False)
            ftype = field.get("type", "text")

            widget = self._create_widget(field)
            self._widgets[name] = widget

            if name in self._initial and self._initial[name] is not None:
                self._set_value(widget, ftype, self._initial[name])

            display_label = f"{label} *:" if required else f"{label}:"
            layout.addRow(display_label, widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _create_widget(self, field: dict) -> QWidget:
        ftype = field.get("type", "text")

        if ftype == "text":
            w = QLineEdit()
            if "max_length" in field:
                w.setMaxLength(field["max_length"])
            if "placeholder" in field:
                w.setPlaceholderText(field["placeholder"])
            return w

        if ftype == "integer":
            w = QSpinBox()
            w.setRange(field.get("min", 0), field.get("max", 999_999_999))
            return w

        if ftype == "float":
            w = QDoubleSpinBox()
            w.setRange(field.get("min", 0.0), field.get("max", 9_999_999.99))
            w.setDecimals(field.get("decimals", 2))
            return w

        if ftype == "date":
            # Para campos opcionais: checkbox + QDateEdit
            # Para campos obrigatórios: apenas QDateEdit
            container = QWidget()
            h = QHBoxLayout(container)
            h.setContentsMargins(0, 0, 0, 0)

            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("dd/MM/yyyy")
            date_edit.setDate(QDate.currentDate())

            if not field.get("required", False):
                cb = QCheckBox("Informar")
                has_initial = (
                    field["name"] in self._initial
                    and self._initial[field["name"]] is not None
                )
                cb.setChecked(has_initial)
                date_edit.setEnabled(has_initial)
                cb.toggled.connect(date_edit.setEnabled)
                h.addWidget(cb)
                container._checkbox = cb  # type: ignore[attr-defined]

            h.addWidget(date_edit)
            container._date_edit = date_edit  # type: ignore[attr-defined]
            return container

        if ftype == "combobox":
            w = QComboBox()
            for value, label in field.get("options", []):
                w.addItem(label, value)
            return w

        if ftype == "textarea":
            w = QTextEdit()
            w.setMaximumHeight(100)
            return w

        # Fallback
        return QLineEdit()

    # ── Get / Set de valores ─────────────────────────────────────────────

    def _set_value(self, widget: QWidget, ftype: str, value):
        if ftype == "text":
            widget.setText(str(value))  # type: ignore[union-attr]
        elif ftype == "integer":
            widget.setValue(int(value))  # type: ignore[union-attr]
        elif ftype == "float":
            widget.setValue(float(value))  # type: ignore[union-attr]
        elif ftype == "date":
            de = widget._date_edit  # type: ignore[attr-defined]
            if isinstance(value, (datetime.date, datetime.datetime)):
                de.setDate(QDate(value.year, value.month, value.day))
            if hasattr(widget, "_checkbox"):
                widget._checkbox.setChecked(True)  # type: ignore[attr-defined]
                de.setEnabled(True)
        elif ftype == "combobox":
            idx = widget.findData(value)  # type: ignore[union-attr]
            if idx >= 0:
                widget.setCurrentIndex(idx)  # type: ignore[union-attr]
        elif ftype == "textarea":
            widget.setPlainText(str(value))  # type: ignore[union-attr]

    def get_values(self) -> dict:
        """Retorna dicionário {campo: valor} com os dados preenchidos."""
        values: dict = {}
        for field in self._fields:
            name = field["name"]
            widget = self._widgets[name]
            ftype = field.get("type", "text")

            if ftype == "text":
                v = widget.text().strip()  # type: ignore[union-attr]
                values[name] = v if v else None
            elif ftype == "integer":
                values[name] = widget.value()  # type: ignore[union-attr]
            elif ftype == "float":
                values[name] = widget.value()  # type: ignore[union-attr]
            elif ftype == "date":
                if hasattr(widget, "_checkbox") and not widget._checkbox.isChecked():  # type: ignore[attr-defined]
                    values[name] = None
                else:
                    qd = widget._date_edit.date()  # type: ignore[attr-defined]
                    values[name] = datetime.date(qd.year(), qd.month(), qd.day())
            elif ftype == "combobox":
                values[name] = widget.currentData()  # type: ignore[union-attr]
            elif ftype == "textarea":
                v = widget.toPlainText().strip()  # type: ignore[union-attr]
                values[name] = v if v else None
        return values

    # ── Validação ────────────────────────────────────────────────────────

    def _validate_and_accept(self):
        for field in self._fields:
            if not field.get("required", False):
                continue
            name = field["name"]
            label = field.get("label", name)
            widget = self._widgets[name]
            ftype = field.get("type", "text")

            if ftype == "text":
                if not widget.text().strip():  # type: ignore[union-attr]
                    QMessageBox.warning(
                        self, "Campo Obrigatório",
                        f"O campo '{label}' é obrigatório.",
                    )
                    widget.setFocus()  # type: ignore[union-attr]
                    return
            elif ftype == "textarea":
                if not widget.toPlainText().strip():  # type: ignore[union-attr]
                    QMessageBox.warning(
                        self, "Campo Obrigatório",
                        f"O campo '{label}' é obrigatório.",
                    )
                    widget.setFocus()  # type: ignore[union-attr]
                    return

        self.accept()
