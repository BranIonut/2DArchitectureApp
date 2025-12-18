#optional in aceasta etapa2

from typing import List
from .ArchitecturalObjects import Wall, Door, Window, Furniture, ArchitecturalObject


class CollisionDetector:
##asdas

    def collides(self, new_obj: ArchitecturalObject,
                 objects: List[ArchitecturalObject]) -> bool:


        for obj in objects:
            if obj is new_obj:
                continue


            if isinstance(new_obj, Wall) and isinstance(obj, Wall):
                if self._walls_intersect(new_obj, obj):
                    return True


            else:
                if self._bbox_intersect(new_obj, obj):
                    return True

        return False

    @staticmethod
    def _bbox(obj):

        return obj.x, obj.y, obj.width, obj.height

    @staticmethod
    def _rects_overlap(a, b) -> bool:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return not (
            ax + aw <= bx or
            bx + bw <= ax or
            ay + ah <= by or
            by + bh <= ay
        )

    @staticmethod
    def _lines_intersect(w1: Wall, w2: Wall) -> bool:


        def ccw(A, B, C):
            return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

        A = (w1.x1, w1.y1)
        B = (w1.x2, w1.y2)
        C = (w2.x1, w2.y1)
        D = (w2.x2, w2.y2)

        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

    @staticmethod
    def _parallel(w1: Wall, w2: Wall) -> bool:
        dx1 = w1.x2 - w1.x1
        dy1 = w1.y2 - w1.y1
        dx2 = w2.x2 - w2.x1
        dy2 = w2.y2 - w2.y1
        return abs(dx1 * dy2 - dy1 * dx2) < 1e-6


    @classmethod
    def can_add_wall(cls, new_wall: Wall, walls: List[Wall]) -> bool:
        for w in walls:

            if cls._lines_intersect(new_wall, w):
                return False


            if cls._parallel(new_wall, w):
                if cls._rects_overlap(
                    cls.wall_bbox(new_wall),
                    cls.wall_bbox(w)
                ):
                    return False

        return True

    @staticmethod
    def wall_bbox(w: Wall):
        x = min(w.x1, w.x2)
        y = min(w.y1, w.y2)
        return x, y, abs(w.x2 - w.x1), abs(w.y2 - w.y1)



    @classmethod
    def can_add_opening(cls, obj, walls: List[Wall], others: List[ArchitecturalObject]) -> bool:
        """Ușă sau fereastră trebuie să fie pe un perete."""

        on_wall = False
        for w in walls:
            if cls._rects_overlap(cls._bbox(obj), cls.wall_bbox(w)):
                on_wall = True
                break

        if not on_wall:
            return False

        for o in others:
            if cls._rects_overlap(cls._bbox(obj), cls._bbox(o)):
                return False

        return True


    @classmethod
    def can_add_furniture(cls, furn: Furniture,
                          walls: List[Wall],
                          openings: List[ArchitecturalObject]) -> bool:

        for w in walls:
            if cls._rects_overlap(cls._bbox(furn), cls.wall_bbox(w)):
                return False

        for o in openings:
            if cls._rects_overlap(cls._bbox(furn), cls._bbox(o)):
                return False

        return True



    @classmethod
    def can_move_object(cls, obj: ArchitecturalObject,
                        others: List[ArchitecturalObject]) -> bool:

        for o in others:
            if o is obj:
                continue

            if cls._rects_overlap(cls._bbox(obj), cls._bbox(o)):
                return False

        return True
