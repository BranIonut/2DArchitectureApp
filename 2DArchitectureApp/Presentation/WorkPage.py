from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QWidget,
    QGroupBox, QScrollArea, QMessageBox, QFileDialog, QSpinBox,
    QCheckBox, QSlider, QComboBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush

from Presentation.Page import Page
from Business.ProjectManager import ProjectManager


class SimpleCanvas(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pm = ProjectManager()
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: white;")

        self.setMouseTracking(True)
        self.mouse_x = 0
        self.mouse_y = 0

        self.is_drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_tool = None

        self.is_moving = False
        self.drag_start_x = 0
        self.drag_start_y = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.pm.get_grid_visible():
            self.draw_grid(painter)

        self.draw_objects(painter)

        if self.is_drawing and self.current_tool:
            self.draw_preview(painter)

    def draw_grid(self, painter):
        grid_size = self.pm.coordinate_system.grid_size

        pen = QPen(QColor(220, 220, 220))
        pen.setWidth(1)
        painter.setPen(pen)

        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())

        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)

        pen.setColor(QColor(180, 180, 180))
        pen.setWidth(2)
        painter.setPen(pen)

        for x in range(0, self.width(), grid_size * 10):
            painter.drawLine(x, 0, x, self.height())

        for y in range(0, self.height(), grid_size * 10):
            painter.drawLine(0, y, self.width(), y)

    def draw_objects(self, painter):
        for wall in self.pm.get_walls():
            color = QColor(wall.color) if not wall.selected else QColor("#FF5722")
            pen = QPen(color)
            pen.setWidth(int(wall.thickness) if not wall.selected else int(wall.thickness) + 4)
            painter.setPen(pen)
            painter.drawLine(int(wall.x1), int(wall.y1), int(wall.x2), int(wall.y2))

        for door in self.pm.get_doors():
            color = QColor(door.color) if not door.selected else QColor("#FF5722")
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawRect(int(door.x), int(door.y), int(door.width), int(door.height))

            if not door.selected:
                painter.setPen(QPen(color, 1))
                painter.drawArc(int(door.x), int(door.y), int(door.width), int(door.width), 0, 90 * 16)

        for window in self.pm.get_windows():
            color = QColor(window.color) if not window.selected else QColor("#FF5722")
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(QColor(173, 216, 230, 150)))
            painter.drawRect(int(window.x), int(window.y), int(window.width), int(window.height))

            mid_x = int(window.x + window.width / 2)
            mid_y = int(window.y + window.height / 2)
            painter.drawLine(mid_x, int(window.y), mid_x, int(window.y + window.height))
            painter.drawLine(int(window.x), mid_y, int(window.x + window.width), mid_y)

        for furniture in self.pm.get_furniture():
            color = QColor(furniture.color) if not furniture.selected else QColor("#FF5722")
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(QColor(furniture.color)))
            painter.drawRect(int(furniture.x), int(furniture.y), int(furniture.width), int(furniture.height))

            painter.setPen(QPen(Qt.white))
            painter.setFont(QFont('Arial', 8))
            painter.drawText(int(furniture.x + 5), int(furniture.y + 15), furniture.furniture_type)

    def draw_preview(self, painter):
        pen = QPen(QColor(100, 100, 100))
        pen.setStyle(Qt.DashLine)
        pen.setWidth(2)
        painter.setPen(pen)

        if self.current_tool == "wall":
            painter.drawLine(int(self.start_x), int(self.start_y),
                             int(self.mouse_x), int(self.mouse_y))
        elif self.current_tool in ["door", "window", "furniture"]:
            width = abs(self.mouse_x - self.start_x)
            height = abs(self.mouse_y - self.start_y)
            x = min(self.start_x, self.mouse_x)
            y = min(self.start_y, self.mouse_y)
            painter.drawRect(int(x), int(y), int(width), int(height))

    def mousePressEvent(self, event):
        x, y = event.x(), event.y()

        if event.button() != Qt.LeftButton:
            return

        if self.current_tool:
            self.is_drawing = True

            if self.pm.get_snap_to_grid():
                self.start_x, self.start_y = self.pm.coordinate_system.snap_to_grid(x, y)
            else:
                self.start_x = x
                self.start_y = y
            self.update()
            return

        obj = self.pm.find_object_at_position(x, y)

        self.pm.select_object(obj)

        if obj:
            self.is_moving = True
            self.drag_start_x = x
            self.drag_start_y = y

        self.update()
        if self.parent():
            self.parent().parent().refresh_statistics()

    def mouseMoveEvent(self, event):
        self.mouse_x = event.x()
        self.mouse_y = event.y()

        if self.parent() and self.parent().parent():
            self.parent().parent().update_mouse_position(self.mouse_x, self.mouse_y)

        if self.is_drawing:
            self.update()

        elif self.is_moving and self.pm.get_selected_object():
            dx = self.mouse_x - self.drag_start_x
            dy = self.mouse_y - self.drag_start_y

            self.pm.translate_selected(dx, dy)

            self.drag_start_x = self.mouse_x
            self.drag_start_y = self.mouse_y

            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:

            if self.is_moving:
                self.is_moving = False

                self.pm._sync_to_project()

                if self.pm.get_snap_to_grid() and self.pm.get_selected_object():
                    obj = self.pm.get_selected_object()
                    snapped_x, snapped_y = self.pm.coordinate_system.snap_to_grid(obj.x, obj.y)
                    self.pm.translate_selected(snapped_x - obj.x, snapped_y - obj.y)

                self.update()
                if self.parent() and self.parent().parent():
                    self.parent().parent().refresh_statistics()
                    self.parent().parent().lbl_status.setText("Obiect mutat cu succes")
                return

            if self.is_drawing:
                self.is_drawing = False

                end_x, end_y = event.x(), event.y()
                if self.pm.get_snap_to_grid():
                    end_x, end_y = self.pm.coordinate_system.snap_to_grid(end_x, end_y)

                if self.current_tool == "wall":
                    self.pm.add_wall(self.start_x, self.start_y, end_x, end_y)
                elif self.current_tool == "door":
                    width = abs(end_x - self.start_x)
                    height = abs(end_y - self.start_y)
                    self.pm.add_door(min(self.start_x, end_x), min(self.start_y, end_y),
                                     max(width, 80), max(height, 20))
                elif self.current_tool == "window":
                    width = abs(end_x - self.start_x)
                    height = abs(end_y - self.start_y)
                    self.pm.add_window(min(self.start_x, end_x), min(self.start_y, end_y),
                                       max(width, 100), max(height, 20))
                elif self.current_tool == "furniture":
                    width = abs(end_x - self.start_x)
                    height = abs(end_y - self.start_y)
                    self.pm.add_furniture(min(self.start_x, end_x), min(self.start_y, end_y),
                                          max(width, 50), max(height, 50), "mobilier")

                self.update()
                if self.parent() and self.parent().parent():
                    self.parent().parent().refresh_statistics()
                    self.parent().parent().lbl_status.setText(f"Obiect '{self.current_tool}' adăugat")


class WorkPage(Page):

    def init_ui(self):
        self.pm = ProjectManager()

        if not self.pm.current_project:
            self.pm.create_new_project("Proiect Nou", width=1000, height=800)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = self.create_header()
        main_layout.addWidget(header)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)

        toolbar = self.create_toolbar()
        content_layout.addWidget(toolbar)

        canvas_container = QWidget()
        canvas_layout = QVBoxLayout()
        canvas_layout.setContentsMargins(10, 10, 10, 10)

        self.canvas = SimpleCanvas(self)
        canvas_layout.addWidget(self.canvas)

        canvas_container.setLayout(canvas_layout)
        content_layout.addWidget(canvas_container, 1)

        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel)

        main_layout.addLayout(content_layout, 1)

        footer = self.create_footer()
        main_layout.addWidget(footer)

        self.setLayout(main_layout)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_statistics)
        self.refresh_timer.start(1000)

    def create_header(self):
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: #03254C;
                padding: 10px;
            }
            QPushButton {
                background-color: #185E8A;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 15px;
                margin: 0 5px;
            }
            QPushButton:hover {
                background-color: #2679AE;
            }
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)

        layout = QHBoxLayout()

        title = QLabel("Floor Plan Architecture - Workspace")
        layout.addWidget(title)

        layout.addStretch()

        btn_new = QPushButton("Nou")
        btn_new.clicked.connect(self.new_project)
        layout.addWidget(btn_new)

        btn_save = QPushButton("Salveaza")
        btn_save.clicked.connect(self.save_project)
        layout.addWidget(btn_save)

        btn_load = QPushButton("Deschide")
        btn_load.clicked.connect(self.load_project)
        layout.addWidget(btn_load)

        btn_back = QPushButton("Meniu")
        btn_back.clicked.connect(lambda: self.dashboard.update_page('main'))
        layout.addWidget(btn_back)

        header.setLayout(layout)
        return header

    def create_toolbar(self):
        toolbar = QWidget()
        toolbar.setFixedWidth(200)
        toolbar.setStyleSheet("""
            QWidget {
                background-color: #F7F3E8;
                padding: 10px;
            }
            QPushButton {
                background-color: #008080;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                margin: 5px 0;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #009999;
            }
            QPushButton:checked {
                background-color: #FF6F61;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #D1C4A5;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        tools_group = QGroupBox("Unelte Desenare")
        tools_layout = QVBoxLayout()

        self.btn_wall = QPushButton("Perete")
        self.btn_wall.setCheckable(True)
        self.btn_wall.clicked.connect(lambda: self.select_tool("wall"))
        tools_layout.addWidget(self.btn_wall)

        self.btn_door = QPushButton("Usa")
        self.btn_door.setCheckable(True)
        self.btn_door.clicked.connect(lambda: self.select_tool("door"))
        tools_layout.addWidget(self.btn_door)

        self.btn_window = QPushButton("Fereastra")
        self.btn_window.setCheckable(True)
        self.btn_window.clicked.connect(lambda: self.select_tool("window"))
        tools_layout.addWidget(self.btn_window)

        self.btn_furniture = QPushButton("Mobilier")
        self.btn_furniture.setCheckable(True)
        self.btn_furniture.clicked.connect(lambda: self.select_tool("furniture"))
        tools_layout.addWidget(self.btn_furniture)

        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)

        grid_group = QGroupBox("Setari Grila")
        grid_layout = QVBoxLayout()

        grid_size_layout = QHBoxLayout()
        grid_size_layout.addWidget(QLabel("Dimensiune:"))
        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(5, 50)
        self.grid_size_spin.setValue(10)
        self.grid_size_spin.valueChanged.connect(self.change_grid_size)
        grid_size_layout.addWidget(self.grid_size_spin)
        grid_layout.addLayout(grid_size_layout)

        self.grid_visible_check = QCheckBox("Afiseaza grila")
        self.grid_visible_check.setChecked(True)
        self.grid_visible_check.stateChanged.connect(self.toggle_grid_visibility)
        grid_layout.addWidget(self.grid_visible_check)

        self.snap_to_grid_check = QCheckBox("Snap to grid")
        self.snap_to_grid_check.setChecked(True)
        self.snap_to_grid_check.stateChanged.connect(self.toggle_snap_to_grid)
        grid_layout.addWidget(self.snap_to_grid_check)

        grid_group.setLayout(grid_layout)
        layout.addWidget(grid_group)

        btn_clear = QPushButton("Sterge Tot")
        btn_clear.setStyleSheet("background-color: #E74C3C;")
        btn_clear.clicked.connect(self.clear_all)
        layout.addWidget(btn_clear)

        layout.addStretch()

        toolbar.setLayout(layout)
        return toolbar

    def create_right_panel(self):
        panel = QWidget()
        panel.setFixedWidth(250)
        panel.setStyleSheet("""
            QWidget {
                background-color: #FEFCF3;
                padding: 10px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #D1C4A5;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QLabel {
                padding: 3px;
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        stats_group = QGroupBox("Statistici Proiect")
        stats_layout = QVBoxLayout()

        self.lbl_project_name = QLabel("Proiect: -")
        self.lbl_total_objects = QLabel("Total obiecte: 0")
        self.lbl_walls = QLabel("Pereti: 0")
        self.lbl_doors = QLabel("Usi: 0")
        self.lbl_windows = QLabel("Ferestre: 0")
        self.lbl_furniture = QLabel("Mobilier: 0")
        self.lbl_wall_length = QLabel("Lungime pereti: 0 cm")

        for lbl in [self.lbl_project_name, self.lbl_total_objects, self.lbl_walls,
                    self.lbl_doors, self.lbl_windows, self.lbl_furniture, self.lbl_wall_length]:
            stats_layout.addWidget(lbl)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        coord_group = QGroupBox("Sistem Coordonate")
        coord_layout = QVBoxLayout()

        self.lbl_grid_size = QLabel("Grila: 10 px")
        self.lbl_snap = QLabel("Snap: Activ")
        self.lbl_conversion = QLabel("10 px = 1 cm")

        for lbl in [self.lbl_grid_size, self.lbl_snap, self.lbl_conversion]:
            coord_layout.addWidget(lbl)

        coord_group.setLayout(coord_layout)
        layout.addWidget(coord_group)

        canvas_group = QGroupBox("Canvas")
        canvas_layout = QVBoxLayout()

        self.lbl_canvas_size = QLabel("Dimensiune: 1000x800")
        self.lbl_mouse_pos = QLabel("Mouse: (0, 0)")

        canvas_layout.addWidget(self.lbl_canvas_size)
        canvas_layout.addWidget(self.lbl_mouse_pos)

        canvas_group.setLayout(canvas_layout)
        layout.addWidget(canvas_group)

        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def create_footer(self):
        footer = QWidget()
        footer.setStyleSheet("""
            QWidget {
                background-color: #185E8A;
                padding: 5px 10px;
            }
            QLabel {
                color: white;
                font-size: 11px;
            }
        """)

        layout = QHBoxLayout()

        self.lbl_status = QLabel("Gata | Selecteaza o unealta pentru a incepe")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        footer.setLayout(layout)
        return footer

    def select_tool(self, tool):
        for btn in [self.btn_wall, self.btn_door, self.btn_window, self.btn_furniture]:
            btn.setChecked(False)

        if tool == "wall":
            self.btn_wall.setChecked(True)
            self.lbl_status.setText("Deseneaza pereti | Click si drag pentru a crea un perete")
        elif tool == "door":
            self.btn_door.setChecked(True)
            self.lbl_status.setText("Deseneaza usi | Click si drag pentru a plasa o usa")
        elif tool == "window":
            self.btn_window.setChecked(True)
            self.lbl_status.setText("Deseneaza ferestre | Click si drag pentru a plasa o fereastra")
        elif tool == "furniture":
            self.btn_furniture.setChecked(True)
            self.lbl_status.setText("Deseneaza mobilier | Click si drag pentru a plasa mobilier")

        self.canvas.current_tool = tool

    def change_grid_size(self, value):
        self.pm.set_grid_size(value)
        self.canvas.update()
        self.refresh_statistics()

    def toggle_grid_visibility(self):
        self.pm.toggle_grid_visibility()
        self.canvas.update()
        self.refresh_statistics()

    def toggle_snap_to_grid(self):
        self.pm.toggle_snap_to_grid()
        self.refresh_statistics()

    def clear_all(self):
        reply = QMessageBox.question(
            self, 'Confirmare',
            'Sigur doresti sa stergi toate obiectele?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.pm.current_project:
                self.pm.current_project.clear()
                self.pm._clear_caches()
                self.canvas.update()
                self.refresh_statistics()
                self.lbl_status.setText("Toate obiectele au fost sterse")

    def new_project(self):
        self.pm.create_new_project("Proiect Nou")
        self.canvas.update()
        self.refresh_statistics()
        self.lbl_status.setText("Proiect nou creat")

    def save_project(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salveaza Proiect", "", "JSON Files (*.json)"
        )

        if filename:
            if self.pm.save_project(filename):
                QMessageBox.information(self, "Success", f"Proiect salvat: {filename}")
                self.lbl_status.setText(f"Proiect salvat: {filename}")
            else:
                QMessageBox.warning(self, "Eroare", "Nu s-a putut salva proiectul")

    def load_project(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Deschide Proiect", "", "JSON Files (*.json)"
        )

        if filename:
            if self.pm.load_project(filename):
                self.canvas.update()
                self.refresh_statistics()
                QMessageBox.information(self, "Success", f"Proiect incarcat: {filename}")
                self.lbl_status.setText(f"Proiect incarcat: {filename}")
            else:
                QMessageBox.warning(self, "Eroare", "Nu s-a putut incarca proiectul")

    def update_mouse_position(self, x: int, y: int):
        self.lbl_mouse_pos.setText(f"Mouse: ({x}, {y})")

    def refresh_statistics(self):
        stats = self.pm.get_statistics()
        selected_obj = self.pm.get_selected_object()

        if stats:
            self.lbl_project_name.setText(f"Proiect: {stats['project_name']}")
            self.lbl_total_objects.setText(f"Total obiecte: {stats['total_objects']}")
            self.lbl_walls.setText(f"Pereti: {stats['walls_count']}")
            self.lbl_doors.setText(f"Usi: {stats['doors_count']}")
            self.lbl_windows.setText(f"Ferestre: {stats['windows_count']}")
            self.lbl_furniture.setText(f"Mobilier: {stats['furniture_count']}")
            self.lbl_wall_length.setText(f"Lungime pereti: {stats['total_wall_length']}")

            self.lbl_grid_size.setText(f"Grila: {stats['grid_size']} px")
            self.lbl_snap.setText(f"Snap: {'Activ' if stats['snap_to_grid'] else 'Inactiv'}")
            self.lbl_canvas_size.setText(f"Dimensiune: {stats['canvas_width']}x{stats['canvas_height']}")

            grid_cm = self.pm.coordinate_system.get_grid_spacing_cm()
            self.lbl_conversion.setText(f"{stats['grid_size']} px = {grid_cm:.1f} cm")

        if selected_obj:
            self.lbl_status.setText(f"Obiect selectat: Tip={type(selected_obj).__name__}, "
                                    f"Poz=({selected_obj.x:.0f}, {selected_obj.y:.0f}), "
                                    f"Dim={selected_obj.width:.0f}x{selected_obj.height:.0f}")
        elif not self.canvas.current_tool:
            self.lbl_status.setText("Gata | Selecteaza o unealta sau click pentru a selecta un obiect")