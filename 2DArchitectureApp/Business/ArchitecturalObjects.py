import uuid
from typing import Dict, Tuple, Optional
from enum import Enum


class ObjectType(Enum):
    #tipuri obiecte
    WALL = "wall"
    DOOR = "door"
    WINDOW = "window"
    FURNITURE = "furniture"


class ArchitecturalObject:
    #clasa pentru toate obiectele

    def __init__(self, x: float, y: float, width: float, height: float):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = 0.0  # în grade
        self.layer = "structure"
        self.color = "#000000"
        self.selected = False

    def to_dict(self) -> Dict:
        #convertire obiect pentru salvare
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'rotation': self.rotation,
            'layer': self.layer,
            'color': self.color
        }

    @classmethod
    def from_dict(cls, data: Dict):
        #creaza obiect dictionar
        obj = cls(
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 0),
            height=data.get('height', 0)
        )
        obj.id = data.get('id', str(uuid.uuid4()))
        obj.rotation = data.get('rotation', 0.0)
        obj.layer = data.get('layer', 'structure')
        obj.color = data.get('color', '#000000')
        return obj

    def get_bounds(self) -> Tuple[float, float, float, float]:
        #returneaza limite obiect
        return self.x, self.y, self.width, self.height

    def get_center(self) -> Tuple[float, float]:
        #returneaza centru obiect
        return self.x + self.width / 2, self.y + self.height / 2

    def set_position(self, x: float, y: float):
        #pozitia obiectului
        self.x = x
        self.y = y

    def set_size(self, width: float, height: float):
        #seteaza dimensiune obiect
        self.width = width
        self.height = height

    def set_rotation(self, angle: float):
        #rotatie obiect
        self.rotation = angle % 360

    def contains_point(self, px: float, py: float) -> bool:
        #punctul e in interiorul obiectului?
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)


class Wall(ArchitecturalObject):
    #clasa pereti

    def __init__(self, x: float, y: float, x2: float, y2: float, thickness: float = 20):
        # calculeaza h si w
        width = abs(x2 - x)
        height = abs(y2 - y)

        super().__init__(min(x, x2), min(y, y2), max(width, thickness), max(height, thickness))

        self.x1 = x
        self.y1 = y
        self.x2 = x2
        self.y2 = y2
        self.thickness = thickness
        self.layer = "structure"
        self.color = "#495867"

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'x1': self.x1,
            'y1': self.y1,
            'x2': self.x2,
            'y2': self.y2,
            'thickness': self.thickness
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict):
        wall = cls(
            x=data.get('x1', 0),
            y=data.get('y1', 0),
            x2=data.get('x2', 0),
            y2=data.get('y2', 0),
            thickness=data.get('thickness', 20)
        )
        wall.id = data.get('id', str(uuid.uuid4()))
        wall.rotation = data.get('rotation', 0.0)
        wall.layer = data.get('layer', 'structure')
        wall.color = data.get('color', '#495867')
        return wall

    def get_length(self) -> float:
        #returneaza lungime proiect
        import math
        return math.sqrt((self.x2 - self.x1) ** 2 + (self.y2 - self.y1) ** 2)


class Door(ArchitecturalObject):
    #clasa pt usi

    def __init__(self, x: float, y: float, width: float = 80, height: float = 20):
        super().__init__(x, y, width, height)
        self.layer = "doors_windows"
        self.color = "#A88F6E"
        self.opening_direction = "right"  # right, left
        self.opening_angle = 90  # grade

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'opening_direction': self.opening_direction,
            'opening_angle': self.opening_angle
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict):
        door = cls(
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 80),
            height=data.get('height', 20)
        )
        door.id = data.get('id', str(uuid.uuid4()))
        door.rotation = data.get('rotation', 0.0)
        door.layer = data.get('layer', 'doors_windows')
        door.color = data.get('color', '#A88F6E')
        door.opening_direction = data.get('opening_direction', 'right')
        door.opening_angle = data.get('opening_angle', 90)
        return door


class Window(ArchitecturalObject):
    #clasa ferestre

    def __init__(self, x: float, y: float, width: float = 100, height: float = 20):
        super().__init__(x, y, width, height)
        self.layer = "doors_windows"
        self.color = "#7CB9E8"

    def to_dict(self) -> Dict:
        return super().to_dict()

    @classmethod
    def from_dict(cls, data: Dict):
        window = cls(
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 100),
            height=data.get('height', 20)
        )
        window.id = data.get('id', str(uuid.uuid4()))
        window.rotation = data.get('rotation', 0.0)
        window.layer = data.get('layer', 'doors_windows')
        window.color = data.get('color', '#7CB9E8')
        return window


class Furniture(ArchitecturalObject):
    #clasa mobilier

    def __init__(self, x: float, y: float, width: float, height: float,
                 furniture_type: str = "generic"):
        super().__init__(x, y, width, height)
        self.layer = "furniture"
        self.color = "#587B7F"
        self.furniture_type = furniture_type  # bed, table, chair, etc.
        self.category = "generic"  # bedroom, living, kitchen, bathroom, office

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'furniture_type': self.furniture_type,
            'category': self.category
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict):
        furniture = cls(
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 50),
            height=data.get('height', 50),
            furniture_type=data.get('furniture_type', 'generic')
        )
        furniture.id = data.get('id', str(uuid.uuid4()))
        furniture.rotation = data.get('rotation', 0.0)
        furniture.layer = data.get('layer', 'furniture')
        furniture.color = data.get('color', '#587B7F')
        furniture.category = data.get('category', 'generic')
        return furniture


class Transform:
    @staticmethod
    def rotate(obj: ArchitecturalObject, angle: float, center: Optional[Tuple[float, float]] = None):
        #rotire obiect
        if center is None:
            center = obj.get_center()

        obj.set_rotation(obj.rotation + angle)

    @staticmethod
    def scale(obj: ArchitecturalObject, scale_x: float, scale_y: float):
        #selectie obiect
        new_width = obj.width * scale_x
        new_height = obj.height * scale_y
        obj.set_size(new_width, new_height)

    @staticmethod
    def translate(obj: ArchitecturalObject, dx: float, dy: float):
        obj.set_position(obj.x + dx, obj.y + dy)
        #translare obiect

    @staticmethod
    def resize(obj: ArchitecturalObject, new_width: float, new_height: float,
               anchor: str = "center"):
        #redimensionare
        old_width = obj.width
        old_height = obj.height

        if anchor == "center":
            center_x, center_y = obj.get_center()
            obj.set_size(new_width, new_height)
            obj.set_position(center_x - new_width / 2, center_y - new_height / 2)
        elif anchor == "topleft":
            obj.set_size(new_width, new_height)
        elif anchor == "topright":
            obj.set_size(new_width, new_height)
            obj.set_position(obj.x + old_width - new_width, obj.y)
        elif anchor == "bottomleft":
            obj.set_size(new_width, new_height)
            obj.set_position(obj.x, obj.y + old_height - new_height)
        elif anchor == "bottomright":
            obj.set_size(new_width, new_height)
            obj.set_position(obj.x + old_width - new_width, obj.y + old_height - new_height)