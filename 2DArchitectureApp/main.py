# main.py
import sys
from PyQt5.QtWidgets import QApplication

from Presentation.Dashboard import Dashboard

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.run()
    sys.exit(app.exec_())
