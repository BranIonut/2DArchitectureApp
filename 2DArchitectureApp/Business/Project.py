import json
import os
from datetime import datetime
from typing import Optional, Dict, List


class Project:
    #creare deschidere salvare proiect
    def __init__(self, name: str = "Proiect Nou", width: int = 1000, height: int = 800):
        self.name = name
        self.width = width  # dimensiune canvas in pixeli
        self.height = height
        self.created_date = datetime.now().isoformat()
        self.modified_date = datetime.now().isoformat()
        self.filepath: Optional[str] = None

        # Lista de obiecte din proiect
        self.walls: List[Dict] = []
        self.doors: List[Dict] = []
        self.windows: List[Dict] = []
        self.furniture: List[Dict] = []

        # Setari grid
        self.grid_size = 10  # dimensiune celula grid in pixeli
        self.grid_visible = True
        self.snap_to_grid = True

        # Setari vizualizare
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Layers (straturi)
        self.layers = {
            'structure': {'visible': True, 'locked': False},
            'doors_windows': {'visible': True, 'locked': False},
            'furniture': {'visible': True, 'locked': False},
            'annotations': {'visible': True, 'locked': False}
        }

    def save(self, filepath: str = None) -> bool:
        #salvare json
        try:
            if filepath:
                self.filepath = filepath

            if not self.filepath:
                return False

            self.modified_date = datetime.now().isoformat()

            project_data = {
                'name': self.name,
                'width': self.width,
                'height': self.height,
                'created_date': self.created_date,
                'modified_date': self.modified_date,
                'walls': self.walls,
                'doors': self.doors,
                'windows': self.windows,
                'furniture': self.furniture,
                'grid_size': self.grid_size,
                'grid_visible': self.grid_visible,
                'snap_to_grid': self.snap_to_grid,
                'zoom_level': self.zoom_level,
                'pan_x': self.pan_x,
                'pan_y': self.pan_y,
                'layers': self.layers
            }

            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=4, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Eroare la salvarea proiectului: {e}")
            return False

    @staticmethod
    def load(filepath: str) -> Optional['Project']:
        """Încarcă un proiect din fișier JSON"""
        try:
            if not os.path.exists(filepath):
                return None

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            project = Project(
                name=data.get('name', 'Proiect'),
                width=data.get('width', 1000),
                height=data.get('height', 800)
            )

            project.filepath = filepath
            project.created_date = data.get('created_date', project.created_date)
            project.modified_date = data.get('modified_date', project.modified_date)

            project.walls = data.get('walls', [])
            project.doors = data.get('doors', [])
            project.windows = data.get('windows', [])
            project.furniture = data.get('furniture', [])

            project.grid_size = data.get('grid_size', 10)
            project.grid_visible = data.get('grid_visible', True)
            project.snap_to_grid = data.get('snap_to_grid', True)

            project.zoom_level = data.get('zoom_level', 1.0)
            project.pan_x = data.get('pan_x', 0)
            project.pan_y = data.get('pan_y', 0)

            project.layers = data.get('layers', project.layers)

            return project

        except Exception as e:
            print(f"Eroare la încărcarea proiectului: {e}")
            return None

    def add_wall(self, wall_data: Dict):
        """Adaugă un perete în proiect"""
        self.walls.append(wall_data)
        self.modified_date = datetime.now().isoformat()

    def add_door(self, door_data: Dict):
        """Adaugă o ușă în proiect"""
        self.doors.append(door_data)
        self.modified_date = datetime.now().isoformat()

    def add_window(self, window_data: Dict):
        """Adaugă o fereastră în proiect"""
        self.windows.append(window_data)
        self.modified_date = datetime.now().isoformat()

    def add_furniture(self, furniture_data: Dict):
        """Adaugă mobilier în proiect"""
        self.furniture.append(furniture_data)
        self.modified_date = datetime.now().isoformat()

    def remove_object(self, obj_type: str, obj_id: str) -> bool:
        """Șterge un obiect din proiect"""
        try:
            if obj_type == 'wall':
                self.walls = [w for w in self.walls if w.get('id') != obj_id]
            elif obj_type == 'door':
                self.doors = [d for d in self.doors if d.get('id') != obj_id]
            elif obj_type == 'window':
                self.windows = [w for w in self.windows if w.get('id') != obj_id]
            elif obj_type == 'furniture':
                self.furniture = [f for f in self.furniture if f.get('id') != obj_id]
            else:
                return False

            self.modified_date = datetime.now().isoformat()
            return True

        except Exception as e:
            print(f"Eroare la ștergerea obiectului: {e}")
            return False

    def clear(self):
        """Șterge toate obiectele din proiect"""
        self.walls.clear()
        self.doors.clear()
        self.windows.clear()
        self.furniture.clear()
        self.modified_date = datetime.now().isoformat()

    def get_all_objects(self) -> List[Dict]:
        """Returnează toate obiectele din proiect"""
        all_objects = []

        for wall in self.walls:
            wall['type'] = 'wall'
            all_objects.append(wall)

        for door in self.doors:
            door['type'] = 'door'
            all_objects.append(door)

        for window in self.windows:
            window['type'] = 'window'
            all_objects.append(window)

        for item in self.furniture:
            item['type'] = 'furniture'
            all_objects.append(item)

        return all_objects