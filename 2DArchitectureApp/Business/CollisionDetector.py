from .ArchitecturalObjects import SvgFurnitureObject


class CollisionDetector:
    """
        Clasa utilitara statica pentru detectarea coliziunilor intre obiecte 2D.
        Se bazeaza pe intersectia dreptunghiurilor de incadrare (Bounding Boxes).
        """
    @staticmethod
    def check_collision(obj1, obj2):
        """ Verifica daca doua obiecte se intersecteaza. """
        if obj1 is obj2:
            return False

        # Folosim metoda intersects din QRectF
        return obj1.rect.intersects(obj2.rect)

    @staticmethod
    def get_colliding_objects(target_obj, all_objects):
        """
                Returneaza o lista cu toate obiectele din 'all_objects' care
                se intersecteaza cu 'target_obj'.
                """
        collisions = []
        for obj in all_objects:
            if target_obj is not obj:
                if target_obj.rect.intersects(obj.rect):
                    collisions.append(obj)
        return collisions