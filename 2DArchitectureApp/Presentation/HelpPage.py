from .Page import Page
from PyQt5.QtWidgets import (QVBoxLayout, QPushButton, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class HelpPage(Page):

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Ajutor si Instructiuni")
        title.setFont(QFont('Arial', 20, QFont.Bold))
        title.setStyleSheet("padding: 20px;")
        layout.addWidget(title)

        help_text = """
        <h3>Cum sa folosesti aplicatia:</h3>
        <ul>
            <li><b>Perete:</b> Deseneaza pereti pentru a crea conturul Incaperii</li>
            <li><b>Usa:</b> Adauga usi In pereti</li>
            <li><b>Fereastra:</b> Adauga ferestre In pereti</li>
            <li><b>sterge:</b> sterge elemente din plan</li>
        </ul>

        <h3>Controale:</h3>
        <ul>
            <li>Click stanga - Selecteaza/Plaseaza</li>
            <li>Click dreapta - Meniu contextual</li>
            <li>Scroll - Zoom in/out</li>
        </ul>

        <h3>Sfaturi:</h3>
        <ul>
            <li>Incepe prin a desena peretele exterior</li>
            <li>Adauga apoi peretii interiori</li>
            <li>Plaseaza usile si ferestrele la final</li>
        </ul>
        """

        content = QLabel(help_text)
        content.setWordWrap(True)
        content.setStyleSheet("""
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 5px;
            margin: 0 20px;
        """)
        layout.addWidget(content)

        layout.addStretch()

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

