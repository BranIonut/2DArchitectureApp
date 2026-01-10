import math
import os
import sys

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
    QMessageBox, QFileDialog, QSpinBox, QCheckBox, QShortcut
)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QKeySequence
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from Business.ArchitecturalObjects import Transform

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .Page import Page
from Business.ProjectManager import ProjectManager


# =====================================================================
# CANVAS
# =====================================================================
#MODIFICARE ROTIRE
class SimpleCanvas(QWidget):
    mouse_moved_signal = pyqtSignal(int, int)
    project_changed_signal = pyqtSignal()
    status_message_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_rotating = False
        self.rotate_start_angle = 0.0
        self.initial_rotation = 0.0
        self.pm = ProjectManager()

        self.offset_x = 0
        self.offset_y = 0
        self.is_panning = False
        self.last_pan_x = 0
        self.last_pan_y = 0

        self.mouse_x = 0
        self.mouse_y = 0

        self.is_drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_tool = None

        self.is_moving = False
        self.drag_start_x = 0
        self.drag_start_y = 0

        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    # =============================== DRAW ===============================
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.white)

        scale = self.pm.get_view_scale()
        painter.translate(self.offset_x, self.offset_y)

        if self.pm.current_project and self.pm.current_project.grid_visible:
            self.draw_grid(painter, scale)

        self.draw_objects(painter, scale)

        if self.is_drawing and self.current_tool:
            self.draw_preview(painter, scale)

    def draw_grid(self, painter, scale: float):
        if not self.pm.current_project:
            return

        grid_size = self.pm.current_project.grid_size
        step = int(grid_size * scale)
        if step <= 2:
            return

        width = self.width()
        height = self.height()

        start_x = -self.offset_x
        start_y = -self.offset_y
        end_x = start_x + width
        end_y = start_y + height

        first_x = start_x - (start_x % step)
        first_y = start_y - (start_y % step)

        pen_main = QPen(QColor(220, 220, 220))
        pen_bold = QPen(QColor(180, 180, 180))
        pen_main.setWidth(1)
        pen_bold.setWidth(1)

        x = first_x
        while x < end_x + step:
            idx = int(x // step)
            painter.setPen(pen_bold if idx % 10 == 0 else pen_main)
            painter.drawLine(int(x), int(start_y), int(x), int(end_y))
            x += step

        y = first_y
        while y < end_y + step:
            idx = int(y // step)
            painter.setPen(pen_bold if idx % 10 == 0 else pen_main)
            painter.drawLine(int(start_x), int(y), int(end_x), int(y))
            y += step
    #MODIFICARE PT ROTIRE
    def draw_objects(self, painter, scale: float):
        to_scr = lambda v: int(v * scale)

        # WALLS
        for w in self.pm._walls:
            color = QColor("#FF5722") if w.selected else QColor(w.color)
            pen = QPen(color)
            pen.setWidth(max(2, int(w.thickness * scale)))
            painter.setPen(pen)
            painter.drawLine(to_scr(w.x1), to_scr(w.y1), to_scr(w.x2), to_scr(w.y2))

        # DOORS
        for d in self.pm._doors:

            painter.save()
            cx = (d.x + d.width / 2) * scale
            cy = (d.y + d.height / 2) * scale

            painter.translate(cx, cy)
            painter.rotate(d.rotation)
            painter.translate(-cx, -cy)

            sx, sy = to_scr(d.x), to_scr(d.y)
            sw, sh = to_scr(d.width), to_scr(d.height)
            color = QColor("#FF5722") if d.selected else QColor(d.color)
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawRect(sx, sy, sw, sh)

            painter.restore()

        # WINDOWS
        for w in self.pm._windows:
            painter.save()

            cx = (w.x + w.width / 2) * scale
            cy = (w.y + w.height / 2) * scale

            painter.translate(cx, cy)
            painter.rotate(w.rotation)
            painter.translate(-cx, -cy)

            sx, sy = to_scr(w.x), to_scr(w.y)
            sw, sh = to_scr(w.width), to_scr(w.height)
            color = QColor("#FF5722") if w.selected else QColor(w.color)
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(QColor(173, 216, 230, 150)))
            painter.drawRect(sx, sy, sw, sh)

            painter.restore()

        # FURNITURE
        for f in self.pm._furniture:
            painter.save()

            cx = (f.x + f.width / 2) * scale
            cy = (f.y + f.height / 2) * scale

            painter.translate(cx, cy)
            painter.rotate(f.rotation)
            painter.translate(-cx, -cy)

            sx, sy = to_scr(f.x), to_scr(f.y)
            sw, sh = to_scr(f.width), to_scr(f.height)
            color = QColor("#FF5722") if f.selected else QColor(f.color)
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawRect(sx, sy, sw, sh)

            painter.restore()

    def draw_preview(self, painter, scale: float):
        painter.setPen(QPen(QColor(100, 100, 100), 2, Qt.DashLine))

        sx = int(self.start_x * scale)
        sy = int(self.start_y * scale)
        mx = int((self.mouse_x - self.offset_x))
        my = int((self.mouse_y - self.offset_y))

        if self.current_tool == "wall":
            painter.drawLine(sx, sy, mx, my)
        else:
            painter.drawRect(
                min(sx, mx),
                min(sy, my),
                abs(mx - sx),
                abs(my - sy)
            )

    # =============================== MOUSE ==============================
    #MODIFICARE ROTIRE
    def mousePressEvent(self, e):
        scale = self.pm.get_view_scale()

        if e.button() == Qt.MiddleButton:
            self.is_panning = True
            self.last_pan_x = e.x()
            self.last_pan_y = e.y()
            self.setCursor(Qt.ClosedHandCursor)
            return

        if e.button() == Qt.RightButton and self.pm.selected_object:
            scale = self.pm.get_view_scale()
            wx = (e.x() - self.offset_x) / scale
            wy = (e.y() - self.offset_y) / scale

            obj = self.pm.selected_object
            cx, cy = obj.get_center()

            self.is_rotating = True
            self.rotate_start_angle = self._angle_to_mouse(cx, cy, wx, wy)
            self.initial_rotation = obj.rotation
            return

        if e.button() != Qt.LeftButton:
            return

        wx = (e.x() - self.offset_x) / scale
        wy = (e.y() - self.offset_y) / scale


        # DRAW MODE
        if self.current_tool:
            if self.pm.current_project and self.pm.current_project.snap_to_grid:
                wx, wy = self.pm.coordinate_system.snap_to_grid(wx, wy)
            self.is_drawing = True
            self.start_x, self.start_y = wx, wy
            self.update()
            return

        # SELECT MODE
        obj = self.pm.find_object_at(wx, wy)
        self.pm.select_object(obj)

        if obj:
            self.is_moving = True
            self.drag_start_x = wx
            self.drag_start_y = wy

        self.project_changed_signal.emit()
        self.update()
    #MODIFICARE ROTIRE
    def mouseMoveEvent(self, e):
        self.mouse_x = e.x()
        self.mouse_y = e.y()

        scale = self.pm.get_view_scale()
        wx = (e.x() - self.offset_x) / scale
        wy = (e.y() - self.offset_y) / scale

        self.mouse_moved_signal.emit(int(wx), int(wy))

        if self.is_panning:
            dx = e.x() - self.last_pan_x
            dy = e.y() - self.last_pan_y
            self.offset_x += dx
            self.offset_y += dy
            self.last_pan_x = e.x()
            self.last_pan_y = e.y()
            self.update()
            return

        if self.is_rotating and self.pm.selected_object:
            scale = self.pm.get_view_scale()
            wx = (e.x() - self.offset_x) / scale
            wy = (e.y() - self.offset_y) / scale

            obj = self.pm.selected_object
            cx, cy = obj.get_center()

            current_angle = self._angle_to_mouse(cx, cy, wx, wy)
            delta = current_angle - self.rotate_start_angle

            Transform.rotate(obj, delta)
            obj.rotation = (self.initial_rotation + delta) % 360

            self.update()
            return

        if self.is_drawing:
            self.update()
            return

        if self.is_moving and self.pm.selected_object:
            dx = wx - self.drag_start_x
            dy = wy - self.drag_start_y
            self.pm.translate_selected(dx, dy)
            self.drag_start_x = wx
            self.drag_start_y = wy
            self.update()
    #MODIFICARE ROTIRE
    def mouseReleaseEvent(self, e):
        scale = self.pm.get_view_scale()
        if e.button() == Qt.RightButton:
            self.is_rotating = False
            self.project_changed_signal.emit()
            self.update()
            return
        if e.button() == Qt.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
            return

        if e.button() != Qt.LeftButton:
            return

        wx = (e.x() - self.offset_x) / scale
        wy = (e.y() - self.offset_y) / scale

        # FINISH MOVE
        if self.is_moving:
            self.is_moving = False

            # FIX CRUCIAL – PREVINE DESENAREA DUPĂ MUTARE
            self.is_drawing = False
            self.current_tool = None

            self.project_changed_signal.emit()
            self.update()
            return

        # FINISH DRAW
        if self.is_drawing and self.current_tool:
            self.is_drawing = False

            sx = self.start_x
            sy = self.start_y
            ex = wx
            ey = wy

            if self.pm.current_project and self.pm.current_project.snap_to_grid:
                ex, ey = self.pm.coordinate_system.snap_to_grid(ex, ey)

            if self.current_tool == "wall":
                self.pm.add_wall(sx, sy, ex, ey)
                self.status_message_signal.emit("Perete adăugat")
            elif self.current_tool == "door":
                self.pm.add_door(min(sx, ex), min(sy, ey), abs(ex - sx), abs(ey - sy))
                self.status_message_signal.emit("Ușă adăugată")
            elif self.current_tool == "window":
                self.pm.add_window(min(sx, ex), min(sy, ey), abs(ex - sx), abs(ey - sy))
                self.status_message_signal.emit("Fereastră adăugată")
            elif self.current_tool == "furniture":
                self.pm.add_furniture(min(sx, ex), min(sy, ey), abs(ex - sx), abs(ey - sy), "mobilier")
                self.status_message_signal.emit("Mobilier adăugat")

            self.project_changed_signal.emit()
            self.update()

    # =============================== WHEEL ==============================

    def wheelEvent(self, e):
        # Ctrl + scroll = zoom
        if not (e.modifiers() & Qt.ControlModifier):
            e.ignore()
            return

        scale = self.pm.get_view_scale()
        cx = e.x()
        cy = e.y()

        wx = (cx - self.offset_x) / scale
        wy = (cy - self.offset_y) / scale

        factor = 1.1 if e.angleDelta().y() > 0 else 0.9
        new_scale = max(0.1, min(10.0, scale * factor))

        self.pm.set_view_scale(new_scale)

        self.offset_x = cx - wx * new_scale
        self.offset_y = cy - wy * new_scale

        self.status_message_signal.emit(f"Zoom: {new_scale:.2f}x")
        self.update()

#=================================Rotire=========================

    def _angle_to_mouse(self, cx, cy, mx, my):
        dx = mx - cx
        dy = my - cy
        return math.degrees(math.atan2(dy, dx))

# =====================================================================
# WORKPAGE
# =====================================================================

class WorkPage(Page):

    # -------------------------- Undo / Redo ---------------------------

    def undo(self):
        if self.pm.undo():
            self.canvas.update()
            self.refresh_statistics()
            self.lbl_status.setText("Undo realizat")
        else:
            self.lbl_status.setText("Nu există acțiuni pentru undo")

    def redo(self):
        if self.pm.redo():
            self.canvas.update()
            self.refresh_statistics()
            self.lbl_status.setText("Redo realizat")
        else:
            self.lbl_status.setText("Nu există acțiuni pentru redo")

    # ----------------------------- INIT UI ----------------------------

    def init_ui(self):
        self.pm = ProjectManager()
        if not self.pm.current_project:
            self.pm.create_new_project("Proiect Nou")

        main = QVBoxLayout()
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self.create_header())

        content = QHBoxLayout()
        content.setSpacing(0)

        content.addWidget(self.create_toolbar())

        canvas_holder = QWidget()
        ch_layout = QVBoxLayout()
        ch_layout.setContentsMargins(10, 10, 10, 10)

        self.canvas = SimpleCanvas(self)
        ch_layout.addWidget(self.canvas)

        canvas_holder.setLayout(ch_layout)
        content.addWidget(canvas_holder, 1)

        content.addWidget(self.create_right_panel())

        main.addLayout(content, 1)
        main.addWidget(self.create_footer())

        self.setLayout(main)

        # Conexiuni semnale
        self.canvas.status_message_signal.connect(self.lbl_status.setText)
        self.canvas.mouse_moved_signal.connect(self.update_mouse_position)
        self.canvas.project_changed_signal.connect(self.refresh_statistics)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self.redo)

        # Timer pentru refresh statisitici (optional)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_statistics)
        self.refresh_timer.start(1000)
    #MODIFICARE PT ROTIRE
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.deselect_all)

        self.refresh_statistics()

    # ----------------------------- HEADER -----------------------------

    def create_header(self):
        w = QWidget()
        w.setStyleSheet("""
            QWidget { background-color: #03254C; padding: 8px; }
            QPushButton {
                background-color: #185E8A;
                color: white;
                border: none;
                padding: 6px 14px;
                border-radius: 4px;
                margin: 0 4px;
            }
            QPushButton:hover { background-color: #2679AE; }
            QLabel { color: white; font-size: 18px; font-weight: bold; }
        """)

        h = QHBoxLayout()

        h.addWidget(QLabel("Floor Plan Architecture - Workspace"))
        h.addStretch()

        btn_new = QPushButton("Nou")
        btn_new.clicked.connect(self.new_project)
        h.addWidget(btn_new)

        btn_save = QPushButton("Salvează")
        btn_save.clicked.connect(self.save_project)
        h.addWidget(btn_save)

        btn_load = QPushButton("Deschide")
        btn_load.clicked.connect(self.load_project)
        h.addWidget(btn_load)

        btn_menu = QPushButton("Meniu")
        btn_menu.clicked.connect(lambda: self.dashboard.update_page("main"))
        h.addWidget(btn_menu)

        w.setLayout(h)
        return w

    # ----------------------------- TOOLBAR ----------------------------

    def create_toolbar(self):
        w = QWidget()
        w.setFixedWidth(200)
        w.setStyleSheet("""
            QWidget { background-color: #F7F3E8; padding: 10px; }
            QPushButton {
                background-color: #008080;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                margin: 4px 0;
                text-align: left;
            }
            QPushButton:hover { background-color: #009999; }
            QPushButton:checked { background-color: #FF6F61; }
            QGroupBox {
                border: 2px solid #D1C4A5;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
        """)

        v = QVBoxLayout()
        v.setAlignment(Qt.AlignTop)

        # Tools
        tools = QGroupBox("Unelte desenare")
        tl = QVBoxLayout()

        self.btn_wall = QPushButton("Perete")
        self.btn_wall.setCheckable(True)
        self.btn_wall.clicked.connect(lambda: self.select_tool("wall"))
        tl.addWidget(self.btn_wall)

        self.btn_door = QPushButton("Ușă")
        self.btn_door.setCheckable(True)
        self.btn_door.clicked.connect(lambda: self.select_tool("door"))
        tl.addWidget(self.btn_door)

        self.btn_window = QPushButton("Fereastră")
        self.btn_window.setCheckable(True)
        self.btn_window.clicked.connect(lambda: self.select_tool("window"))
        tl.addWidget(self.btn_window)

        self.btn_furniture = QPushButton("Mobilier")
        self.btn_furniture.setCheckable(True)
        self.btn_furniture.clicked.connect(lambda: self.select_tool("furniture"))
        tl.addWidget(self.btn_furniture)

        tools.setLayout(tl)
        v.addWidget(tools)

        # Grid settings
        grid = QGroupBox("Setări grilă")
        gl = QVBoxLayout()

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Dimensiune:"))
        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(5, 100)
        if self.pm.current_project:
            self.grid_size_spin.setValue(self.pm.current_project.grid_size)
        self.grid_size_spin.valueChanged.connect(self.change_grid_size)
        size_row.addWidget(self.grid_size_spin)
        gl.addLayout(size_row)

        self.grid_visible_check = QCheckBox("Afișează grila")
        self.grid_visible_check.setChecked(
            self.pm.current_project.grid_visible if self.pm.current_project else True
        )
        self.grid_visible_check.stateChanged.connect(self.toggle_grid_visibility)
        gl.addWidget(self.grid_visible_check)

        self.snap_check = QCheckBox("Snap to grid")
        self.snap_check.setChecked(
            self.pm.current_project.snap_to_grid if self.pm.current_project else True
        )
        self.snap_check.stateChanged.connect(self.toggle_snap_to_grid)
        gl.addWidget(self.snap_check)

        grid.setLayout(gl)
        v.addWidget(grid)

        # Clear
        btn_clear = QPushButton("Șterge tot")
        btn_clear.setStyleSheet("background-color: #E74C3C;")
        btn_clear.clicked.connect(self.clear_all)
        v.addWidget(btn_clear)

        v.addStretch()
        w.setLayout(v)
        return w

    # -------------------------- RIGHT PANEL ---------------------------

    def create_right_panel(self):
        w = QWidget()
        w.setFixedWidth(260)
        w.setStyleSheet("""
            QWidget { background-color: #FEFCF3; padding: 10px; }
            QGroupBox {
                border: 2px solid #D1C4A5;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QLabel { padding: 2px; }
        """)

        v = QVBoxLayout()
        v.setAlignment(Qt.AlignTop)

        # Stats
        stats = QGroupBox("Statistici proiect")
        sv = QVBoxLayout()

        self.lbl_project_name = QLabel("Proiect: -")
        self.lbl_total_objects = QLabel("Total obiecte: 0")
        self.lbl_walls = QLabel("Pereți: 0")
        self.lbl_doors = QLabel("Uși: 0")
        self.lbl_windows = QLabel("Ferestre: 0")
        self.lbl_furniture = QLabel("Mobilier: 0")
        self.lbl_wall_length = QLabel("Lungime pereți: 0")

        for lab in [
            self.lbl_project_name, self.lbl_total_objects, self.lbl_walls,
            self.lbl_doors, self.lbl_windows, self.lbl_furniture, self.lbl_wall_length
        ]:
            sv.addWidget(lab)

        stats.setLayout(sv)
        v.addWidget(stats)

        # Grid / canvas info
        info = QGroupBox("Canvas / Grilă")
        iv = QVBoxLayout()

        self.lbl_grid_size = QLabel("Grilă: -")
        self.lbl_snap = QLabel("Snap: -")
        self.lbl_canvas_size = QLabel("Dimensiune canvas: -")
        self.lbl_conversion = QLabel("Conversie: -")

        iv.addWidget(self.lbl_grid_size)
        iv.addWidget(self.lbl_snap)
        iv.addWidget(self.lbl_canvas_size)
        iv.addWidget(self.lbl_conversion)

        info.setLayout(iv)
        v.addWidget(info)

        v.addStretch()
        w.setLayout(v)
        return w

    # ------------------------------ FOOTER -----------------------------

    def create_footer(self):
        w = QWidget()
        w.setStyleSheet("""
            QWidget { background-color: #185E8A; padding: 6px 10px; }
            QLabel { color: white; font-size: 12px; }
        """)

        h = QHBoxLayout()
        self.lbl_status = QLabel("Gata | Selectează o unealtă")
        h.addWidget(self.lbl_status)
        h.addStretch()

        w.setLayout(h)
        return w
#MODIFICARE PT ROTIRE
    def deselect_all(self):
        # deselectăm obiect
        self.pm.select_object(None)

        # deselectăm toate uneltele
        for b in [self.btn_wall, self.btn_door, self.btn_window, self.btn_furniture]:
            b.setChecked(False)

        # anulăm tool-ul curent
        self.canvas.current_tool = None

        self.lbl_status.setText("Gata | Nimic selectat")
        self.canvas.update()

    # ----------------------- TOOLBAR / GRID LOGIC ----------------------

    def select_tool(self, tool: str):
        for b in [self.btn_wall, self.btn_door, self.btn_window, self.btn_furniture]:
            b.setChecked(False)

        if tool == "wall":
            self.btn_wall.setChecked(True)
            self.lbl_status.setText("Perete: click & drag pentru desenare")
        elif tool == "door":
            self.btn_door.setChecked(True)
            self.lbl_status.setText("Ușă: click & drag pentru desenare")
        elif tool == "window":
            self.btn_window.setChecked(True)
            self.lbl_status.setText("Fereastră: click & drag pentru desenare")
        elif tool == "furniture":
            self.btn_furniture.setChecked(True)
            self.lbl_status.setText("Mobilier: click & drag pentru desenare")

        self.canvas.current_tool = tool

    def change_grid_size(self, value: int):
        if self.pm.current_project:
            self.pm.current_project.grid_size = value
        # dacă CoordinateSystem are set_grid_size, îl folosim
        if hasattr(self.pm.coordinate_system, "set_grid_size"):
            self.pm.coordinate_system.set_grid_size(value)

        self.canvas.update()
        self.refresh_statistics()

    def toggle_grid_visibility(self):
        if self.pm.current_project:
            self.pm.current_project.grid_visible = bool(self.grid_visible_check.isChecked())
        self.canvas.update()
        self.refresh_statistics()

    def toggle_snap_to_grid(self):
        if self.pm.current_project:
            self.pm.current_project.snap_to_grid = bool(self.snap_check.isChecked())
        self.refresh_statistics()

    # ---------------------------- PROJECT OPS --------------------------

    def clear_all(self):
        if not self.pm.current_project:
            return

        reply = QMessageBox.question(
            self, "Confirmare",
            "Sigur dorești să ștergi toate obiectele?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # curățăm tot
        self.pm.current_project.clear()
        self.pm._clear_cache()
        # punem stare nouă în istoric
        self.pm._push_history()

        self.canvas.update()
        self.refresh_statistics()
        self.lbl_status.setText("Toate obiectele au fost șterse")

    def new_project(self):
        self.pm.create_new_project("Proiect Nou")
        self.canvas.update()
        self.refresh_statistics()
        self.lbl_status.setText("Proiect nou creat")

    def save_project(self):
        fname, _ = QFileDialog.getSaveFileName(
            self, "Salvează proiect", "", "JSON Files (*.json)"
        )
        if not fname:
            return

        if self.pm.save_project(fname):
            QMessageBox.information(self, "Succes", f"Proiect salvat: {fname}")
            self.lbl_status.setText(f"Proiect salvat: {fname}")
        else:
            QMessageBox.warning(self, "Eroare", "Nu s-a putut salva proiectul")

    def load_project(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Deschide proiect", "", "JSON Files (*.json)"
        )
        if not fname:
            return

        if self.pm.load_project(fname):
            self.canvas.update()
            self.refresh_statistics()
            QMessageBox.information(self, "Succes", f"Proiect încărcat: {fname}")
            self.lbl_status.setText(f"Proiect încărcat: {fname}")
        else:
            QMessageBox.warning(self, "Eroare", "Nu s-a putut încărca proiectul")

    # ----------------------------- UI UPDATE ---------------------------

    def update_mouse_position(self, x: int, y: int):
        # nu stricăm statusul dacă e ceva important acolo, doar îl completăm:
        self.lbl_status.setText(f"Mouse: ({x}, {y})")

    def refresh_statistics(self):
        st = self.pm.get_statistics()
        if not st:
            return

        self.lbl_project_name.setText(f"Proiect: {st['project_name']}")
        self.lbl_total_objects.setText(f"Total obiecte: {st['total_objects']}")
        self.lbl_walls.setText(f"Pereți: {st['walls_count']}")
        self.lbl_doors.setText(f"Uși: {st['doors_count']}")
        self.lbl_windows.setText(f"Ferestre: {st['windows_count']}")
        self.lbl_furniture.setText(f"Mobilier: {st['furniture_count']}")
        self.lbl_wall_length.setText(f"Lungime pereți: {st['total_wall_length']}")

        self.lbl_grid_size.setText(f"Grilă: {st['grid_size']} px")
        self.lbl_snap.setText(f"Snap: {'Activ' if st['snap_to_grid'] else 'Inactiv'}")
        self.lbl_canvas_size.setText(
            f"Dimensiune canvas: {st['canvas_width']} x {st['canvas_height']}"
        )

        # conversie px -> cm dacă există metoda în CoordinateSystem
        if hasattr(self.pm.coordinate_system, "get_grid_spacing_cm"):
            cm = self.pm.coordinate_system.get_grid_spacing_cm()
            self.lbl_conversion.setText(f"{st['grid_size']} px = {cm:.1f} cm")
        else:
            self.lbl_conversion.setText("Conversie: nedefinită")

        sel = self.pm.selected_object
        if sel and not self.canvas.current_tool:
            self.lbl_status.setText(
                f"Obiect selectat: {type(sel).__name__} la ({sel.x:.0f}, {sel.y:.0f})"
            )
        elif not self.canvas.current_tool:
            self.lbl_status.setText("Gata | Selectează o unealtă sau un obiect")

