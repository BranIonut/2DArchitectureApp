class Command:
    """
    Interfata abstracta pentru toate comenzile executabile si reversibile.
    """
    def execute(self):
        """ Executa actiunea. """
        pass

    def undo(self):
        """ Inverseaza actiunea (revine la starea anterioara). """
        pass


class UndoStack:
    """
    Gestioneaza stiva de comenzi pentru Undo/Redo.
    Pastreaza istoricul actiunilor si permite navigarea inainte/inapoi.
    """

    def __init__(self, capacity=50):
        self.history = []
        self.redo_stack = []
        self.capacity = capacity

    def push(self, command):
        """
        Adauga o noua comanda in istoric si curata stiva de redo.
        Daca se depaseste capacitatea, sterge cele mai vechi comenzi.
        """
        self.history.append(command)
        self.redo_stack.clear()  # O actiune noua invalideaza viitorul (redo)

        if len(self.history) > self.capacity:
            self.history.pop(0)

    def undo(self):
        """ Executa undo pentru ultima comanda si o muta in redo_stack. """
        if not self.history:
            return

        command = self.history.pop()
        command.undo()
        self.redo_stack.append(command)

    def redo(self):
        """ Executa redo pentru ultima comanda anulata. """
        if not self.redo_stack:
            return

        command = self.redo_stack.pop()
        command.execute()
        self.history.append(command)

class AddObjectCommand(Command):
    def __init__(self, objects_list, new_object):
        self.objects_list = objects_list
        self.new_object = new_object

    def execute(self):
        if self.new_object not in self.objects_list:
            self.objects_list.append(self.new_object)

    def undo(self):
        if self.new_object in self.objects_list:
            self.objects_list.remove(self.new_object)


class DeleteObjectCommand(Command):
    def __init__(self, objects_list, obj_to_delete):
        self.objects_list = objects_list
        self.obj = obj_to_delete
        self.index = -1

    def execute(self):
        if self.obj in self.objects_list:
            self.index = self.objects_list.index(self.obj)
            self.objects_list.remove(self.obj)

    def undo(self):
        if self.index != -1:
            self.objects_list.insert(self.index, self.obj)
        else:
            self.objects_list.append(self.obj)


class MoveObjectCommand(Command):
    def __init__(self, obj, old_pos, new_pos):
        self.obj = obj
        self.old_x, self.old_y = old_pos
        self.new_x, self.new_y = new_pos

    def execute(self):
        self.obj.x = self.new_x
        self.obj.y = self.new_y

    def undo(self):
        self.obj.x = self.old_x
        self.obj.y = self.old_y


class MoveWallCommand(Command):
    def __init__(self, wall, old_coords, new_coords):
        self.wall = wall
        self.ox1, self.oy1, self.ox2, self.oy2 = old_coords
        self.nx1, self.ny1, self.nx2, self.ny2 = new_coords

    def execute(self):
        self.wall.x1, self.wall.y1 = self.nx1, self.ny1
        self.wall.x2, self.wall.y2 = self.nx2, self.ny2

    def undo(self):
        self.wall.x1, self.wall.y1 = self.ox1, self.oy1
        self.wall.x2, self.wall.y2 = self.ox2, self.oy2


class RotateObjectCommand(Command):
    def __init__(self, obj, old_angle, new_angle):
        self.obj = obj
        self.old_angle = old_angle
        self.new_angle = new_angle

    def execute(self):
        self.obj.rotation = self.new_angle

    def undo(self):
        self.obj.rotation = self.old_angle


class ResizeObjectCommand(Command):
    def __init__(self, obj, old_rect, new_rect):
        """ rects are tuples: (x, y, w, h) """
        self.obj = obj
        self.ox, self.oy, self.ow, self.oh = old_rect
        self.nx, self.ny, self.nw, self.nh = new_rect

    def execute(self):
        self.obj.x, self.obj.y = self.nx, self.ny
        self.obj.width, self.obj.height = self.nw, self.nh

    def undo(self):
        self.obj.x, self.obj.y = self.ox, self.oy
        self.obj.width, self.obj.height = self.ow, self.oh
