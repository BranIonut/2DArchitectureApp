from typing import Optional, List, Dict
from .Project import Project
from .ArchitecturalObjects import (
    ArchitecturalObject, Wall, Door, Window, Furniture, Transform
)
from .CoordinateSystem import CoordinateSystem


class ProjectManager:
    #singelton pt proiectul activ
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProjectManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.current_project: Optional[Project] = None
        self.coordinate_system = CoordinateSystem(grid_size=10, scale=1.0)

        # cache-uri pentru obiecte
        self._walls: List[Wall] = []
        self._doors: List[Door] = []
        self._windows: List[Window] = []
        self._furniture: List[Furniture] = []

        # obiectul selectat curent
        self.selected_object: Optional[ArchitecturalObject] = None

        # starea undo/redo (simplificat)
        self._history: List[Dict] = []
        self._history_index = -1

    def create_new_project(self, name: str = "Proiect Nou",
                           width: int = 1000, height: int = 800) -> Project:
        #creare proiect nou
        self.current_project = Project(name, width, height)
        self._clear_caches()
        return self.current_project

    def load_project(self, filepath: str) -> bool:
        #incarca proiect intr un fisier
        project = Project.load(filepath)
        if project:
            self.current_project = project
            self._rebuild_caches()
            return True
        return False

    def save_project(self, filepath: str = None) -> bool:
        #salvare proeict curent
        if not self.current_project:
            return False

        #sincron cache-urile cu proiectul
        self._sync_to_project()
        return self.current_project.save(filepath)

    def _clear_caches(self):
        #stergere totala a cache ului
        self._walls.clear()
        self._doors.clear()
        self._windows.clear()
        self._furniture.clear()
        self.selected_object = None

    def _rebuild_caches(self):
        #reconstruire cache
        if not self.current_project:
            return

        self._clear_caches()

        #reconstruire pereti
        for wall_data in self.current_project.walls:
            wall = Wall.from_dict(wall_data)
            self._walls.append(wall)

        # rec usi
        for door_data in self.current_project.doors:
            door = Door.from_dict(door_data)
            self._doors.append(door)

        # rec fereste
        for window_data in self.current_project.windows:
            window = Window.from_dict(window_data)
            self._windows.append(window)

        # rec mobilier
        for furniture_data in self.current_project.furniture:
            furniture = Furniture.from_dict(furniture_data)
            self._furniture.append(furniture)

    def _sync_to_project(self):
        if not self.current_project:
            return

        self.current_project.walls = [w.to_dict() for w in self._walls]
        self.current_project.doors = [d.to_dict() for d in self._doors]
        self.current_project.windows = [w.to_dict() for w in self._windows]
        self.current_project.furniture = [f.to_dict() for f in self._furniture]

    #operatii pereti
    def add_wall(self, x1: float, y1: float, x2: float, y2: float,
                 thickness: float = 20) -> Wall:
        #adauga perete nou
        if self.current_project and self.current_project.snap_to_grid:
            x1, y1 = self.coordinate_system.snap_to_grid(x1, y1)
            x2, y2 = self.coordinate_system.snap_to_grid(x2, y2)

        wall = Wall(x1, y1, x2, y2, thickness)
        self._walls.append(wall)

        if self.current_project:
            self.current_project.add_wall(wall.to_dict())

        return wall

    def get_walls(self) -> List[Wall]:
        #lista pereti
        return self._walls.copy()

    #operatii usi
    def add_door(self, x: float, y: float, width: float = 80,
                 height: float = 20) -> Door:
        #usa noua
        if self.current_project and self.current_project.snap_to_grid:
            x, y = self.coordinate_system.snap_to_grid(x, y)

        door = Door(x, y, width, height)
        self._doors.append(door)

        if self.current_project:
            self.current_project.add_door(door.to_dict())

        return door

    def get_doors(self) -> List[Door]:
        return self._doors.copy()

    #operatii ferestre
    def add_window(self, x: float, y: float, width: float = 100,
                   height: float = 20) -> Window:
        if self.current_project and self.current_project.snap_to_grid:
            x, y = self.coordinate_system.snap_to_grid(x, y)

        window = Window(x, y, width, height)
        self._windows.append(window)

        if self.current_project:
            self.current_project.add_window(window.to_dict())

        return window

    def get_windows(self) -> List[Window]:
        return self._windows.copy()


        #ooeratii mobilier
    def add_furniture(self, x: float, y: float, width: float, height: float,
                      furniture_type: str = "generic") -> Furniture:
        if self.current_project and self.current_project.snap_to_grid:
            x, y = self.coordinate_system.snap_to_grid(x, y)

        furniture = Furniture(x, y, width, height, furniture_type)
        self._furniture.append(furniture)

        if self.current_project:
            self.current_project.add_furniture(furniture.to_dict())

        return furniture

    def get_furniture(self) -> List[Furniture]:
        return self._furniture.copy()


    def get_all_objects(self) -> List[ArchitecturalObject]:
        #returneaza toate obiectele din proiect
        all_objects = []
        all_objects.extend(self._walls)
        all_objects.extend(self._doors)
        all_objects.extend(self._windows)
        all_objects.extend(self._furniture)
        return all_objects

    def remove_object(self, obj: ArchitecturalObject) -> bool:
        #sterge un obiect din proiect
        try:
            if isinstance(obj, Wall):
                self._walls.remove(obj)
                if self.current_project:
                    self.current_project.remove_object('wall', obj.id)
            elif isinstance(obj, Door):
                self._doors.remove(obj)
                if self.current_project:
                    self.current_project.remove_object('door', obj.id)
            elif isinstance(obj, Window):
                self._windows.remove(obj)
                if self.current_project:
                    self.current_project.remove_object('window', obj.id)
            elif isinstance(obj, Furniture):
                self._furniture.remove(obj)
                if self.current_project:
                    self.current_project.remove_object('furniture', obj.id)

            if self.selected_object == obj:
                self.selected_object = None

            return True
        except ValueError:
            return False

    def find_object_at_position(self, x: float, y: float) -> Optional[ArchitecturalObject]:
        # cauta ultimul obiect pus (sunt deasupra)
        all_objects = self.get_all_objects()

        for obj in reversed(all_objects):
            if obj.contains_point(x, y):
                return obj

        return None

    def select_object(self, obj: Optional[ArchitecturalObject]):
        # deselectare obiectul anterior
        if self.selected_object:
            self.selected_object.selected = False

        # select noul obiect
        self.selected_object = obj
        if obj:
            obj.selected = True

    def get_selected_object(self) -> Optional[ArchitecturalObject]:
        return self.selected_object


    def rotate_selected(self, angle: float):
        if self.selected_object:
            Transform.rotate(self.selected_object, angle)
            self._sync_to_project()

    def scale_selected(self, scale_x: float, scale_y: float):
        if self.selected_object:
            Transform.scale(self.selected_object, scale_x, scale_y)
            self._sync_to_project()

    def translate_selected(self, dx: float, dy: float):
        if self.selected_object:
            Transform.translate(self.selected_object, dx, dy)
            self._sync_to_project()

    def resize_selected(self, new_width: float, new_height: float, anchor: str = "center"):
        if self.selected_object:
            Transform.resize(self.selected_object, new_width, new_height, anchor)
            self._sync_to_project()

    def set_grid_size(self, size: int):
        self.coordinate_system.set_grid_size(size)
        if self.current_project:
            self.current_project.grid_size = size

    def toggle_grid_visibility(self):
        if self.current_project:
            self.current_project.grid_visible = not self.current_project.grid_visible

    def toggle_snap_to_grid(self):
        if self.current_project:
            self.current_project.snap_to_grid = not self.current_project.snap_to_grid

    def get_grid_visible(self) -> bool:
        return self.current_project.grid_visible if self.current_project else True

    def get_snap_to_grid(self) -> bool:
        return self.current_project.snap_to_grid if self.current_project else True