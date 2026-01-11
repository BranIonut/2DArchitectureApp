from .Project import Project
from .ArchitecturalObjects import SvgFurnitureObject, Wall, Window


class ProjectManager:
    """
        Clasa Singleton responsabila de gestionarea ciclului de viata al proiectului curent.
        Asigura ca exista o singura instanta activa a proiectului in aplicatie.
        """
    _instance = None

    def __new__(cls):
        """ Implementare sablon Singleton. """
        if cls._instance is None:
            cls._instance = super(ProjectManager, cls).__new__(cls)
            cls._instance.current_project = None
        return cls._instance

    def create_new_project(self, name):
        """ Initializeaza un proiect nou gol. """
        self.current_project = Project(name)
        return self.current_project

    def save_project(self, filepath, objects_list):
        """
                Salveaza starea curenta a proiectului pe disk.
                Daca nu exista proiect, creeaza unul temporar.
                """
        if not self.current_project:
            self.create_new_project("Untitled")
        return self.current_project.save(filepath, objects_list)

    def load_project(self, filepath):
        """
                Incarca un proiect din fisier si reconstruieste lista de obiecte
                folosind metodele factory 'from_dict' ale fiecarei clase.
                """
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
                    elif obj_type == "room_floor":
                        restored_objects.append(RoomFloor.from_dict(item))
                    else:
                        restored_objects.append(SvgFurnitureObject.from_dict(item))
                except Exception as e:
                    print(f"Eroare la restaurarea obiectului: {e}")
                    continue

            return restored_objects
        return None