import math
import os
import sys

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
    QMessageBox, QFileDialog, QSpinBox, QCheckBox, QShortcut, QToolBox,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QKeySequence, QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QSize, QRectF, QMarginsF

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from .Page import Page

try:
    from Business.ProjectManager import ProjectManager
    from Business.ArchitecturalObjects import SvgFurnitureObject, Wall, Window, RoomFloor
    from Business.CollisionDetector import CollisionDetector
except ImportError:
    from ProjectManager import ProjectManager
    from ArchitecturalObjects import SvgFurnitureObject, Wall, Window
    try:
        from ArchitecturalObjects import RoomFloor
    except Exception:
        RoomFloor = None
    from CollisionDetector import CollisionDetector


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

        self.is_drawing_floor = False
        self.floor_start_pt = None
        self.floor_temp_rect = None

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

        if RoomFloor is not None:
            for obj in self.objects:
                if isinstance(obj, RoomFloor):
                    self.draw_room_floor(painter, obj)

            if self.is_drawing_floor and self.floor_temp_rect:
                painter.save()
                painter.setBrush(QBrush(QColor(100, 200, 100, 100)))
                painter.setPen(QPen(Qt.black, 1, Qt.DashLine))
                painter.drawRect(self.floor_temp_rect)
                painter.restore()

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
        for x in range(start, end, step):
            painter.drawLine(x, start, x, end)
        for y in range(start, end, step):
            painter.drawLine(start, y, end, y)

    def draw_room_floor(self, painter, floor):
        rect = floor.rect
        base_color = getattr(floor, "color", QColor(100, 200, 100, 120))
        if getattr(floor, "is_selected", False):
            base_color = QColor(255, 200, 200, 150)

        painter.save()
        painter.setBrush(QBrush(base_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(rect)

        area_m2 = getattr(floor, "area_m2", None)
        if area_m2 is not None:
            painter.setPen(QPen(Qt.black))
            f = QFont("Arial", 10)
            f.setBold(True)
            painter.setFont(f)
            painter.drawText(rect, Qt.AlignCenter, f"{area_m2} m²")
        painter.restore()

    def draw_wall(self, painter, wall):
        color = QColor(64, 64, 64)
        if wall.is_colliding:
            color = QColor(255, 69, 0)
        elif wall.is_selected:
            color = Qt.red

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

        if win.is_colliding:
            painter.setPen(QPen(QColor(255, 69, 0), 3))
        else:
            painter.setPen(QPen(Qt.red if win.is_selected else Qt.blue, 2))

        painter.drawRect(rect)
        painter.drawLine(QPointF(win.x, win.y + win.height / 2),
                         QPointF(win.x + win.width, win.y + win.height / 2))
        painter.restore()

    def check_collisions(self):
        for obj in self.objects:
            obj.is_colliding = False

        count = len(self.objects)
        for i in range(count):
            obj1 = self.objects[i]

            if RoomFloor is not None and isinstance(obj1, RoomFloor):
                continue

            rect1 = obj1.rect

            for j in range(i + 1, count):
                obj2 = self.objects[j]

                if RoomFloor is not None and isinstance(obj2, RoomFloor):
                    continue

                rect2 = obj2.rect
                intersection = rect1.intersected(rect2)

                if intersection.isEmpty():
                    continue

                is_wall1 = isinstance(obj1, Wall)
                is_wall2 = isinstance(obj2, Wall)
                is_win1 = isinstance(obj1, Window)
                is_win2 = isinstance(obj2, Window)
                is_svg1 = isinstance(obj1, SvgFurnitureObject)
                is_svg2 = isinstance(obj2, SvgFurnitureObject)

                is_attach1 = getattr(obj1, 'is_wall_attachment', False)
                is_attach2 = getattr(obj2, 'is_wall_attachment', False)

                if is_wall1 and is_wall2:
                    continue

                if (is_wall1 and is_attach1) or (is_wall2 and is_attach2) or \
                        (is_wall1 and is_attach2) or (is_wall2 and is_attach1):
                    continue

                if (is_win1 and is_svg2) or (is_win2 and is_svg1):
                    win_obj = obj1 if is_win1 else obj2
                    win_thickness = min(win_obj.rect.width(), win_obj.rect.height())
                    overlap_depth = min(intersection.width(), intersection.height())

                    if overlap_depth <= (win_thickness / 2 + 1):
                        continue

                if (is_wall1 and not is_attach2) or (is_wall2 and not is_attach1):
                    overlap_depth = min(intersection.width(), intersection.height())
                    if overlap_depth <= 6.0:
                        continue
                    else:
                        obj1.is_colliding = True
                        obj2.is_colliding = True
                        continue

                overlap_depth = min(intersection.width(), intersection.height())
                if overlap_depth > 1.0:
                    obj1.is_colliding = True
                    obj2.is_colliding = True

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

            if self.current_tool_mode == "floor":
                if RoomFloor is None:
                    self.status_message_signal.emit("RoomFloor nu este disponibil (import esuat).")
                    self.current_tool_mode = None
                    self.setCursor(Qt.ArrowCursor)
                    return
                self.is_drawing_floor = True
                self.floor_start_pt = pos_pt
                self.floor_temp_rect = QRectF(pos_pt.x(), pos_pt.y(), 0, 0)
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
                elif RoomFloor is not None and isinstance(obj, RoomFloor):
                    if obj.rect.contains(pos_pt):
                        clicked_obj = obj
                        break
                elif isinstance(obj, (Window, SvgFurnitureObject)):
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

        if self.is_drawing_floor and self.floor_start_pt:
            x = min(self.floor_start_pt.x(), wx)
            y = min(self.floor_start_pt.y(), wy)
            w = abs(wx - self.floor_start_pt.x())
            h = abs(wy - self.floor_start_pt.y())
            self.floor_temp_rect = QRectF(x, y, w, h)
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

            self.check_collisions()
            self.object_selected_signal.emit(self.selected_object)
            self.update()
            return

        if self.is_rotating and self.selected_object:
            rect = self.selected_object.rect
            curr_angle = self._angle_to_mouse(rect.center().x(), rect.center().y(), wx, wy)
            self.selected_object.rotation = (self.initial_rotation + curr_angle - self.rotate_start_angle) % 360
            self.check_collisions()
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
                self.check_collisions()
                self.project_changed_signal.emit()
            self.update()

        if self.is_drawing_floor and self.current_tool_mode == "floor":
            self.is_drawing_floor = False
            if RoomFloor is not None and self.floor_temp_rect and self.floor_temp_rect.width() > 0 and self.floor_temp_rect.height() > 0:
                try:
                    new_floor = RoomFloor(
                        self.floor_temp_rect.x(),
                        self.floor_temp_rect.y(),
                        self.floor_temp_rect.width(),
                        self.floor_temp_rect.height(),
                    )
                except TypeError:
                    new_floor = None

                if new_floor is not None:
                    self.objects.insert(0, new_floor)
                    self.select_object(new_floor)
                    self.project_changed_signal.emit()

            self.floor_start_pt = None
            self.floor_temp_rect = None
            self.current_tool_mode = None
            self.setCursor(Qt.ArrowCursor)
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

    def set_tool_floor(self):
        if RoomFloor is None:
            self.status_message_signal.emit("RoomFloor nu exista in proiect (import esuat).")
            self.current_tool_mode = None
            self.setCursor(Qt.ArrowCursor)
            return
        self.current_tool_mode = "floor"
        self.select_object(None)
        self.setCursor(Qt.CrossCursor)
        self.status_message_signal.emit("Suprafata: Click si TRAGE (diagonala) pentru a desena.")

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
            self.check_collisions()
            self.project_changed_signal.emit()
            if self.current_tool_mode == "svg_placement":
                self.current_tool_mode = None
                self.setCursor(Qt.ArrowCursor)
            self.update()

    def select_object(self, obj):
        for o in self.objects:
            o.is_selected = False
        self.selected_object = obj
        if obj:
            obj.is_selected = True
        self.object_selected_signal.emit(obj)
        self.update()

    def dist_to_segment(self, p, wall):
        x, y = p.x(), p.y()
        x1, y1, x2, y2 = wall.x1, wall.y1, wall.x2, wall.y2
        A = x - x1
        B = y - y1
        C = x2 - x1
        D = y2 - y1
        dot = A * C + B * D
        len_sq = C * C + D * D
        param = -1
        if len_sq != 0:
            param = dot / len_sq
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
            self.check_collisions()
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

        content.addWidget(self.create_left_panel())

        canvas_container = QWidget()
        cl = QVBoxLayout(canvas_container)
        cl.setContentsMargins(5, 5, 5, 5)
        cl.addWidget(self.canvas)
        content.addWidget(canvas_container, 1)

        content.addWidget(self.create_right_panel())

        main.addLayout(content, 1)
        main.addWidget(self.create_footer())

        self.canvas.status_message_signal.connect(self.lbl_status.setText)
        self.canvas.project_changed_signal.connect(self.refresh_stats)
        self.canvas.object_selected_signal.connect(self.update_properties)
        self.canvas.mouse_moved_signal.connect(lambda x, y: None)

        QShortcut(QKeySequence("Delete"), self).activated.connect(self.canvas.delete_selection)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.action_cancel)

        self.refresh_stats()

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
        self.chk_grid.toggled.connect(lambda val: setattr(self.canvas, 'grid_visible', val) or self.canvas.update())
        v_view.addWidget(self.chk_grid)

        self.chk_snap = QCheckBox("Snap to Grid")
        self.chk_snap.setChecked(True)
        self.chk_snap.toggled.connect(lambda val: setattr(self.canvas, 'snap_to_grid', val))
        v_view.addWidget(self.chk_snap)

        v.addWidget(gb_view)

        self.toolbox = QToolBox()
        self.toolbox.setStyleSheet("""
            QToolBox::tab { background: #E0D8C0; border: 1px solid #aaa; border-radius: 2px; color: black; font-weight: bold; }
            QListWidget { border: none; background: #F7F3E8; }
        """)

        list_struct = QListWidget()
        list_struct.setIconSize(QSize(32, 32))

        item_wall = QListWidgetItem("Perete (Linie)")
        item_wall.setData(Qt.UserRole, "CMD_WALL")
        list_struct.addItem(item_wall)

        item_win = QListWidgetItem("Fereastră (Albastru)")
        item_win.setData(Qt.UserRole, "CMD_WINDOW")
        list_struct.addItem(item_win)

        item_floor = QListWidgetItem("Zonă / Cameră (m²)")
        item_floor.setData(Qt.UserRole, "CMD_FLOOR")
        list_struct.addItem(item_floor)

        list_struct.itemClicked.connect(self.on_menu_item_clicked)
        self.toolbox.addItem(list_struct, "Structură")

        self.load_assets_structured()

        v.addWidget(self.toolbox)

        btn_clear = QPushButton("Sterge Tot")
        btn_clear.setStyleSheet("background: #E74C3C; color: white; padding: 5px;")
        btn_clear.clicked.connect(self.ask_clear_scene)
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
            return

        doors_path = os.path.join(assets_dir, "doors")
        if os.path.exists(doors_path):
            self.add_grid_category("Uși", doors_path)

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
        elif data == "CMD_FLOOR":
            self.canvas.set_tool_floor()
        elif data:
            self.canvas.set_tool_svg(data)

    def create_right_panel(self):
        w = QWidget()
        w.setFixedWidth(240)
        w.setStyleSheet("background-color: #FEFCF3; border-left: 1px solid #ccc;")
        v = QVBoxLayout(w)

        gb_tools = QGroupBox("Unelte Rapide")
        v_tools = QVBoxLayout(gb_tools)

        btn_add_floor = QPushButton("➕ Adauga Zona (m²)")
        btn_add_floor.setMinimumHeight(40)
        btn_add_floor.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #45a049; }
        """)
        btn_add_floor.clicked.connect(self.canvas.set_tool_floor)
        v_tools.addWidget(btn_add_floor)
        v.addWidget(gb_tools)

        gb_stats = QGroupBox("Statistici Proiect")
        v_stats = QVBoxLayout(gb_stats)
        self.lbl_total_area = QLabel("Total Arie: 0.00 m²")
        self.lbl_total_area.setStyleSheet("font-weight: bold; font-size: 14px; color: #2E7D32;")
        v_stats.addWidget(self.lbl_total_area)
        v.addWidget(gb_stats)

        self.gb_props = QGroupBox("Proprietăți")
        vp = QVBoxLayout(self.gb_props)

        self.lbl_name = QLabel("Nume: -")
        vp.addWidget(self.lbl_name)

        vp.addWidget(QLabel("Rotatie (°):"))
        self.spin_rot = QSpinBox()
        self.spin_rot.setRange(0, 360)
        self.spin_rot.setSingleStep(45)
        self.spin_rot.valueChanged.connect(self.on_rotation_changed)
        vp.addWidget(self.spin_rot)

        vp.addWidget(QLabel("Lățime (cm/px):"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(10, 2000)
        self.spin_width.setSingleStep(10)
        self.spin_width.valueChanged.connect(self.on_width_changed)
        vp.addWidget(self.spin_width)

        vp.addWidget(QLabel("Înălțime/Grosime (cm/px):"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(5, 2000)
        self.spin_height.setSingleStep(5)
        self.spin_height.valueChanged.connect(self.on_height_changed)
        vp.addWidget(self.spin_height)

        vp.addSpacing(10)
        self.btn_delete_obj = QPushButton("🗑️ Sterge Element")
        self.btn_delete_obj.setMinimumHeight(35)
        self.btn_delete_obj.setStyleSheet("""
            QPushButton { background-color: #ff4444; color: white; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #cc0000; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        self.btn_delete_obj.clicked.connect(self.canvas.delete_selection)
        self.btn_delete_obj.setEnabled(False)
        vp.addWidget(self.btn_delete_obj)

        self.gb_props.setEnabled(False)
        v.addWidget(self.gb_props)

        v.addStretch()
        return w

    def on_rotation_changed(self, val):
        obj = self.canvas.selected_object
        if obj and not isinstance(obj, Wall):
            obj.rotation = val
            self.canvas.check_collisions()
            self.canvas.update()

    def on_width_changed(self, val):
        obj = self.canvas.selected_object
        if obj:
            if isinstance(obj, Wall):
                pass
            else:
                obj.width = val
                self.canvas.check_collisions()
                self.canvas.update()
                self.refresh_stats()

    def on_height_changed(self, val):
        obj = self.canvas.selected_object
        if obj:
            if isinstance(obj, Wall):
                obj.thickness = val
            else:
                obj.height = val
            self.canvas.check_collisions()
            self.canvas.update()
            self.refresh_stats()

    def create_footer(self):
        w = QWidget()
        w.setStyleSheet("background:#185E8A; color:white;")
        h = QHBoxLayout(w)
        self.lbl_status = QLabel("Gata.")
        h.addWidget(self.lbl_status)
        return w

    def refresh_stats(self):
        total_m2 = 0.0
        if RoomFloor is not None:
            for obj in self.canvas.objects:
                if isinstance(obj, RoomFloor):
                    total_m2 += float(getattr(obj, "area_m2", 0.0))
        if hasattr(self, "lbl_total_area"):
            self.lbl_total_area.setText(f"Total Arie: {total_m2:.2f} m²")

    def update_properties(self, obj):
        if obj:
            self.gb_props.setEnabled(True)
            if hasattr(self, "btn_delete_obj"):
                self.btn_delete_obj.setEnabled(True)

            self.spin_rot.blockSignals(True)
            self.spin_width.blockSignals(True)
            self.spin_height.blockSignals(True)

            if isinstance(obj, Wall):
                self.lbl_name.setText("Perete")
                self.spin_rot.setEnabled(False)
                self.spin_rot.setValue(0)

                self.spin_width.setEnabled(False)
                self.spin_width.setValue(0)

                self.spin_height.setEnabled(True)
                self.spin_height.setValue(int(obj.thickness))

            elif RoomFloor is not None and isinstance(obj, RoomFloor):
                self.lbl_name.setText(f"Camera ({getattr(obj, 'area_m2', 0)} m²)")
                self.spin_rot.setEnabled(False)
                self.spin_rot.setValue(0)

                self.spin_width.setEnabled(True)
                self.spin_width.setValue(int(getattr(obj, "width", 0)))

                self.spin_height.setEnabled(True)
                self.spin_height.setValue(int(getattr(obj, "height", 0)))

            elif isinstance(obj, Window):
                self.lbl_name.setText("Fereastră")
                self.spin_rot.setEnabled(True)
                self.spin_rot.setValue(int(obj.rotation))

                self.spin_width.setEnabled(True)
                self.spin_width.setValue(int(obj.width))

                self.spin_height.setEnabled(True)
                self.spin_height.setValue(int(obj.height))

            else:
                self.lbl_name.setText(getattr(obj, 'name', 'Obiect'))
                self.spin_rot.setEnabled(True)
                self.spin_rot.setValue(int(obj.rotation))

                self.spin_width.setEnabled(True)
                self.spin_width.setValue(int(obj.width))

                self.spin_height.setEnabled(True)
                self.spin_height.setValue(int(obj.height))

            self.spin_rot.blockSignals(False)
            self.spin_width.blockSignals(False)
            self.spin_height.blockSignals(False)
        else:
            self.gb_props.setEnabled(False)
            self.lbl_name.setText("-")
            if hasattr(self, "btn_delete_obj"):
                self.btn_delete_obj.setEnabled(False)

    def action_cancel(self):
        self.canvas.current_tool_mode = None
        self.canvas.is_drawing_wall = False
        self.canvas.is_drawing_floor = False
        self.canvas.wall_start_pt = None
        self.canvas.wall_temp_end = None
        self.canvas.floor_start_pt = None
        self.canvas.floor_temp_rect = None
        self.canvas.select_object(None)
        self.lbl_status.setText("Anulat.")
        self.canvas.setCursor(Qt.ArrowCursor)

    def ask_clear_scene(self):
        reply = QMessageBox.question(
            self,
            "Confirmare Stergere",
            "Esti sigur ca vrei sa stergi TOT proiectul? Actiunea nu poate fi anulata.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.canvas.clear_scene()

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
                self.canvas.check_collisions()
                self.canvas.update()
                self.refresh_stats()
                QMessageBox.information(self, "Succes", "Incarcat cu succes!")
            else:
                QMessageBox.warning(self, "Eroare", "Fisier invalid sau nu s-a putut incarca.")
