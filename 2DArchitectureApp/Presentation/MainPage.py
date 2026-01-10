from PyQt5.QtWidgets import (QVBoxLayout, QPushButton, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .Page import Page

class MainPage(Page):
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Titlu
        title = QLabel("Floor Plan Architecture")
        title.setFont(QFont('Arial', 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Creeaza planuri arhitecturale 2D")
        subtitle.setFont(QFont('Arial', 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray; margin-bottom: 30px;")
        layout.addWidget(subtitle)

        # Buton Work
        btn_work = QPushButton("Incepe Lucrul")
        btn_work.setFixedSize(200, 50)
        btn_work.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        btn_work.clicked.connect(lambda: self.dashboard.update_page('work'))
        layout.addWidget(btn_work)

        # Buton Help
        btn_help = QPushButton("Ajutor")
        btn_help.setFixedSize(200, 50)
        btn_help.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #0b7dda; }
        """)
        btn_help.clicked.connect(lambda: self.dashboard.update_page('help'))
        layout.addWidget(btn_help)

        self.setLayout(layout)