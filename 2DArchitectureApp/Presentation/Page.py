from abc import ABCMeta, abstractmethod
from PyQt5.QtWidgets import QWidget

class CombinedMeta(type(QWidget), ABCMeta):
    pass

class Page(QWidget, metaclass=CombinedMeta):
    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard
        self.init_ui()

    @abstractmethod
    def init_ui(self):
        pass