from .ArchitecturalObjects import SvgFurnitureObject


class CollisionDetector:
    @staticmethod
    def check_collision(obj1, obj2):
        if obj1 is obj2:
            return False

        # Folosim metoda intersects din QRectF
        return obj1.rect.intersects(obj2.rect)

    @staticmethod
    def get_colliding_objects(target_obj, all_objects):
        collisions = []
        for obj in all_objects:
            if target_obj is not obj:
                if target_obj.rect.intersects(obj.rect):
                    collisions.append(obj)
        return collisions