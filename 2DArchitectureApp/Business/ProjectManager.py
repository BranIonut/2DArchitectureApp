from .Project import Project
from .ArchitecturalObjects import SvgFurnitureObject, Wall, Window


class ProjectManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProjectManager, cls).__new__(cls)
            cls._instance.current_project = None
        return cls._instance

    def create_new_project(self, name):
        self.current_project = Project(name)
        return self.current_project

    def save_project(self, filepath, objects_list):
        if not self.current_project:
            self.create_new_project("Untitled")
        return self.current_project.save(filepath, objects_list)

    def load_project(self, filepath):
        loaded_project = Project.load(filepath)
        if loaded_project:
            self.current_project = loaded_project

            restored_objects = []
            for item in self.current_project.objects:
                try:
                    obj_type = item.get("type", "svg_object")

                    if obj_type == "wall":
                        restored_objects.append(Wall.from_dict(item))
                    elif obj_type == "window":
                        restored_objects.append(Window.from_dict(item))
                    else:
                        # aici intra SVG-uri
                        restored_objects.append(SvgFurnitureObject.from_dict(item))
                except Exception as e:
                    print(f"Eroare la restaurarea obiectului: {e}")
                    continue

            return restored_objects
        return None