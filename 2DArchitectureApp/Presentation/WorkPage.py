# Presentation/WorkPage.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QColor

from Presentation.Page import Page
from Business.ProjectManager import ProjectManager

class CanvasWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(600, 400)
        self.pm = ProjectManager()

        self.current_tool = "select"

        self.temp_wall_start: QPoint | None = None
        self.temp_mouse_pos: QPoint | None = None

        if self.pm.current_project is None:
            self.pm.create_new_project("Proiect Diana", 2000, 2000)

    def set_tool(self, tool_name: str):
        self.current_tool = tool_name
        self.temp_wall_start = None
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        x = event.pos().x()
        y = event.pos().y()

        if self.current_tool == "select":
            obj = self.pm.find_object_at_position(x, y)
            self.pm.select_object(obj)
            self.update()

        elif self.current_tool == "wall":
            if self.temp_wall_start is None:
                self.temp_wall_start = event.pos()
            else:
                start = self.temp_wall_start
                end = event.pos()
                self.pm.add_wall(start.x(), start.y(), end.x(), end.y(), thickness=20)
                self.temp_wall_start = None
                self.update()

        elif self.current_tool == "door":
            self.pm.add_door(x, y, width=80, height=20)
            self.update()

        elif self.current_tool == "window":
            self.pm.add_window(x, y, width=100, height=20)
            self.update()

        elif self.current_tool == "delete":
            obj = self.pm.find_object_at_position(x, y)
            if obj:
                self.pm.remove_object(obj)
                self.update()

    def mouseMoveEvent(self, event):
        self.temp_mouse_pos = event.pos()
        self.update()


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.fillRect(self.rect(), QBrush(QColor("white")))

        if self.pm.get_grid_visible():
            self._draw_grid(painter)

        self._draw_objects(painter)

        if self.current_tool == "wall" and self.temp_wall_start and self.temp_mouse_pos:
            pen = QPen(QColor(0, 150, 0), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(self.temp_wall_start, self.temp_mouse_pos)

        painter.end()

    def _draw_grid(self, painter: QPainter):
        cs = self.pm.coordinate_system
        vertical, horizontal = cs.get_grid_lines(self.width(), self.height())

        pen = QPen(QColor(230, 230, 230))
        pen.setWidth(1)
        painter.setPen(pen)

        for x in vertical:
            painter.drawLine(x, 0, x, self.height())

        for y in horizontal:
            painter.drawLine(0, y, self.width(), y)

    def _draw_objects(self, painter: QPainter):
        # pereti
        pen_wall = QPen(QColor("#2C3E50"), 4)
        brush_wall = QBrush(QColor("#34495E"))
        # usi
        pen_door = QPen(QColor("#8B4513"), 2)
        brush_door = QBrush(QColor("#A0522D"))
        # ferestre
        pen_window = QPen(QColor("#2980B9"), 2)
        brush_window = QBrush(QColor("#87CEEB"))

        for wall in self.pm.get_walls():
            x, y, w, h = wall.get_bounds()
            painter.setPen(pen_wall)
            painter.setBrush(brush_wall)
            painter.drawRect(x, y, w, h)

        for door in self.pm.get_doors():
            x, y, w, h = door.get_bounds()
            painter.setPen(pen_door)
            painter.setBrush(brush_door)
            painter.drawRect(x, y, w, h)

        for window in self.pm.get_windows():
            x, y, w, h = window.get_bounds()
            painter.setPen(pen_window)
            painter.setBrush(brush_window)
            painter.drawRect(x, y, w, h)

        selected = self.pm.get_selected_object()
        if selected:
            x, y, w, h = selected.get_bounds()
            sel_pen = QPen(QColor(255, 0, 0))
            sel_pen.setWidth(2)
            sel_pen.setStyle(Qt.DashLine)
            painter.setPen(sel_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(x - 3, y - 3, w + 6, h + 6)


class WorkPage(Page):
    def init_ui(self):
        self.pm = ProjectManager()
        if self.pm.current_project is None:
            self.pm.create_new_project("Proiect", 2000, 2000)

        main_layout = QVBoxLayout()
        header = QLabel("Spatiu de lucru")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("padding: 8px; background-color: #f0f0f0;")
        main_layout.addWidget(header)

        # zona centrala: toolbar stanga + canvas dreapta
        center = QHBoxLayout()

        # ----- toolbar -----
        toolbar = QWidget()
        toolbar_layout = QVBoxLayout()
        toolbar_layout.setAlignment(Qt.AlignTop)

        tools_label = QLabel("Unelte")
        tools_label.setFont(QFont("Arial", 12, QFont.Bold))
        toolbar_layout.addWidget(tools_label)

        self.canvas = CanvasWidget(self)

        # butoane unelte
        self.tool_buttons = {}
        tools = [
            ("Selectie", "select"),
            ("Perete", "wall"),
            ("Usa", "door"),
            ("Fereastra", "window"),
            ("Sterge", "delete"),
        ]

        for text, tool_name in tools:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(35)
            btn.clicked.connect(
                lambda checked, name=tool_name, b=btn: self._on_tool_clicked(name, b)
            )
            toolbar_layout.addWidget(btn)
            self.tool_buttons[tool_name] = btn

        # select implicit – selectie
        self.tool_buttons["select"].setChecked(True)

        toolbar_layout.addStretch()
        toolbar.setLayout(toolbar_layout)
        toolbar.setFixedWidth(150)
        toolbar.setStyleSheet("background-color: #f9f9f9; padding: 8px;")

        center.addWidget(toolbar)
        center.addWidget(self.canvas, 1)

        center_widget = QWidget()
        center_widget.setLayout(center)
        main_layout.addWidget(center_widget, 1)

        # buton inapoi
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
        btn_back.clicked.connect(lambda: self.dashboard.update_page("main"))
        main_layout.addWidget(btn_back, alignment=Qt.AlignLeft)

        self.setLayout(main_layout)

    def _on_tool_clicked(self, tool_name: str, clicked_button: QPushButton):
        # debifam celelalte butoane
        for name, btn in self.tool_buttons.items():
            if btn is not clicked_button:
                btn.setChecked(False)

        clicked_button.setChecked(True)
        self.canvas.set_tool(tool_name)
