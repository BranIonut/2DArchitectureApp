import json
import os
from datetime import datetime


class Project:
    def __init__(self, name="Proiect Nou", width=2000, height=2000):
        self.name = name
        self.width = width
        self.height = height
        self.created_date = datetime.now().isoformat()
        self.modified_date = datetime.now().isoformat()

        # Setari
        self.grid_size = 20
        self.grid_visible = True
        self.snap_to_grid = True

        # Container de date
        self.objects = []

    def save(self, filepath, object_instances):
        try:
            self.modified_date = datetime.now().isoformat()

            # Serializare: converteste instantele in dictionare
            serialized_objects = []
            for obj in object_instances:
                if hasattr(obj, 'to_dict'):
                    serialized_objects.append(obj.to_dict())

            data = {
                "name": self.name,
                "width": self.width,
                "height": self.height,
                "created_date": self.created_date,
                "modified_date": self.modified_date,
                "grid_size": self.grid_size,
                "grid_visible": self.grid_visible,
                "snap_to_grid": self.snap_to_grid,
                "objects": serialized_objects
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False

    @staticmethod
    def load(filepath):
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            project = Project(
                name=data.get("name", "Proiect Incarcat"),
                width=data.get("width", 2000),
                height=data.get("height", 2000)
            )

            project.created_date = data.get("created_date", project.created_date)
            project.modified_date = data.get("modified_date", project.modified_date)
            project.grid_size = data.get("grid_size", 20)
            project.grid_visible = data.get("grid_visible", True)
            project.snap_to_grid = data.get("snap_to_grid", True)

            project.objects = data.get("objects", [])

            return project
        except Exception as e:
            print(f"Error loading project: {e}")
            return None