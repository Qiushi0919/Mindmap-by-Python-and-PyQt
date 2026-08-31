#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Qt UI for generating a concept map with OrcaRouter."""

from PyQt5.QtCore import QThread, QUrl, pyqtSignal
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from AIProvider import DEFAULT_MODEL, ORCAROUTER_BASE_URL, OrcaRouterClient


class AIGenerationThread(QThread):
    generated = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, values, parent=None):
        super().__init__(parent)
        self.values = values

    def run(self):
        try:
            client = OrcaRouterClient(
                self.values["api_key"],
                base_url=self.values["base_url"],
            )
            markdown = client.generate_mindmap(
                topic=self.values["topic"],
                requirements=self.values["requirements"],
                language=self.values["language"],
                model=self.values["model"],
            )
            self.generated.emit(markdown)
        except Exception as exc:
            self.failed.emit(str(exc))


class AIGenerationDialog(QDialog):
    def __init__(self, api_key="", model=DEFAULT_MODEL, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Concept Map · OrcaRouter")
        self.setMinimumWidth(560)

        title = QLabel("Generate a concept map with AI")
        title.setObjectName("dialogTitle")
        subtitle = QLabel(
            "OrcaRouter is optional. Your topic is sent only when you press Generate."
        )
        subtitle.setWordWrap(True)

        self.provider = QComboBox()
        self.provider.addItem("OrcaRouter")
        self.provider.setEnabled(False)

        self.api_key = QLineEdit(api_key)
        self.api_key.setEchoMode(QLineEdit.Password)
        self.api_key.setPlaceholderText("sk-orca-...")
        show_key = QCheckBox("Show")
        show_key.toggled.connect(
            lambda checked: self.api_key.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        )
        key_row = QHBoxLayout()
        key_row.addWidget(self.api_key, 1)
        key_row.addWidget(show_key)

        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.addItems([
            "orcarouter/free",
            "orcarouter/auto",
            "deepseek/deepseek-v4-flash-free",
        ])
        self.model.setCurrentText(model or DEFAULT_MODEL)

        self.topic = QLineEdit()
        self.topic.setPlaceholderText("e.g. Artificial intelligence, project planning, study notes")
        self.requirements = QTextEdit()
        self.requirements.setPlaceholderText("Optional: desired branches, audience, depth, tone…")
        self.requirements.setMaximumHeight(110)

        self.language = QComboBox()
        self.language.addItem("中文", "Chinese")
        self.language.addItem("English", "English")

        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.addRow("Provider", self.provider)
        form.addRow("API key", key_row)
        form.addRow("Model", self.model)
        form.addRow("Central topic", self.topic)
        form.addRow("Requirements", self.requirements)
        form.addRow("Output language", self.language)

        docs_button = QPushButton("Get API key / Documentation")
        docs_button.setFlat(True)
        docs_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://docs.orcarouter.ai/getting-started/quickstart"))
        )

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText("Generate")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        footer = QHBoxLayout()
        footer.addWidget(docs_button)
        footer.addStretch(1)
        footer.addWidget(buttons)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addSpacing(8)
        layout.addLayout(footer)

    def values(self):
        return {
            "api_key": self.api_key.text().strip(),
            "base_url": ORCAROUTER_BASE_URL,
            "model": self.model.currentText().strip(),
            "topic": self.topic.text().strip(),
            "requirements": self.requirements.toPlainText().strip(),
            "language": self.language.currentData(),
        }

    def accept(self):
        if not self.api_key.text().strip():
            self.api_key.setFocus()
            return
        if not self.topic.text().strip():
            self.topic.setFocus()
            return
        if not self.model.currentText().strip():
            self.model.setFocus()
            return
        super().accept()
