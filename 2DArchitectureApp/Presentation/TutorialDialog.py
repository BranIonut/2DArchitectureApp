from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSplitter,
    QListWidget, QTextBrowser, QPushButton, QWidget
)
from PyQt5.QtCore import Qt


class TutorialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ghid Interactiv - Architect App")
        self.resize(800, 500)

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)

        lbl_title = QLabel("Manual de Utilizare")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        splitter = QSplitter(Qt.Horizontal)

        self.topic_list = QListWidget()
        self.topic_list.setFixedWidth(200)
        self.topic_list.setStyleSheet("""
            QListWidget { background: #F7F9F9; border: 1px solid #BDC3C7; font-size: 14px; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #E0E0E0; }
            QListWidget::item:selected { background: #3498DB; color: white; }
        """)
        splitter.addWidget(self.topic_list)

        self.content_viewer = QTextBrowser()
        self.content_viewer.setStyleSheet(
            "background: white; padding: 15px; font-size: 14px; border: 1px solid #BDC3C7;")
        splitter.addWidget(self.content_viewer)

        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        btn_close = QPushButton("Am inteles")
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet("background: #2ECC71; color: white; font-weight: bold; padding: 8px;")
        layout.addWidget(btn_close)

        self.topics = {
            "Introducere": """
                <h3>Bine ai venit!</h3>
                <p>Aceasta aplicatie te ajuta sa creezi planuri 2D rapid si usor.</p>
                <p>Selecteaza un subiect din stanga pentru a invata cum sa folosesti uneltele.</p>
            """,
            "Desenare Pereti": """
                <h3>Cum desenezi un perete</h3>
                <ol>
                    <li>Din meniul din stanga, tab-ul <b>Structura</b>, selecteaza <b>Perete (Linie)</b>.</li>
                    <li>Cursorul va deveni o cruce (+).</li>
                    <li>Click pe canvas pentru punctul de <b>START</b>.</li>
                    <li>Misca mouse-ul spre punctul de <b>FINAL</b>.</li>
                    <li>Click din nou pentru a termina peretele.</li>
                </ol>
                <p><i>Nota: Lungimea peretelui este afisata automat deasupra liniei.</i></p>
            """,
            "Adaugare Camere (Podea)": """
                <h3>Cum desenezi o camera intreaga</h3>
                <ol>
                    <li>Selecteaza <b>Zona / Camera</b> din meniu sau apasa butonul verde <b>Adauga Zona</b> din dreapta.</li>
                    <li>Click pe canvas (intr-un colt al camerei) si <b>TINE APASAT</b>.</li>
                    <li>Trage mouse-ul pe diagonala pana obtii marimea dorita.</li>
                    <li>Elibereaza click-ul.</li>
                </ol>
                <p>Suprafata in m2 va fi calculata automat in centrul camerei.</p>
            """,
            "Plasare Mobila & Usi": """
                <h3>Mobilier si Usi</h3>
                <ul>
                    <li>Deschide categoriile din stanga (ex: <b>Furniture</b>, <b>Usi</b>).</li>
                    <li>Click pe un obiect din lista.</li>
                    <li>Du mouse-ul pe plan si da <b>Click Stanga</b> unde vrei sa il plasezi.</li>
                </ul>
            """,
            "Selectare & Mutare": """
                <h3>Selectare si Mutare</h3>
                <ul>
                    <li>Click pe orice obiect (perete sau mobila) pentru a-l selecta.</li>
                    <li>Obiectul va fi conturat cu rosu sau albastru.</li>
                    <li>Tine apasat <b>Click Stanga</b> pe obiect si trage-l pentru a-l muta.</li>
                </ul>
                <p><b>Smart Snap:</b> Liniile verzi punctate vor aparea automat pentru a te ajuta sa aliniezi obiectul cu altele din jur.</p>
            """,
            "Redimensionare (Resize)": """
                <h3>Redimensionare</h3>
                <ol>
                    <li>Selecteaza un obiect de mobilier sau o fereastra.</li>
                    <li>Vor aparea 4 patratele albe in colturi (manere).</li>
                    <li>Trage de oricare colt pentru a mari sau micsora obiectul.</li>
                </ol>
                <p><i>Peretii se redimensioneaza tragand de capete.</i></p>
            """,
            "Rotire Obiecte": """
                <h3>Cum rotesti obiectele</h3>
                <p>Exista doua metode:</p>
                <ol>
                    <li><b>Cu Mouse-ul (Rapid):</b> Selecteaza obiectul si foloseste <b>Rotita Mouse-ului (Scroll)</b>.
                        <ul><li>Tine apasat <b>Shift</b> + Scroll pentru rotire fina (5 grade).</li></ul>
                    </li>
                    <li><b>Manual (Precis):</b> Selecteaza obiectul, apoi tine apasat <b>Click Dreapta</b> si misca mouse-ul in jurul centrului.</li>
                    <li><b>Din Panou:</b> Foloseste casuta "Rotatie" din meniul din dreapta.</li>
                </ol>
            """,
            "Masurare (Rigla)": """
                <h3>Folosirea Riglei</h3>
                <ol>
                    <li>Selecteaza <b>Rigla (Masurare)</b> din meniu.</li>
                    <li>Click si tine apasat oriunde pe canvas.</li>
                    <li>Trage mouse-ul catre punctul final.</li>
                    <li>Distanta va fi afisata in timp real pe linia albastra.</li>
                </ol>
                <p><i>Masuratoarea dispare cand eliberezi mouse-ul.</i></p>
            """,
            "Stergere & Zoom": """
                <h3>Stergere si Navigare</h3>
                <ul>
                    <li><b>Stergere:</b> Selecteaza un obiect si apasa tasta <b>Delete</b> sau butonul rosu din dreapta.</li>
                    <li><b>Zoom:</b> Tine apasat <b>Ctrl</b> + Scroll.</li>
                    <li><b>Pan (Deplasare plan):</b> Tine apasat <b>Click Mijloc (Rotita)</b> si trage de plan.</li>
                </ul>
            """
        }

        self.topic_list.addItems(self.topics.keys())
        self.topic_list.currentRowChanged.connect(self.display_topic)
        self.topic_list.setCurrentRow(0)

    def display_topic(self, row):
        key = self.topic_list.item(row).text()
        content = self.topics.get(key, "")
        self.content_viewer.setHtml(content)