import math
import os
import sys

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
    QMessageBox, QFileDialog, QSpinBox, QCheckBox, QShortcut, QToolBox,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QKeySequence, QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QSize, QRectF, QMarginsF, QLineF

from .TutorialDialog import TutorialDialog

# Importuri conditionale pentru structura proiectului
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
    """
        Componenta grafica principala (View/Widget) responsabila pentru desenarea
        si interactiunea cu planul 2D.

        Aceasta clasa gestioneaza:
        1. Randarea obiectelor (pereti, ferestre, mobila).
        2. Gestionarea evenimentelor de mouse (click, drag, drop).
        3. Sistemul de coordonate si transformari (zoom, pan).
        4. Logica de aliniere (Snapping) si detectie coliziuni.
        """

    # Semnale pentru comunicarea cu WorkPage (Controller)
    mouse_moved_signal = pyqtSignal(int, int)
    project_changed_signal = pyqtSignal()
    status_message_signal = pyqtSignal(str)
    object_selected_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        """
                Initializeaza canvas-ul, starea interna si setarile implicite.

                Args:
                    parent (QWidget): Widget-ul parinte.
                """
        super().__init__(parent)
        self.pm = ProjectManager()
        self.objects = []  # Lista tuturor obiectelor din scena

        # Variabile pentru Viewport (Zoom/Pan)
        self.offset_x = 0
        self.offset_y = 0
        self.zoom_scale = 1.0

        self.current_tool_mode = None  # 'wall', 'window', 'floor', 'ruler', 'svg_placement'
        self.current_svg_path = None
        self.selected_object = None

        # Stare Panning (deplasare plan)
        self.is_panning = False
        self.last_pan_x = 0
        self.last_pan_y = 0

        # State desenare perete
        self.is_drawing_wall = False
        self.wall_start_pt = None
        self.wall_temp_end = None

        # State desenare podea
        self.is_drawing_floor = False
        self.floor_start_pt = None
        self.floor_temp_rect = None

        # State masurare - RULER
        self.is_measuring = False
        self.ruler_start = None
        self.ruler_end = None

        # Stare Manipulare Obiecte (Move/Rotate/Resize)
        self.is_moving = False
        self.is_rotating = False
        self.is_resizing = False
        self.active_handle = None

        # Variabile auxiliare pentru calcule geometrice
        self.drag_start_pos = QPointF()
        self.obj_start_pos = QPointF()
        self.obj_start_rect = None
        self.wall_coords_start = None
        self.rotate_start_angle = 0
        self.initial_rotation = 0

        # Configurare Smart Snap (Aliniere magnetica)
        self.active_guides = []
        self.snap_threshold = 10

        # Configurare Grila
        self.grid_visible = True
        self.snap_to_grid = True
        self.grid_size = 20
        self.handle_size = 10

        # Setari Widget
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)  # Activeaza mouseMoveEvent fara click
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("background-color: white;")

    def paintEvent(self, e):
        """
                Metoda suprascrisa din QWidget. Este apelata automat la fiecare update().
                Gestioneaza ordinea de desenare (Z-Order) a elementelor.
                """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Curatare fundal
        painter.fillRect(self.rect(), Qt.white)

        # 2. Aplicare transformari globale (Pan & Zoom)
        painter.translate(self.offset_x, self.offset_y)
        painter.scale(self.zoom_scale, self.zoom_scale)

        # 3. Desenare Grila
        if self.grid_visible:
            self.draw_grid(painter)

        # 4. Desenare Podele (Stratul cel mai de jos)
        if RoomFloor is not None:
            for obj in self.objects:
                if isinstance(obj, RoomFloor):
                    self.draw_room_floor(painter, obj)

            # Previzualizare desenare podea
            if self.is_drawing_floor and self.floor_temp_rect:
                painter.save()
                painter.setBrush(QBrush(QColor(100, 200, 100, 100)))
                painter.setPen(QPen(Qt.black, 1, Qt.DashLine))
                painter.drawRect(self.floor_temp_rect)
                painter.restore()

        # 5. Desenare Pereti
        for obj in self.objects:
            if isinstance(obj, Wall):
                self.draw_wall(painter, obj)

        # 6. Desenare Ferestre si Mobilier
        for obj in self.objects:
            if isinstance(obj, Window):
                self.draw_window(painter, obj)
            elif isinstance(obj, SvgFurnitureObject):
                obj.draw(painter)

        # 7. Desenare Elemente UI (Selectie, Ghidaje, Rigla)
        if self.selected_object and not isinstance(self.selected_object, Wall):
            self.draw_selection_handles(painter, self.selected_object)

        if self.is_moving and self.active_guides:
            painter.save()
            pen = QPen(QColor(0, 200, 0), 1)  # Verde
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            for line in self.active_guides:
                painter.drawLine(line)
            painter.restore()

        if self.is_drawing_wall and self.wall_start_pt and self.wall_temp_end:
            pen = QPen(QColor(80, 80, 80), 8)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(self.wall_start_pt, self.wall_temp_end)

        if self.is_measuring and self.ruler_start and self.ruler_end:
            self.draw_ruler(painter)

    def draw_ruler(self, painter):
        """
                Deseneaza instrumentul de masurare (linie punctata si text cu distanta).
                """
        painter.save()

        pen = QPen(Qt.blue, 2)
        pen.setStyle(Qt.DashDotLine)
        painter.setPen(pen)
        painter.drawLine(self.ruler_start, self.ruler_end)

        # Desenare marcaje capete (X-uri)
        sx, sy = self.ruler_start.x(), self.ruler_start.y()
        ex, ey = self.ruler_end.x(), self.ruler_end.y()

        painter.drawLine(QPointF(sx - 5, sy - 5), QPointF(sx + 5, sy + 5))
        painter.drawLine(QPointF(sx - 5, sy + 5), QPointF(sx + 5, sy - 5))

        painter.drawLine(QPointF(ex - 5, ey - 5), QPointF(ex + 5, ey + 5))
        painter.drawLine(QPointF(ex - 5, ey + 5), QPointF(ex + 5, ey - 5))

        # Calcul distanta euclidiana
        dx = ex - sx
        dy = ey - sy
        dist_px = math.sqrt(dx ** 2 + dy ** 2)
        dist_m = dist_px / 100.0 # Conversie: 100px = 1 metru

        # Afisare text la mijloc
        mid_x = (sx + ex) / 2
        mid_y = (sy + ey) / 2

        text = f"{dist_m:.2f} m"
        font = QFont("Arial", 10)
        font.setBold(True)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        w = metrics.width(text) + 10
        h = metrics.height() + 4

        rect_txt = QRectF(mid_x - w / 2, mid_y - h / 2 - 15, w, h)

        painter.setPen(Qt.black)
        painter.setBrush(QColor(255, 255, 200))
        painter.drawRoundedRect(rect_txt, 5, 5)
        painter.drawText(rect_txt, Qt.AlignCenter, text)

        painter.restore()

    def set_tool_ruler(self):
        self.current_tool_mode = "ruler"
        self.select_object(None)
        self.setCursor(Qt.CrossCursor)
        self.status_message_signal.emit("Rigla: Click si trage pentru a masura.")

    def _calculate_smart_snap(self, current_obj, proposed_x, proposed_y):
        """
                Algoritmul de aliniere magnetica (Smart Snapping).
                Compara pozitia propusa a obiectului curent cu marginile tuturor celorlalte obiecte.

                Args:
                    current_obj: Obiectul mutat.
                    proposed_x, proposed_y: Coordonatele unde mouse-ul vrea sa duca obiectul.

                Returns:
                    Tuple (final_x, final_y, guides): Coordonatele ajustate si liniile de desenat.
                """

        snap_x, snap_y = proposed_x, proposed_y
        guides = []

        w, h = current_obj.width, current_obj.height
        cur_l = proposed_x
        cur_r = proposed_x + w
        cur_cx = proposed_x + w / 2

        cur_t = proposed_y
        cur_b = proposed_y + h
        cur_cy = proposed_y + h / 2

        snapped_x = False
        snapped_y = False

        threshold = self.snap_threshold

        # Iteram prin toate obiectele pentru a gasi puncte de aliniere
        for other in self.objects:
            if other is current_obj:
                continue

            r = other.rect
            oth_l, oth_r = r.left(), r.right()
            oth_cx = r.center().x()
            oth_t, oth_b = r.top(), r.bottom()
            oth_cy = r.center().y()

            # Verificari pentru axa X (Stanga, Dreapta, Centru)
            if not snapped_x:
                if abs(cur_l - oth_l) < threshold:
                    snap_x = oth_l
                    snapped_x = True
                    guides.append(QLineF(oth_l, min(cur_t, oth_t) - 50, oth_l, max(cur_b, oth_b) + 50))
                elif abs(cur_l - oth_r) < threshold:
                    snap_x = oth_r
                    snapped_x = True
                    guides.append(QLineF(oth_r, min(cur_t, oth_t) - 50, oth_r, max(cur_b, oth_b) + 50))

                elif abs(cur_r - oth_l) < threshold:
                    snap_x = oth_l - w
                    snapped_x = True
                    guides.append(QLineF(oth_l, min(cur_t, oth_t) - 50, oth_l, max(cur_b, oth_b) + 50))
                elif abs(cur_r - oth_r) < threshold:
                    snap_x = oth_r - w
                    snapped_x = True
                    guides.append(QLineF(oth_r, min(cur_t, oth_t) - 50, oth_r, max(cur_b, oth_b) + 50))

                elif abs(cur_cx - oth_cx) < threshold:
                    snap_x = oth_cx - w / 2
                    snapped_x = True
                    guides.append(QLineF(oth_cx, min(cur_t, oth_t) - 50, oth_cx, max(cur_b, oth_b) + 50))

            # Verificari pentru axa Y (Sus, Jos, Centru)
            if not snapped_y:
                if abs(cur_t - oth_t) < threshold:
                    snap_y = oth_t
                    snapped_y = True
                    guides.append(QLineF(min(cur_l, oth_l) - 50, oth_t, max(cur_r, oth_r) + 50, oth_t))
                elif abs(cur_t - oth_b) < threshold:
                    snap_y = oth_b
                    snapped_y = True
                    guides.append(QLineF(min(cur_l, oth_l) - 50, oth_b, max(cur_r, oth_r) + 50, oth_b))

                elif abs(cur_b - oth_t) < threshold:
                    snap_y = oth_t - h
                    snapped_y = True
                    guides.append(QLineF(min(cur_l, oth_l) - 50, oth_t, max(cur_r, oth_r) + 50, oth_t))
                elif abs(cur_b - oth_b) < threshold:
                    snap_y = oth_b - h
                    snapped_y = True
                    guides.append(QLineF(min(cur_l, oth_l) - 50, oth_b, max(cur_r, oth_r) + 50, oth_b))

                elif abs(cur_cy - oth_cy) < threshold:
                    snap_y = oth_cy - h / 2
                    snapped_y = True
                    guides.append(QLineF(min(cur_l, oth_l) - 50, oth_cy, max(cur_r, oth_r) + 50, oth_cy))

            if snapped_x and snapped_y:
                break

        return snap_x, snap_y, guides

    def draw_selection_handles(self, painter, obj):
        """
                Deseneaza manerele de redimensionare (patratele mici) in colturile obiectului selectat.
                Tine cont de rotatia obiectului.
                """
        painter.save()

        cx = obj.x + obj.width / 2
        cy = obj.y + obj.height / 2

        # Rotim sistemul de coordonate pentru a desena manerele aliniate cu obiectul
        painter.translate(cx, cy)
        painter.rotate(obj.rotation)
        painter.translate(-cx, -cy)

        rect = QRectF(obj.x, obj.y, obj.width, obj.height)

        painter.setPen(QPen(Qt.blue, 1))
        painter.setBrush(QBrush(Qt.white))

        hs = self.handle_size
        hs2 = hs / 2

        # Coordonate locale pentru manere
        handles = [
            QRectF(rect.left() - hs2, rect.top() - hs2, hs, hs),
            QRectF(rect.right() - hs2, rect.top() - hs2, hs, hs),
            QRectF(rect.right() - hs2, rect.bottom() - hs2, hs, hs),
            QRectF(rect.left() - hs2, rect.bottom() - hs2, hs, hs)
        ]

        for h in handles:
            painter.drawRect(h)
            painter.drawLine(h.topLeft(), h.bottomRight())
            painter.drawLine(h.topRight(), h.bottomLeft())

        # Contur de selectie
        pen_outline = QPen(Qt.blue, 1, Qt.DashLine)
        painter.setPen(pen_outline)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)

        painter.restore()

    def _get_mouse_in_object_coords(self, mx, my, obj):
        """
                Transforma coordonatele mouse-ului din spatiul scena in spatiul local al obiectului,
                anuland rotatia acestuia. Util pentru detectia click-ului pe manere.
                """
        cx = obj.x + obj.width / 2
        cy = obj.y + obj.height / 2

        dx = mx - cx
        dy = my - cy

        # Rotatie inversa
        rad = math.radians(-obj.rotation)
        rx = dx * math.cos(rad) - dy * math.sin(rad)
        ry = dx * math.sin(rad) + dy * math.cos(rad)

        final_x = rx + cx
        final_y = ry + cy

        return QPointF(final_x, final_y)

    def _check_handle_click(self, mx, my, obj):
        """
                Verifica daca s-a dat click pe un maner de redimensionare.
                Returns: Codul manerului ('tl', 'tr', 'bl', 'br') sau None.
                """
        if isinstance(obj, Wall):
            return None # Peretii nu au manere standard de resize

        local_pt = self._get_mouse_in_object_coords(mx, my, obj)
        lx, ly = local_pt.x(), local_pt.y()

        hs = self.handle_size
        hs2 = hs / 2

        l, t, r, b = obj.x, obj.y, obj.x + obj.width, obj.y + obj.height

        if abs(lx - l) < hs and abs(ly - t) < hs: return 'tl'
        if abs(lx - r) < hs and abs(ly - t) < hs: return 'tr'
        if abs(lx - r) < hs and abs(ly - b) < hs: return 'br'
        if abs(lx - l) < hs and abs(ly - b) < hs: return 'bl'

        return None

    def draw_grid(self, painter):
        """ Deseneaza grila de fundal pentru orientare. """
        pen = QPen(QColor(240, 240, 240))
        pen.setWidth(1)
        painter.setPen(pen)
        start, end, step = -3000, 6000, self.grid_size
        for x in range(start, end, step):
            painter.drawLine(x, start, x, end)
        for y in range(start, end, step):
            painter.drawLine(start, y, end, y)

    def draw_room_floor(self, painter, floor):
        """ Deseneaza obiectele de tip Podea/Zona. """
        rect = floor.rect
        base_color = getattr(floor, "color", QColor(100, 200, 100, 120))
        if getattr(floor, "is_selected", False):
            base_color = QColor(255, 200, 200, 150)

        painter.save()
        painter.setBrush(QBrush(base_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(rect)

        # Afisare arie in centrul camerei
        area_m2 = getattr(floor, "area_m2", None)
        if area_m2 is not None:
            painter.setPen(QPen(Qt.black))
            f = QFont("Arial", 10)
            f.setBold(True)
            painter.setFont(f)
            painter.drawText(rect, Qt.AlignCenter, f"{area_m2} m²")
        painter.restore()

    def draw_wall(self, painter, wall):
        """ Deseneaza peretii si cotele (dimensiunile) acestora. """
        color = QColor(64, 64, 64)
        if wall.is_colliding:
            color = QColor(255, 69, 0)
        elif wall.is_selected:
            color = Qt.red

        pen = QPen(color, wall.thickness)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        p1 = QPointF(wall.x1, wall.y1)
        p2 = QPointF(wall.x2, wall.y2)
        painter.drawLine(p1, p2)

        # Desenare text lungime
        painter.save()

        dx = wall.x2 - wall.x1
        dy = wall.y2 - wall.y1
        length_px = math.sqrt(dx ** 2 + dy ** 2)
        length_m = length_px / 100.0

        mid_x = (wall.x1 + wall.x2) / 2
        mid_y = (wall.y1 + wall.y2) / 2

        painter.translate(mid_x, mid_y)

        angle_deg = math.degrees(math.atan2(dy, dx))

        if 90 < abs(angle_deg) <= 270:
            angle_deg += 180

        painter.rotate(angle_deg)

        text = f"{length_m:.2f} m"

        font = QFont("Arial", 12)
        font.setBold(True)
        painter.setFont(font)

        # Desenare fundal text pentru lizibilitate
        metrics = painter.fontMetrics()
        text_width = metrics.width(text)
        text_height = metrics.height()

        bg_rect = QRectF(-text_width / 2 - 2, -wall.thickness / 2 - text_height - 2, text_width + 4, text_height)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.drawRect(bg_rect)

        painter.setPen(Qt.black)
        text_pos_y = -wall.thickness / 2 - 5
        painter.drawText(int(-text_width / 2), int(text_pos_y), text)

        painter.restore()

    def draw_window(self, painter, win):
        """ Deseneaza ferestrele, tinand cont de rotatie. """
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
        """
                Verifica intersectiile dintre toate obiectele din scena.
                Are complexitate O(N^2). Marcheaza obiectele cu 'is_colliding = True'.
                Ignora coliziunile valide (ex: Fereastra in Perete).
                """
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

                # Logica specifica pentru ignorarea coliziunilor intentionate
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

                # Ferestrele nu se ciocnesc cu mobila
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
        """
                Gestioneaza click-ul mouse-ului.
                Functionalitati: Selectie, Start Desenare, Start Drag & Drop, Pan (Middle Click).
                """
        # Pan cu butonul din mijloc
        if e.button() == Qt.MiddleButton:
            self.is_panning = True
            self.last_pan_x, self.last_pan_y = e.x(), e.y()
            self.setCursor(Qt.ClosedHandCursor)
            return

        # Conversie coordonate ecran -> coordonate scena
        wx = (e.x() - self.offset_x) / self.zoom_scale
        wy = (e.y() - self.offset_y) / self.zoom_scale

        # Calcul coordonate Grid Snap
        snapped_wx = round(wx / self.grid_size) * self.grid_size
        snapped_wy = round(wy / self.grid_size) * self.grid_size

        pos_pt = QPointF(wx, wy)
        snap_pt = QPointF(snapped_wx, snapped_wy) if self.snap_to_grid else pos_pt

        # 1. Unelte Active (Prioritate 1)
        if self.current_tool_mode == "ruler" and e.button() == Qt.LeftButton:
            self.is_measuring = True
            self.ruler_start = snap_pt
            self.ruler_end = snap_pt
            return

        # 2. Rotire manuala (Click Dreapta)
        if e.button() == Qt.RightButton and self.selected_object:
            if not isinstance(self.selected_object, Wall):
                self.is_rotating = True
                rect = self.selected_object.rect
                self.rotate_start_angle = self._angle_to_mouse(rect.center().x(), rect.center().y(), wx, wy)
                self.initial_rotation = self.selected_object.rotation
                return

        # 3. Interactiuni Selectie (Click Stanga)
        if e.button() == Qt.LeftButton:
            if self.current_tool_mode == "wall":
                self.is_drawing_wall = True
                self.wall_start_pt = snap_pt
                self.wall_temp_end = snap_pt
                return

            if self.current_tool_mode == "floor":
                if RoomFloor is None:
                    self.status_message_signal.emit("RoomFloor nu este disponibil (import esuat).")
                    self.current_tool_mode = None
                    self.setCursor(Qt.ArrowCursor)
                    return
                self.is_drawing_floor = True
                self.floor_start_pt = snap_pt
                self.floor_temp_rect = QRectF(snap_pt.x(), snap_pt.y(), 0, 0)
                return

            if self.current_tool_mode in ["window", "svg_placement"]:
                self.place_object_at(snap_pt.x(), snap_pt.y())
                return

            if self.selected_object and not isinstance(self.selected_object, Wall):
                handle = self._check_handle_click(wx, wy, self.selected_object)
                if handle:
                    self.is_resizing = True
                    self.active_handle = handle
                    self.obj_start_rect = (self.selected_object.x, self.selected_object.y,
                                           self.selected_object.width, self.selected_object.height)
                    self.drag_start_pos = self._get_mouse_in_object_coords(wx, wy, self.selected_object)
                    return

            # Hit Testing pentru selectie obiecte
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

            # Initiere mutare obiect
            if clicked_obj:
                self.is_moving = True
                self.drag_start_pos = pos_pt

                if isinstance(clicked_obj, Wall):
                    self.wall_coords_start = (clicked_obj.x1, clicked_obj.y1, clicked_obj.x2, clicked_obj.y2)
                else:
                    self.obj_start_pos = QPointF(clicked_obj.x, clicked_obj.y)

            self.update()

    def mouseMoveEvent(self, e):
        """
                Gestioneaza miscarea mouse-ului.
                Functionalitati: Update cursor, previzualizare desenare, mutare obiecte cu Smart Snap, redimensionare.
                """
        wx = (e.x() - self.offset_x) / self.zoom_scale
        wy = (e.y() - self.offset_y) / self.zoom_scale
        self.mouse_moved_signal.emit(int(wx), int(wy))

        # Logica schimbare cursor
        if not self.is_resizing and not self.is_moving and not self.is_rotating and self.selected_object:
            handle = self._check_handle_click(wx, wy, self.selected_object)
            if handle in ['tl', 'br']:
                self.setCursor(Qt.SizeBDiagCursor)
            elif handle in ['tr', 'bl']:
                self.setCursor(Qt.SizeFDiagCursor)
            elif not self.is_panning and self.current_tool_mode is None:
                self.setCursor(Qt.ArrowCursor)
        elif not self.is_panning and self.current_tool_mode is None and not self.is_resizing:
            self.setCursor(Qt.ArrowCursor)

        # Logica Pan
        if self.is_panning:
            self.offset_x += e.x() - self.last_pan_x
            self.offset_y += e.y() - self.last_pan_y
            self.last_pan_x, self.last_pan_y = e.x(), e.y()
            self.update()
            return

        snap_wx = round(wx / self.grid_size) * self.grid_size
        snap_wy = round(wy / self.grid_size) * self.grid_size

        # Logica Masurare
        if self.is_measuring:
            tgt = QPointF(snap_wx, snap_wy) if self.snap_to_grid else QPointF(wx, wy)
            self.ruler_end = tgt

            dx = self.ruler_end.x() - self.ruler_start.x()
            dy = self.ruler_end.y() - self.ruler_start.y()
            d_m = math.sqrt(dx ** 2 + dy ** 2) / 100.0
            self.status_message_signal.emit(f"Distanță: {d_m:.2f} m")

            self.update()
            return

        # Logica Desenare
        if self.is_drawing_wall:
            self.wall_temp_end = QPointF(snap_wx, snap_wy) if self.snap_to_grid else QPointF(wx, wy)
            self.update()
            return

        if self.is_drawing_floor and self.floor_start_pt:
            tx = snap_wx if self.snap_to_grid else wx
            ty = snap_wy if self.snap_to_grid else wy
            x = min(self.floor_start_pt.x(), tx)
            y = min(self.floor_start_pt.y(), ty)
            w = abs(tx - self.floor_start_pt.x())
            h = abs(ty - self.floor_start_pt.y())
            self.floor_temp_rect = QRectF(x, y, w, h)
            self.update()
            return

        # Logica Mutare Obiecte
        if self.is_moving and self.selected_object:
            dx = wx - self.drag_start_pos.x()
            dy = wy - self.drag_start_pos.y()

            if isinstance(self.selected_object, Wall):
                if self.snap_to_grid:
                    dx = round(dx / self.grid_size) * self.grid_size
                    dy = round(dy / self.grid_size) * self.grid_size
                ox1, oy1, ox2, oy2 = self.wall_coords_start
                self.selected_object.x1 = ox1 + dx
                self.selected_object.y1 = oy1 + dy
                self.selected_object.x2 = ox2 + dx
                self.selected_object.y2 = oy2 + dy
            else:
                # Obiectele folosesc Smart Snap
                proposed_x = self.obj_start_pos.x() + dx
                proposed_y = self.obj_start_pos.y() + dy

                final_x, final_y, guides = self._calculate_smart_snap(self.selected_object, proposed_x, proposed_y)

                is_snapped_x = (final_x != proposed_x)
                is_snapped_y = (final_y != proposed_y)

                # Fallback la Grid Snap daca nu exista Smart Snap
                if self.snap_to_grid and not is_snapped_x:
                    final_x = round(proposed_x / self.grid_size) * self.grid_size

                if self.snap_to_grid and not is_snapped_y:
                    final_y = round(proposed_y / self.grid_size) * self.grid_size

                self.selected_object.x = final_x
                self.selected_object.y = final_y
                self.active_guides = guides

            self.check_collisions()
            self.object_selected_signal.emit(self.selected_object)
            self.update()
            return

        # Logica Resize
        if self.is_resizing and self.selected_object and self.obj_start_rect:
            local_mouse = self._get_mouse_in_object_coords(wx, wy, self.selected_object)
            dx = local_mouse.x() - self.drag_start_pos.x()
            dy = local_mouse.y() - self.drag_start_pos.y()
            if self.snap_to_grid:
                dx = round(dx / self.grid_size) * self.grid_size
                dy = round(dy / self.grid_size) * self.grid_size

            ox, oy, ow, oh = self.obj_start_rect
            new_x, new_y, new_w, new_h = ox, oy, ow, oh

            # Calculare noi dimensiuni in functie de maner
            if self.active_handle == 'br':
                new_w, new_h = ow + dx, oh + dy
            elif self.active_handle == 'bl':
                new_x, new_w, new_h = ox + dx, ow - dx, oh + dy
            elif self.active_handle == 'tr':
                new_y, new_w, new_h = oy + dy, ow + dx, oh - dy
            elif self.active_handle == 'tl':
                new_x, new_y, new_w, new_h = ox + dx, oy + dy, ow - dx, oh - dy

            if new_w < 10: new_w = 10
            if new_h < 10: new_h = 10

            self.selected_object.x, self.selected_object.y = new_x, new_y
            self.selected_object.width, self.selected_object.height = new_w, new_h

            self.check_collisions()
            self.object_selected_signal.emit(self.selected_object)
            self.update()
            return

        # Logica Rotire
        if self.is_rotating and self.selected_object:
            rect = self.selected_object.rect
            curr_angle = self._angle_to_mouse(rect.center().x(), rect.center().y(), wx, wy)
            self.selected_object.rotation = (self.initial_rotation + curr_angle - self.rotate_start_angle) % 360
            self.check_collisions()
            self.object_selected_signal.emit(self.selected_object)
            self.update()

    def mouseReleaseEvent(self, e):
        """
                Gestioneaza eliberarea butonului mouse-ului.
                Finalizeaza actiunile (desenare, mutare, resize).
                """
        self.active_guides = []

        if self.is_measuring:
            self.is_measuring = False
            self.ruler_start = None
            self.ruler_end = None
            self.status_message_signal.emit("Masurare finalizata.")
            self.update()

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
            if RoomFloor is not None and self.floor_temp_rect and self.floor_temp_rect.width() > 0:
                try:
                    new_floor = RoomFloor(self.floor_temp_rect.x(), self.floor_temp_rect.y(),
                                          self.floor_temp_rect.width(), self.floor_temp_rect.height())
                    self.objects.insert(0, new_floor)
                    self.select_object(new_floor)
                    self.project_changed_signal.emit()
                except:
                    pass
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
        self.is_resizing = False
        self.active_handle = None
        self.obj_start_rect = None
        self.update()

    def wheelEvent(self, e):
        """
                Gestioneaza rotita mouse-ului.
                Ctrl + Scroll -> Zoom.
                Scroll simplu -> Rotire obiect selectat.
                """
        if e.modifiers() & Qt.ControlModifier:
            old_wx = (e.x() - self.offset_x) / self.zoom_scale
            old_wy = (e.y() - self.offset_y) / self.zoom_scale
            factor = 1.1 if e.angleDelta().y() > 0 else 0.9
            self.zoom_scale = max(0.1, min(5.0, self.zoom_scale * factor))
            self.offset_x = e.x() - old_wx * self.zoom_scale
            self.offset_y = e.y() - old_wy * self.zoom_scale
            self.status_message_signal.emit(f"Zoom: {int(self.zoom_scale * 100)}%")
            self.update()

        elif self.selected_object and not isinstance(self.selected_object, Wall):
            delta = e.angleDelta().y()
            step = 5 if (e.modifiers() & Qt.ShiftModifier) else 15

            if delta < 0:
                step = -step

            self.selected_object.rotation = (self.selected_object.rotation + step) % 360
            self.check_collisions()
            self.object_selected_signal.emit(self.selected_object)
            self.update()
            self.status_message_signal.emit(f"Rotatie: {self.selected_object.rotation}°")

        else:
            super().wheelEvent(e)

    def set_tool_wall(self):
        """ Activeaza modul desenare perete. """
        self.current_tool_mode = "wall"
        self.select_object(None)
        self.setCursor(Qt.CrossCursor)
        self.status_message_signal.emit("Unealta Perete: Click si trage.")

    def set_tool_window(self):
        """ Activeaza modul plasare fereastra. """
        self.current_tool_mode = "window"
        self.select_object(None)
        self.setCursor(Qt.CrossCursor)
        self.status_message_signal.emit("Unealta Fereastră: Click pentru a plasa.")

    def set_tool_svg(self, path):
        """ Activeaza modul plasare mobilier SVG. """
        self.current_tool_mode = "svg_placement"
        self.current_svg_path = path
        self.select_object(None)
        self.setCursor(Qt.CrossCursor)
        self.status_message_signal.emit("Unealta Mobilier: Click pentru a plasa.")

    def set_tool_floor(self):
        """ Activeaza modul desenare podea/zona. """
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
        """ Calculeaza distanta de la un punct P la segmentul de dreapta definit de perete. """
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
        """ Calculeaza unghiul in grade dintre centrul obiectului si pozitia mouse-ului. """
        return math.degrees(math.atan2(my - cy, mx - cx))

    def delete_selection(self):
        """ Sterge obiectul selectat curent. """
        if self.selected_object and self.selected_object in self.objects:
            self.objects.remove(self.selected_object)
            self.select_object(None)
            self.check_collisions()
            self.project_changed_signal.emit()
            self.update()

    def clear_scene(self):
        """ Sterge toate obiectele din scena. """
        self.objects.clear()
        self.select_object(None)
        self.project_changed_signal.emit()
        self.update()

    def load_layout_template(self, template_type):
        """
                Incarca un sablon predefinit de apartament.
                Args:
                    template_type (str): Identificatorul sablonului (ex: 'APARTAMENT_STUDIO').
                """
        self.objects.clear()

        if template_type == "APARTAMENT_STUDIO":
            L, T = 80, 80
            R, B = 1140, 800

            self.objects.append(Wall(L, T, R, T))
            self.objects.append(Wall(R, T, R, B))
            self.objects.append(Wall(R, B, L, B))
            self.objects.append(Wall(L, B, L, T))

            hx1 = R - 220
            hy1 = B - 260
            self.objects.append(Wall(hx1, hy1, R, hy1))
            self.objects.append(Wall(hx1, hy1, hx1, B))

            bx1 = hx1
            by1 = hy1
            bx2 = R
            by2 = hy1 + 220
            self.objects.append(Wall(bx1, by2, bx2, by2))

            kx2 = L + 360
            ky1 = T + 260
            self.objects.append(Wall(L, ky1, kx2, ky1))

            nx1 = hx1 - 200
            ny1 = B - 260
            self.objects.append(Wall(nx1, ny1, hx1, ny1))
            self.objects.append(Wall(nx1, ny1, nx1, B))

        elif template_type == "APARTAMENT_2_CAMERE":
            L, T = 60, 60
            R, B = 1240, 900

            self.objects.append(Wall(L, T, R, T))
            self.objects.append(Wall(R, T, R, B))
            self.objects.append(Wall(R, B, L, B))
            self.objects.append(Wall(L, B, L, T))

            hall_w = 180
            hx = R - hall_w
            self.objects.append(Wall(hx, T + 120, hx, B - 120))

            by1 = T + 320
            by2 = by1 + 220
            self.objects.append(Wall(hx, by1, R, by1))
            self.objects.append(Wall(hx, by2, R, by2))

            kx2 = L + 380
            ky = B - 320
            self.objects.append(Wall(kx2, ky, kx2, B))
            self.objects.append(Wall(L, ky, kx2, ky))

            self.objects.append(Wall(hx, B - 340, R, B - 340))

            dx = L + 520
            dy = T + 420
            self.objects.append(Wall(L, dy, dx, dy))
            self.objects.append(Wall(dx, T, dx, dy))

            self.objects.append(Wall(kx2, ky, hx - 120, ky))

        else:
            self.status_message_signal.emit(f"Template necunoscut: {template_type}")
            return

        self.select_object(None)
        self.check_collisions()
        self.project_changed_signal.emit()
        self.update()
        self.status_message_signal.emit(f"Sablon {template_type} incarcat.")

    def get_content_bbox(self):
        """
                Calculeaza dreptunghiul minim care cuprinde toate obiectele (Bounding Box).
                Util pentru exportul imaginilor.
                Returns: QRectF
                """
        if not self.objects:
            return QRectF(0, 0, 800, 600)  # Default size

        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')

        found_objects = False

        for obj in self.objects:
            rect = None
            if hasattr(obj, 'rect'):
                rect = obj.rect
            elif isinstance(obj, Wall):
                x_coords = [obj.x1, obj.x2]
                y_coords = [obj.y1, obj.y2]
                rect = QRectF(min(x_coords), min(y_coords),
                              abs(obj.x2 - obj.x1), abs(obj.y2 - obj.y1))

            if rect:
                found_objects = True
                min_x = min(min_x, rect.left())
                min_y = min(min_y, rect.top())
                max_x = max(max_x, rect.right())
                max_y = max(max_y, rect.bottom())

        if not found_objects:
            return QRectF(0, 0, 800, 600)

        padding = 50
        return QRectF(min_x - padding, min_y - padding,
                      (max_x - min_x) + 2 * padding, (max_y - min_y) + 2 * padding)

    def save_to_image(self, file_path):
        """
                Exporta continutul canvas-ului intr-un fisier imagine.
                Args:
                    file_path (str): Calea completa a fisierului de destinatie.
                Returns: bool (Succes/Esec)
                """
        bbox = self.get_content_bbox()

        width = int(math.ceil(bbox.width()))
        height = int(math.ceil(bbox.height()))

        image = QPixmap(width, height)
        image.fill(Qt.white)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.translate(-bbox.x(), -bbox.y())

        if RoomFloor is not None:
            for obj in self.objects:
                if isinstance(obj, RoomFloor):
                    self.draw_room_floor(painter, obj)

        for obj in self.objects:
            if isinstance(obj, Wall):
                self.draw_wall(painter, obj)

        for obj in self.objects:
            if isinstance(obj, Window):
                self.draw_window(painter, obj)
            elif isinstance(obj, SvgFurnitureObject):
                obj.draw(painter)

        painter.end()
        return image.save(file_path)
