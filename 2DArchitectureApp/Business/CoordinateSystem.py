import math
from typing import Tuple, List


class CoordinateSystem:
    """
        Ofera metode utilitare pentru gestionarea sistemului de coordonate,
        conversii unitati (pixeli <-> metri) si calcule geometrice vectoriale.
        """

    def __init__(self, grid_size: int = 20, scale: float = 1.0):
        self.grid_size = grid_size
        self.scale = scale
        # Unitatea curenta de afisare ('m', 'cm', 'mm')
        self.display_unit = 'm'

    def set_display_unit(self, unit: str):
        """ Seteaza unitatea de masura pentru afisare (m, cm, mm). """
        if unit in ['m', 'cm', 'mm']:
            self.display_unit = unit

    def pixels_to_current_unit(self, pixels: float) -> float:
        """ Converteste pixelii in valoarea numerica a unitatii curente. """
        # Baza: 100px = 1m
        meters = pixels / 100.0

        if self.display_unit == 'm':
            return meters
        elif self.display_unit == 'cm':
            return meters * 100.0
        elif self.display_unit == 'mm':
            return meters * 1000.0
        return meters

    def pixels_to_real_units(self, pixels: float) -> float:
        """ Converteste pixelii de pe ecran in unitati reale bazate pe scara curenta. """
        return (pixels / self.grid_size) * self.scale

    def real_units_to_pixels(self, units: float) -> float:
        """ Converteste unitatile reale inapoi in pixeli pentru randare. """
        return (units * self.grid_size) / self.scale

    def snap_to_grid(self, x: float, y: float) -> Tuple[float, float]:
        snapped_x = round(x / self.grid_size) * self.grid_size
        snapped_y = round(y / self.grid_size) * self.grid_size
        return snapped_x, snapped_y

    def snap_point_to_grid(self, point: Tuple[float, float]) -> Tuple[float, float]:
        return self.snap_to_grid(point[0], point[1])

    def distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """ Calculeaza distanta Euclidiana intre doua puncte (pixeli). """
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def distance_real(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """ Calculeaza distanta reala intre doua puncte de pe ecran. """
        pixel_distance = self.distance(x1, y1, x2, y2)
        return self.pixels_to_real_units(pixel_distance)

    def angle_between_points(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """ Calculeaza unghiul in grade dintre doua puncte. """
        dx = x2 - x1
        dy = y2 - y1
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        return angle_deg % 360

    def rotate_point(self, x: float, y: float, center_x: float, center_y: float,
                     angle_deg: float) -> Tuple[float, float]:
        """
                Roteste un punct (x, y) in jurul unui centru (center_x, center_y) cu un unghi dat.
                Foloseste matricea de rotatie 2D.
                """
        angle_rad = math.radians(angle_deg)
        translated_x = x - center_x
        translated_y = y - center_y
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        rotated_x = translated_x * cos_angle - translated_y * sin_angle
        rotated_y = translated_x * sin_angle + translated_y * cos_angle
        final_x = rotated_x + center_x
        final_y = rotated_y + center_y
        return final_x, final_y

    def scale_point(self, x: float, y: float, center_x: float, center_y: float,
                    scale_x: float, scale_y: float) -> Tuple[float, float]:
        translated_x = x - center_x
        translated_y = y - center_y
        scaled_x = translated_x * scale_x
        scaled_y = translated_y * scale_y
        final_x = scaled_x + center_x
        final_y = scaled_y + center_y
        return final_x, final_y

    def is_point_in_rect(self, px: float, py: float,
                         rect_x: float, rect_y: float,
                         rect_width: float, rect_height: float) -> bool:
        return (rect_x <= px <= rect_x + rect_width and
                rect_y <= py <= rect_y + rect_height)

    def get_grid_lines(self, width: int, height: int, offset_x: float = 0,
                       offset_y: float = 0) -> Tuple[List[float], List[float]]:
        vertical_lines = []
        horizontal_lines = []
        start_x = int(offset_x % self.grid_size)
        start_y = int(offset_y % self.grid_size)
        x = start_x
        while x < width:
            vertical_lines.append(x)
            x += self.grid_size
        y = start_y
        while y < height:
            horizontal_lines.append(y)
            y += self.grid_size
        return vertical_lines, horizontal_lines

    def format_distance(self, distance_cm: float) -> str:
        """ Formateaza o distanta pentru afisare (ex: '2.50 m' sau '80.0 cm'). """
        if distance_cm >= 100:
            meters = distance_cm / 100
            return f"{meters:.2f} m"
        else:
            return f"{distance_cm:.1f} cm"

    def format_length(self, pixels: float) -> str:
        """ Returneaza un string formatat cu unitatea curenta (ex: '2.50 m'). """
        val = self.pixels_to_current_unit(pixels)
        return f"{val:.2f} {self.display_unit}"

    def set_grid_size(self, size: int):
        if size <= 0:
            raise ValueError("Dimensiunea grilei trebuie să fie pozitiva")
        self.grid_size = size

    def set_scale(self, scale: float):
        if scale <= 0:
            raise ValueError("Scala trebuie să fie pozitiva")
        self.scale = scale

    def get_grid_spacing_cm(self) -> float:
        return self.pixels_to_real_units(self.grid_size)

    def meters_to_pixels(self, meters: float) -> float:
        cm = meters * 100
        return self.real_units_to_pixels(cm)

    def pixels_to_meters(self, pixels: float) -> float:
        cm = self.pixels_to_real_units(pixels)
        return cm / 100
