import math
import os
import sys

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
    QMessageBox, QFileDialog, QSpinBox, QCheckBox, QShortcut, QToolBox,
    QListWidget, QListWidgetItem, QSplitter, QAbstractItemView
)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QKeySequence, QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPointF, QSize, QRectF

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from .Page import Page

try:
    from Business.ProjectManager import ProjectManager
    from Business.ArchitecturalObjects import SvgFurnitureObject, Wall, Window
except ImportError:
    from ProjectManager import ProjectManager
    from ArchitecturalObjects import SvgFurnitureObject, Wall, Window

class SimpleCanvas(QWidget):
    mouse_moved_signal = pyqtSignal(int, int)
    project_changed_signal = pyqtSignal()
    status_message_signal = pyqtSignal(str)
    object_selected_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pm = ProjectManager()
        self.objects = []
        self.offset_x = 0
        self.offset_y = 0
        self.zoom_scale = 1.0
        self.current_tool_mode = None
        self.current_svg_path = None
        self.selected_object = None
        self.is_panning = False
        self.last_pan_x = 0
        self.last_pan_y = 0
        self.is_drawing_wall = False
        self.wall_start_pt = None
        self.wall_temp_end = None
        self.is_moving = False
        self.is_rotating = False
        self.drag_start_pos = QPointF()
        self.obj_start_pos = QPointF()
        self.wall_coords_start = None
        self.rotate_start_angle = 0
        self.initial_rotation = 0
        self.grid_visible = True
        self.snap_to_grid = True
        self.grid_size = 20

        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("background-color: white;")

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.white)
        painter.translate(self.offset_x, self.offset_y)
        painter.scale(self.zoom_scale, self.zoom_scale)

        if self.grid_visible:
            self.draw_grid(painter)

        for obj in self.objects:
            if isinstance(obj, Wall):
                self.draw_wall(painter, obj)

        for obj in self.objects:
            if isinstance(obj, Window):
                self.draw_window(painter, obj)
            elif isinstance(obj, SvgFurnitureObject):
                obj.draw(painter)

        if self.is_drawing_wall and self.wall_start_pt and self.wall_temp_end:
            pen = QPen(QColor(80, 80, 80), 8)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(self.wall_start_pt, self.wall_temp_end)

    def draw_grid(self, painter):
        pen = QPen(QColor(240, 240, 240))
        pen.setWidth(1)
        painter.setPen(pen)
        start, end, step = -3000, 6000, self.grid_size
        for x in range(start, end, step): painter.drawLine(x, start, x, end)
        for y in range(start, end, step): painter.drawLine(start, y, end, y)

    def draw_wall(self, painter, wall):
        color = QColor(64, 64, 64)
        if wall.is_selected: color = Qt.red
        pen = QPen(color, wall.thickness)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(int(wall.x1), int(wall.y1), int(wall.x2), int(wall.y2))

    def draw_window(self, painter, win):
        painter.save()
        center = QPointF(win.x + win.width / 2, win.y + win.height / 2)
        painter.translate(center)
        painter.rotate(win.rotation)
        painter.translate(-center)
        rect = QRectF(win.x, win.y, win.width, win.height)
        painter.setBrush(QBrush(QColor(173, 216, 230, 200)))
        painter.setPen(QPen(Qt.red if win.is_selected else Qt.blue, 2))
        painter.drawRect(rect)
        painter.drawLine(QPointF(win.x, win.y + win.height / 2),
                         QPointF(win.x + win.width, win.y + win.height / 2))
        painter.restore()

    def mousePressEvent(self, e):
        if e.button() == Qt.MiddleButton:
            self.is_panning = True
            self.last_pan_x, self.last_pan_y = e.x(), e.y()
            self.setCursor(Qt.ClosedHandCursor)
            return
        wx = (e.x() - self.offset_x) / self.zoom_scale
        wy = (e.y() - self.offset_y) / self.zoom_scale
        if self.snap_to_grid:
            wx = round(wx / self.grid_size) * self.grid_size
            wy = round(wy / self.grid_size) * self.grid_size
        pos_pt = QPointF(wx, wy)

        if e.button() == Qt.RightButton and self.selected_object:
            if not isinstance(self.selected_object, Wall):
                self.is_rotating = True
                rect = self.selected_object.rect
                self.rotate_start_angle = self._angle_to_mouse(rect.center().x(), rect.center().y(), wx, wy)
                self.initial_rotation = self.selected_object.rotation
                return

        if e.button() == Qt.LeftButton:
            if self.current_tool_mode == "wall":
                self.is_drawing_wall = True
                self.wall_start_pt = pos_pt
                self.wall_temp_end = pos_pt
                return
            if self.current_tool_mode in ["window", "svg_placement"]:
                self.place_object_at(wx, wy)
                return

            clicked_obj = None
            for obj in reversed(self.objects):
                if isinstance(obj, Wall):
                    if self.dist_to_segment(pos_pt, obj) < obj.thickness / 2 + 5:
                        clicked_obj = obj
                        break
                elif isinstance(obj, (Window, SvgFurnitureObject)):
                    # === FIX AICI: Folosim rect.contains în loc de obj.contains ===
                    if obj.rect.contains(pos_pt):
                        clicked_obj = obj
                        break

            self.select_object(clicked_obj)
            if clicked_obj:
                self.is_moving = True
                self.drag_start_pos = pos_pt
                if isinstance(clicked_obj, Wall):
                    self.wall_coords_start = (clicked_obj.x1, clicked_obj.y1, clicked_obj.x2, clicked_obj.y2)
                else:
                    self.obj_start_pos = QPointF(clicked_obj.x, clicked_obj.y)
            self.update()

    def mouseMoveEvent(self, e):
        wx = (e.x() - self.offset_x) / self.zoom_scale
        wy = (e.y() - self.offset_y) / self.zoom_scale
        self.mouse_moved_signal.emit(int(wx), int(wy))
        if self.is_panning:
            self.offset_x += e.x() - self.last_pan_x
            self.offset_y += e.y() - self.last_pan_y
            self.last_pan_x, self.last_pan_y = e.x(), e.y()
            self.update()
            return
        if self.snap_to_grid:
            wx = round(wx / self.grid_size) * self.grid_size
            wy = round(wy / self.grid_size) * self.grid_size
        if self.is_drawing_wall:
            self.wall_temp_end = QPointF(wx, wy)
            self.update()
            return
        if self.is_moving and self.selected_object:
            dx = wx - self.drag_start_pos.x()
            dy = wy - self.drag_start_pos.y()
            if isinstance(self.selected_object, Wall):
                ox1, oy1, ox2, oy2 = self.wall_coords_start
                self.selected_object.x1 = ox1 + dx
                self.selected_object.y1 = oy1 + dy
                self.selected_object.x2 = ox2 + dx
                self.selected_object.y2 = oy2 + dy
            else:
                self.selected_object.x = self.obj_start_pos.x() + dx
                self.selected_object.y = self.obj_start_pos.y() + dy
            self.object_selected_signal.emit(self.selected_object)
            self.update()
            return
        if self.is_rotating and self.selected_object:
            rect = self.selected_object.rect
            curr_angle = self._angle_to_mouse(rect.center().x(), rect.center().y(), wx, wy)
            self.selected_object.rotation = (self.initial_rotation + curr_angle - self.rotate_start_angle) % 360
            self.object_selected_signal.emit(self.selected_object)
            self.update()

    def mouseReleaseEvent(self, e):
        if self.is_drawing_wall and self.current_tool_mode == "wall":
            self.is_drawing_wall = False
            if self.wall_start_pt != self.wall_temp_end:
                new_wall = Wall(self.wall_start_pt.x(), self.wall_start_pt.y(),
                                self.wall_temp_end.x(), self.wall_temp_end.y())
                self.objects.append(new_wall)
                self.select_object(new_wall)
                self.project_changed_signal.emit()
            self.update()
        if e.button() == Qt.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
        self.is_moving = False
        self.is_rotating = False

    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            old_wx = (e.x() - self.offset_x) / self.zoom_scale
            old_wy = (e.y() - self.offset_y) / self.zoom_scale
            factor = 1.1 if e.angleDelta().y() > 0 else 0.9
            self.zoom_scale = max(0.1, min(5.0, self.zoom_scale * factor))
            self.offset_x = e.x() - old_wx * self.zoom_scale
            self.offset_y = e.y() - old_wy * self.zoom_scale
            self.status_message_signal.emit(f"Zoom: {int(self.zoom_scale * 100)}%")
            self.update()
        else:
            super().wheelEvent(e)

    def set_tool_wall(self):
        self.current_tool_mode = "wall"
        self.select_object(None)
        self.setCursor(Qt.CrossCursor)
        self.status_message_signal.emit("Unealta Perete: Click si trage.")

    def set_tool_window(self):
        self.current_tool_mode = "window"
        self.select_object(None)
        self.setCursor(Qt.CrossCursor)
        self.status_message_signal.emit("Unealta Fereastră: Click pentru a plasa.")

    def set_tool_svg(self, path):
        self.current_tool_mode = "svg_placement"
        self.current_svg_path = path
        self.select_object(None)
        self.setCursor(Qt.CrossCursor)
        self.status_message_signal.emit("Unealta Mobilier: Click pentru a plasa.")

    def place_object_at(self, x, y):
        new_obj = None
        if self.current_tool_mode == "window":
            new_obj = Window(x - 50, y - 7, 100, 15)
        elif self.current_tool_mode == "svg_placement" and self.current_svg_path:
            new_obj = SvgFurnitureObject(self.current_svg_path, x=x, y=y)
            new_obj.move_to(QPointF(x, y))

        if new_obj:
            self.objects.append(new_obj)
            self.select_object(new_obj)
            self.project_changed_signal.emit()
            if self.current_tool_mode == "svg_placement":
                self.current_tool_mode = None
                self.setCursor(Qt.ArrowCursor)
            self.update()

    def select_object(self, obj):
        for o in self.objects: o.is_selected = False
        self.selected_object = obj
        if obj: obj.is_selected = True
        self.object_selected_signal.emit(obj)
        self.update()

    def dist_to_segment(self, p, wall):
        x, y = p.x(), p.y()
        x1, y1, x2, y2 = wall.x1, wall.y1, wall.x2, wall.y2
        A = x - x1;
        B = y - y1;
        C = x2 - x1;
        D = y2 - y1
        dot = A * C + B * D
        len_sq = C * C + D * D
        param = -1
        if len_sq != 0: param = dot / len_sq
        if param < 0:
            xx, yy = x1, y1
        elif param > 1:
            xx, yy = x2, y2
        else:
            xx, yy = x1 + param * C, y1 + param * D
        return math.sqrt((x - xx) ** 2 + (y - yy) ** 2)

    def _angle_to_mouse(self, cx, cy, mx, my):
        return math.degrees(math.atan2(my - cy, mx - cx))

    def delete_selection(self):
        if self.selected_object and self.selected_object in self.objects:
            self.objects.remove(self.selected_object)
            self.select_object(None)
            self.project_changed_signal.emit()
            self.update()

    def clear_scene(self):
        self.objects.clear()
        self.select_object(None)
        self.project_changed_signal.emit()
        self.update()

class WorkPage(Page):
    def init_ui(self):
        self.pm = ProjectManager()
        if not self.pm.current_project:
            self.pm.create_new_project("Proiect Hibrid")

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self.create_header())

        content = QHBoxLayout()
        content.setSpacing(0)

        self.canvas = SimpleCanvas(self)

        # Meniu Stanga
        content.addWidget(self.create_left_panel())

        # Canvas
        canvas_container = QWidget()
        cl = QVBoxLayout(canvas_container)
        cl.setContentsMargins(5, 5, 5, 5)
        cl.addWidget(self.canvas)
        content.addWidget(canvas_container, 1)

        # Meniu Dreapta
        content.addWidget(self.create_right_panel())

        main.addLayout(content, 1)
        main.addWidget(self.create_footer())

        self.canvas.status_message_signal.connect(self.lbl_status.setText)
        self.canvas.project_changed_signal.connect(self.refresh_stats)
        self.canvas.object_selected_signal.connect(self.update_properties)
        self.canvas.mouse_moved_signal.connect(lambda x, y: None)

        QShortcut(QKeySequence("Delete"), self).activated.connect(self.canvas.delete_selection)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.action_cancel)

    def create_header(self):
        w = QWidget()
        w.setStyleSheet("background-color: #03254C; color: white; padding: 5px;")
        h = QHBoxLayout(w)
        h.addWidget(QLabel("<b>Architect App</b>"))
        h.addStretch()
        btn_save = QPushButton("💾 Salvează")
        btn_save.setStyleSheet("border:none; background:#185E8A; padding:5px; border-radius:3px;")
        btn_save.clicked.connect(self.save_project)
        h.addWidget(btn_save)
        btn_load = QPushButton("📂 Deschide")
        btn_load.setStyleSheet("border:none; background:#185E8A; padding:5px; border-radius:3px;")
        btn_load.clicked.connect(self.load_project)
        h.addWidget(btn_load)
        btn_back = QPushButton("🏠 Meniu")
        btn_back.setStyleSheet("border:none; background:#185E8A; padding:5px; border-radius:3px;")
        btn_back.clicked.connect(lambda: self.dashboard.update_page("main"))
        h.addWidget(btn_back)
        return w

    def create_left_panel(self):
        w = QWidget()
        w.setFixedWidth(250)
        w.setStyleSheet("background-color: #F7F3E8;")
        v = QVBoxLayout(w)
        v.setContentsMargins(5, 10, 5, 5)

        gb_view = QGroupBox("Vizualizare")
        v_view = QVBoxLayout(gb_view)
        self.chk_grid = QCheckBox("Arată Grila")
        self.chk_grid.setChecked(True)
        self.chk_grid.toggled.connect(lambda v: setattr(self.canvas, 'grid_visible', v) or self.canvas.update())
        v_view.addWidget(self.chk_grid)
        self.chk_snap = QCheckBox("Snap to Grid")
        self.chk_snap.setChecked(True)
        self.chk_snap.toggled.connect(lambda v: setattr(self.canvas, 'snap_to_grid', v))
        v_view.addWidget(self.chk_snap)
        v.addWidget(gb_view)

        # Toolbox Principal
        self.toolbox = QToolBox()
        self.toolbox.setStyleSheet("""
            QToolBox::tab { background: #E0D8C0; border: 1px solid #aaa; border-radius: 2px; color: black; font-weight: bold; }
            QListWidget { border: none; background: #F7F3E8; }
        """)

        # 1. Structura
        list_struct = QListWidget()
        list_struct.setIconSize(QSize(32, 32))
        item_wall = QListWidgetItem("Perete (Linie)")
        item_wall.setData(Qt.UserRole, "CMD_WALL")
        list_struct.addItem(item_wall)
        item_win = QListWidgetItem("Fereastră (Albastru)")
        item_win.setData(Qt.UserRole, "CMD_WINDOW")
        list_struct.addItem(item_win)
        list_struct.itemClicked.connect(self.on_menu_item_clicked)
        self.toolbox.addItem(list_struct, "Structură")

        # doors si furniture
        self.load_assets_structured()

        v.addWidget(self.toolbox)

        btn_clear = QPushButton("Sterge Tot")
        btn_clear.setStyleSheet("background: #E74C3C; color: white; padding: 5px;")
        btn_clear.clicked.connect(self.canvas.clear_scene)
        v.addWidget(btn_clear)
        return w

    def load_assets_structured(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)

        possible_paths = [
            os.path.join(root_dir, "resources", "assets"),
            os.path.join(current_dir, "resources", "assets")
        ]
        assets_dir = None
        for p in possible_paths:
            if os.path.exists(p):
                assets_dir = p
                break

        if not assets_dir:
            print("Assets folder not found.")
            return

        # 1 Usi
        doors_path = os.path.join(assets_dir, "doors")
        if os.path.exists(doors_path):
            self.add_grid_category("Uși", doors_path)

        # 2 Mobilier
        furn_path = os.path.join(assets_dir, "furniture")
        if os.path.exists(furn_path):
            subfolders = sorted([d for d in os.listdir(furn_path) if os.path.isdir(os.path.join(furn_path, d))])
            for folder_name in subfolders:
                full_path = os.path.join(furn_path, folder_name)
                self.add_grid_category(folder_name.capitalize(), full_path)

    def add_grid_category(self, title, path):
        list_w = QListWidget()

        list_w.setViewMode(QListWidget.IconMode)
        list_w.setResizeMode(QListWidget.Adjust)
        list_w.setIconSize(QSize(65, 65))
        list_w.setSpacing(10)
        list_w.setMovement(QListWidget.Static)
        list_w.setWordWrap(True)

        list_w.itemClicked.connect(self.on_menu_item_clicked)

        try:
            files = sorted([f for f in os.listdir(path) if f.lower().endswith(('.svg', '.png'))])
            for f in files:
                clean_name = os.path.splitext(f)[0].replace('AdobeStock_', '').replace('_', ' ').title()

                if len(clean_name) > 15:
                    clean_name = clean_name[:12] + "..."

                item = QListWidgetItem(clean_name)
                full_path = os.path.join(path, f)
                item.setData(Qt.UserRole, full_path)

                item.setToolTip(os.path.splitext(f)[0].replace('_', ' ').title())

                pix = QPixmap(full_path)
                if not pix.isNull():
                    item.setIcon(QIcon(pix))

                list_w.addItem(item)

            if list_w.count() > 0:
                self.toolbox.addItem(list_w, title)
        except Exception as e:
            print(f"Error loading category {title}: {e}")

    def on_menu_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data == "CMD_WALL":
            self.canvas.set_tool_wall()
        elif data == "CMD_WINDOW":
            self.canvas.set_tool_window()
        elif data:
            self.canvas.set_tool_svg(data)

    def create_right_panel(self):
        w = QWidget()
        w.setFixedWidth(240)
        w.setStyleSheet("background-color: #FEFCF3; border-left: 1px solid #ccc;")
        v = QVBoxLayout(w)
        self.gb_props = QGroupBox("Proprietăți")
        vp = QVBoxLayout(self.gb_props)
        self.lbl_name = QLabel("Nume: -")
        vp.addWidget(self.lbl_name)
        vp.addWidget(QLabel("Rotatie:"))
        self.spin_rot = QSpinBox()
        self.spin_rot.setRange(0, 360)
        self.spin_rot.setSingleStep(45)
        self.spin_rot.valueChanged.connect(self.on_rotation_changed)
        vp.addWidget(self.spin_rot)
        self.gb_props.setEnabled(False)
        v.addWidget(self.gb_props)
        v.addStretch()
        return w

    def on_rotation_changed(self, val):
        obj = self.canvas.selected_object
        if obj and not isinstance(obj, Wall):
            obj.rotation = val
            self.canvas.update()

    def create_footer(self):
        w = QWidget()
        w.setStyleSheet("background:#185E8A; color:white;")
        h = QHBoxLayout(w)
        self.lbl_status = QLabel("Gata.")
        h.addWidget(self.lbl_status)
        return w

    def refresh_stats(self):
        pass

    def update_properties(self, obj):
        if obj:
            self.gb_props.setEnabled(True)
            self.spin_rot.blockSignals(True)
            if isinstance(obj, Wall):
                self.lbl_name.setText("Perete")
                self.spin_rot.setEnabled(False)
                self.spin_rot.setValue(0)
            elif isinstance(obj, Window):
                self.lbl_name.setText("Fereastră")
                self.spin_rot.setEnabled(True)
                self.spin_rot.setValue(int(obj.rotation))
            else:
                self.lbl_name.setText(getattr(obj, 'name', 'Obiect'))
                self.spin_rot.setEnabled(True)
                self.spin_rot.setValue(int(obj.rotation))
            self.spin_rot.blockSignals(False)
        else:
            self.gb_props.setEnabled(False)
            self.lbl_name.setText("-")

    def action_cancel(self):
        self.canvas.current_tool_mode = None
        self.canvas.select_object(None)
        self.lbl_status.setText("Anulat.")
        self.canvas.setCursor(Qt.ArrowCursor)

    def save_project(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Salveaza", "", "JSON (*.json)")
        if fname:
            if self.pm.save_project(fname, self.canvas.objects):
                QMessageBox.information(self, "Succes", "Salvat cu succes!")
            else:
                QMessageBox.warning(self, "Eroare", "Nu s-a putut salva.")

    def load_project(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Deschide", "", "JSON (*.json)")
        if fname:
            objs = self.pm.load_project(fname)
            if objs is not None:
                self.canvas.objects = objs
                self.canvas.update()
                QMessageBox.information(self, "Succes", "Incarcat cu succes!")