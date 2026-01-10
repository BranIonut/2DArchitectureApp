import os
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import QRectF, Qt, QByteArray, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QColor
class Wall:
    def __init__(self, x1, y1, x2, y2, thickness=10):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.thickness = thickness
        self.type = "wall"
        self.is_selected = False
        self.is_colliding = False
        self.is_structure = True

    @property
    def rect(self):
        min_x = min(self.x1, self.x2)
        min_y = min(self.y1, self.y2)
        w = abs(self.x2 - self.x1)
        h = abs(self.y2 - self.y1)
        return QRectF(min_x - 5, min_y - 5, w + 10, h + 10)

    def to_dict(self):
        return {
            "type": "wall",
            "x1": self.x1, "y1": self.y1,
            "x2": self.x2, "y2": self.y2,
            "thickness": self.thickness
        }

    @staticmethod
    def from_dict(data):
        return Wall(data["x1"], data["y1"], data["x2"], data["y2"], data.get("thickness", 10))

class Window:
    def __init__(self, x, y, width=100, height=15, rotation=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = rotation
        self.type = "window"
        self.is_selected = False
        self.is_colliding = False
        self.is_structure = True
        self.is_wall_attachment = True

    @property
    def rect(self):
        if abs(self.rotation) % 180 == 90:
            cx = self.x + self.width / 2
            cy = self.y + self.height / 2
            new_w = self.height
            new_h = self.width
            return QRectF(cx - new_w / 2, cy - new_h / 2, new_w, new_h)

        return QRectF(self.x, self.y, self.width, self.height)

    def to_dict(self):
        return {
            "type": "window",
            "x": self.x, "y": self.y,
            "width": self.width, "height": self.height,
            "rotation": self.rotation
        }

    @staticmethod
    def from_dict(data):
        return Window(data["x"], data["y"], data["width"], data["height"], data.get("rotation", 0))

class SvgFurnitureObject:
    def __init__(self, file_path, category="General", x=0, y=0, rotation=0, width=80, height=80):
        self.file_path = file_path

        path_str = str(file_path).lower().replace('\\', '/')
        filename = os.path.basename(file_path)
        self.name = os.path.splitext(filename)[0].replace('AdobeStock_', '').replace('_', ' ').title()

        self.category = category
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = rotation
        self.type = "svg_object"
        self.is_selected = False
        self.is_colliding = False

        if "doors/" in path_str or "door" in self.name.lower():
            self.is_structure = True
            self.is_wall_attachment = False
        else:
            self.is_structure = False
            self.is_wall_attachment = False

        self.renderer = None
        self.pixmap = None
        self.is_valid = False

        self._load_resource()

    def _load_resource(self):
        if not os.path.exists(self.file_path):
            return
        try:
            with open(self.file_path, 'rb') as f:
                header = f.read(4)
                f.seek(0)
                data = f.read()

            if header.startswith(b'\x89PNG') or header.startswith(b'\xff\xd8'):
                self.pixmap = QPixmap()
                if self.pixmap.loadFromData(data):
                    self.is_valid = True
            else:
                self.renderer = QSvgRenderer()
                content = data.decode('utf-8', errors='ignore').strip()
                if self.renderer.load(QByteArray(content.encode('utf-8'))):
                    self.is_valid = True
                else:
                    self.pixmap = QPixmap(self.file_path)
                    self.is_valid = not self.pixmap.isNull()
        except:
            pass

    @property
    def rect(self):
        if abs(self.rotation) % 180 == 90:
            cx = self.x + self.width / 2
            cy = self.y + self.height / 2
            new_w = self.height
            new_h = self.width
            new_x = cx - new_w / 2
            new_y = cy - new_h / 2
            return QRectF(new_x, new_y, new_w, new_h)

        return QRectF(self.x, self.y, self.width, self.height)

    def move_to(self, pos):
        self.x = pos.x() - self.width / 2
        self.y = pos.y() - self.height / 2

    def contains(self, point):
        return self.rect.contains(point)

    def draw(self, painter):
        if not self.is_valid:
            return

        painter.save()
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        painter.translate(cx, cy)
        painter.rotate(self.rotation)
        painter.translate(-cx, -cy)

        target = QRectF(self.x, self.y, self.width, self.height)

        if self.renderer and self.renderer.isValid():
            self.renderer.render(painter, target)
        elif self.pixmap:
            painter.drawPixmap(target.toRect(), self.pixmap)

        if self.is_selected or self.is_colliding:
            pen = painter.pen()
            if self.is_colliding:
                pen.setColor(QColor(255, 69, 0))
                pen.setStyle(Qt.SolidLine)
                pen.setWidth(3)
            else:
                pen.setColor(Qt.red)
                pen.setStyle(Qt.DashLine)
                pen.setWidth(2)

            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(target)

        painter.restore()

    def to_dict(self):
        return {
            "type": "svg_object",
            "file_path": self.file_path,
            "category": self.category,
            "x": self.x, "y": self.y,
            "width": self.width, "height": self.height,
            "rotation": self.rotation
        }

    @staticmethod
    def from_dict(data):
        return SvgFurnitureObject(
            data.get("file_path", ""),
            data.get("category", "General"),
            data.get("x", 0), data.get("y", 0),
            data.get("rotation", 0),
            data.get("width", 80), data.get("height", 80)
        )