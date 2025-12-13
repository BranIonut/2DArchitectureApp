from typing import Optional, List, Dict
import copy

from .Project import Project
from .ArchitecturalObjects import (
    ArchitecturalObject, Wall, Door, Window, Furniture, Transform
)
from .CoordinateSystem import CoordinateSystem


class ProjectManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProjectManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self.current_project: Optional[Project] = None


        self.view_scale: float = 1.0
        self.coordinate_system = CoordinateSystem(grid_size=10, scale=1.0)

        self._walls: List[Wall] = []
        self._doors: List[Door] = []
        self._windows: List[Window] = []
        self._furniture: List[Furniture] = []

        self.selected_object: Optional[ArchitecturalObject] = None


        self._history: List[Dict] = []
        self._history_index = -1


    def _get_snapshot(self) -> Dict:
        return {
            "project": copy.deepcopy(self.current_project),
            "walls": copy.deepcopy(self._walls),
            "doors": copy.deepcopy(self._doors),
            "windows": copy.deepcopy(self._windows),
            "furniture": copy.deepcopy(self._furniture),
            "selected": self.selected_object.id if self.selected_object else None
        }

    def _push_history(self):
        if not self.current_project:
            return

        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]

        self._history.append(self._get_snapshot())
        self._history_index += 1

    def _restore(self, snapshot: Dict):
        self.current_project = snapshot["project"]
        self._walls = snapshot["walls"]
        self._doors = snapshot["doors"]
        self._windows = snapshot["windows"]
        self._furniture = snapshot["furniture"]

        sel = snapshot["selected"]

        self.selected_object = None
        for obj in self.get_all_objects():
            obj.selected = False
            if sel and obj.id == sel:
                obj.selected = True
                self.selected_object = obj

    def undo(self) -> bool:
        if self._history_index <= 0:
            return False

        self._history_index -= 1
        snap = self._history[self._history_index]
        self._restore(snap)
        return True

    def redo(self) -> bool:
        if self._history_index >= len(self._history) - 1:
            return False

        self._history_index += 1
        snap = self._history[self._history_index]
        self._restore(snap)
        return True

    def set_view_scale(self, value: float):
        self.view_scale = max(0.1, min(10.0, value))

    def get_view_scale(self) -> float:
        return self.view_scale


    def create_new_project(self, name="Proiect Nou", width=1000, height=800):
        self.current_project = Project(name, width, height)

        self._clear_cache()

        self._history = []
        self._history_index = -1

        # reset view
        self.view_scale = 1.0
        self.coordinate_system = CoordinateSystem(grid_size=10, scale=1.0)

        self._push_history()

        return self.current_project

    def save_project(self, filepath=None):
        if not self.current_project:
            return False

        self._sync_to_project()
        return self.current_project.save(filepath)

    def load_project(self, filepath):
        project = Project.load(filepath)
        if not project:
            return False

        self.current_project = project
        self._rebuild_cache()
        self._push_history()
        return True



    def _clear_cache(self):
        self._walls = []
        self._doors = []
        self._windows = []
        self._furniture = []
        self.selected_object = None

    def _rebuild_cache(self):
        self._clear_cache()

        for w in self.current_project.walls:
            self._walls.append(Wall.from_dict(w))
        for d in self.current_project.doors:
            self._doors.append(Door.from_dict(d))
        for w in self.current_project.windows:
            self._windows.append(Window.from_dict(w))
        for f in self.current_project.furniture:
            self._furniture.append(Furniture.from_dict(f))

    def _sync_to_project(self):
        self.current_project.walls = [w.to_dict() for w in self._walls]
        self.current_project.doors = [d.to_dict() for d in self._doors]
        self.current_project.windows = [w.to_dict() for w in self._windows]
        self.current_project.furniture = [f.to_dict() for f in self._furniture]



    def add_wall(self, x1, y1, x2, y2, t=20):
        wall = Wall(x1, y1, x2, y2, t)
        self._walls.append(wall)

        self._sync_to_project()
        self._push_history()

        return wall

    def add_door(self, x, y, w, h):
        d = Door(x, y, w, h)
        self._doors.append(d)

        self._sync_to_project()
        self._push_history()

        return d

    def add_window(self, x, y, w, h):
        win = Window(x, y, w, h)
        self._windows.append(win)

        self._sync_to_project()
        self._push_history()

        return win

    def add_furniture(self, x, y, w, h, t="generic"):
        f = Furniture(x, y, w, h, t)
        self._furniture.append(f)

        self._sync_to_project()
        self._push_history()

        return f

    def remove_object(self, obj):

        if isinstance(obj, Wall):
            self._walls.remove(obj)
        elif isinstance(obj, Door):
            self._doors.remove(obj)
        elif isinstance(obj, Window):
            self._windows.remove(obj)
        elif isinstance(obj, Furniture):
            self._furniture.remove(obj)

        self.selected_object = None

        self._sync_to_project()
        self._push_history()



    def get_all_objects(self):
        return self._walls + self._doors + self._windows + self._furniture

    def select_object(self, obj):
        if self.selected_object:
            self.selected_object.selected = False
        self.selected_object = obj
        if obj:
            obj.selected = True

    def find_object_at(self, x, y):
        for obj in reversed(self.get_all_objects()):
            if obj.contains_point(x, y):
                return obj
        return None

    def translate_selected(self, dx, dy):
        if not self.selected_object:
            return
        Transform.translate(self.selected_object, dx, dy)
        self._sync_to_project()



    def get_statistics(self):
        if not self.current_project:
            return {}

        total_len = sum(w.get_length() for w in self._walls)
        real_len = self.coordinate_system.pixels_to_real_units(total_len)

        return {
            "project_name": self.current_project.name,
            "total_objects": len(self.get_all_objects()),
            "walls_count": len(self._walls),
            "doors_count": len(self._doors),
            "windows_count": len(self._windows),
            "furniture_count": len(self._furniture),
            "total_wall_length": self.coordinate_system.format_distance(real_len),
            "canvas_width": self.current_project.width,
            "canvas_height": self.current_project.height,
            "grid_size": self.current_project.grid_size,
            "snap_to_grid": self.current_project.snap_to_grid,
            "grid_visible": self.current_project.grid_visible
        }
