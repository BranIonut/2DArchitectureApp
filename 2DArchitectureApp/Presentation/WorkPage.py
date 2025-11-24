from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from Presentation.Page import Page


class WorkPage(Page):

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("Spatiu de Lucru")
        header.setFont(QFont('Arial', 18, QFont.Bold))
        header.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(header)

        # Canvas placeholder
        canvas = QLabel("Aici va fi canvas-ul pentru desenare")
        canvas.setAlignment(Qt.AlignCenter)
        canvas.setStyleSheet("""
            background-color: white;
            border: 2px dashed #ccc;
            margin: 20px;
            padding: 50px;
        """)
        canvas.setFont(QFont('Arial', 14))
        layout.addWidget(canvas, 1)

        # Toolbar
        toolbar = QWidget()
        toolbar_layout = QVBoxLayout()

        tools_label = QLabel("Unelte:")
        tools_label.setFont(QFont('Arial', 12, QFont.Bold))
        toolbar_layout.addWidget(tools_label)

        tool_buttons = ["Perete", "Usa", "Fereastra", "Sterge"]
        for tool in tool_buttons:
            btn = QPushButton(tool)
            btn.setFixedHeight(35)
            toolbar_layout.addWidget(btn)

        toolbar.setLayout(toolbar_layout)
        toolbar.setFixedWidth(150)
        toolbar.setStyleSheet("background-color: #f9f9f9; padding: 10px;")

        content = QWidget()
        content_layout = QVBoxLayout()

        work_area = QWidget()
        work_layout = QVBoxLayout()
        work_layout.addWidget(canvas)
        work_area.setLayout(work_layout)

        content_layout.addWidget(work_area)
        content.setLayout(content_layout)
        layout.addWidget(content, 1)

        btn_back = QPushButton("← Inapoi la Meniu")
        btn_back.setFixedSize(150, 40)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        btn_back.clicked.connect(lambda: self.dashboard.update_page('main'))
        layout.addWidget(btn_back)

        self.setLayout(layout)
