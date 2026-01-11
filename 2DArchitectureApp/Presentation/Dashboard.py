from PyQt5.QtWidgets import (QMainWindow, QStackedWidget)

from .HelpPage import HelpPage
from .MainPage import MainPage
from .WorkPage import WorkPage


class Dashboard(QMainWindow):
    """
        Fereastra principala a aplicatiei.
        Gestioneaza navigarea intre ecrane folosind QStackedWidget.
        """
    def __init__(self):
        super().__init__()
        self.page = None
        self.previous_page = None
        self.pages = {}
        self.init_ui()

    def init_ui(self):
        """ Initializeaza fereastra si stiva de pagini. """

        self.setWindowTitle("Floor Plan Architecture")
        self.setGeometry(100, 100, 1400, 800)

        # Widget-ul 'stiva' permite afisarea unei singure pagini la un moment dat
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initializare pagini
        self.pages['main'] = MainPage(self)
        self.pages['work'] = WorkPage(self)
        self.pages['help'] = HelpPage(self)

        # Inregistrare pagini
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

        # Setare pagina de start
        self.page = 'main'
        self.stacked_widget.setCurrentWidget(self.pages['main'])

    def update_page(self, page_name):
        """ Schimba pagina curenta afisata. """
        if page_name in self.pages:
            self.previous_page = self.page
            self.page = page_name
            self.stacked_widget.setCurrentWidget(self.pages[page_name])

    def run(self):
        self.show()


