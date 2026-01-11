import math
import os
import sys

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
    QMessageBox, QFileDialog, QSpinBox, QCheckBox, QShortcut, QToolBox,
    QListWidget, QListWidgetItem, QAbstractItemView, QComboBox
)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QKeySequence, QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QSize, QRectF, QMarginsF, QLineF

from .TutorialDialog import TutorialDialog

# Importuri Business Logic
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from .Page import Page

try:
    from Business.ProjectManager import ProjectManager
    from Business.ArchitecturalObjects import SvgFurnitureObject, Wall, Window, RoomFloor
    from Business.CollisionDetector import CollisionDetector
except ImportError:
    from ProjectManager import ProjectManager
    from ArchitecturalObjects import SvgFurnitureObject, Wall, Window

    try:
        from ArchitecturalObjects import RoomFloor
    except Exception:
        RoomFloor = None
    from CollisionDetector import CollisionDetector

from .SimpleCanvas import SimpleCanvas

class WorkPage(Page):
    """
        Pagina principala de lucru a aplicatiei.

        Rol: Actioneaza ca un Controller care integreaza:
        - Canvas-ul de desenare (SimpleCanvas).
        - Bara de instrumente din stanga (Toolbox).
        - Panoul de proprietati din dreapta.
        - Bara de meniu superioara.
        """
    def init_ui(self):
        """
                Configureaza layout-ul principal si initializeaza componentele UI.
                Seteaza conexiunile semnal-slot dintre componente.
                """
        self.pm = ProjectManager()
        if not self.pm.current_project:
            self.pm.create_new_project("Proiect Hibrid")

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # 1. Header
        main.addWidget(self.create_header())

        content = QHBoxLayout()
        content.setSpacing(0)

        self.canvas = SimpleCanvas(self)

        content.addWidget(self.create_left_panel())

        canvas_container = QWidget()
        cl = QVBoxLayout(canvas_container)
        cl.setContentsMargins(5, 5, 5, 5)
        cl.addWidget(self.canvas)
        content.addWidget(canvas_container, 1)

        content.addWidget(self.create_right_panel())
        main.addLayout(content, 1)

        # 3. Footer
        main.addWidget(self.create_footer())

        # Conectare Semnale Canvas -> UI
        self.canvas.status_message_signal.connect(self.lbl_status.setText)
        self.canvas.project_changed_signal.connect(self.refresh_stats)
        self.canvas.object_selected_signal.connect(self.update_properties)
        self.canvas.mouse_moved_signal.connect(lambda x, y: None)

        # Scurtaturi tastatura
        QShortcut(QKeySequence("Delete"), self).activated.connect(self.canvas.delete_selection)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.action_cancel)

        # Scurtaturi Undo / Redo
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self.canvas.trigger_undo)

        # Pentru Redo, standardul este Ctrl+Y sau Ctrl+Shift+Z
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        redo_shortcut.activated.connect(self.canvas.trigger_redo)

        redo_shortcut_alt = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        redo_shortcut_alt.activated.connect(self.canvas.trigger_redo)

        self.refresh_stats()

    def create_header(self):
        """ Creeaza bara superioara cu butoane de actiune globala. """
        w = QWidget()
        w.setStyleSheet("background-color: #03254C; color: white; padding: 5px;")
        h = QHBoxLayout(w)
        h.addWidget(QLabel("<b>Architect App</b>"))
        h.addStretch()

        btn_help = QPushButton("? Ajutor")
        btn_help.setStyleSheet(
            "border:none; background:#E67E22; padding:5px 10px; border-radius:3px; font-weight:bold;")
        btn_help.clicked.connect(self.show_tutorial)
        h.addWidget(btn_help)

        btn_export = QPushButton("🖼️ Export Foto")
        btn_export.setStyleSheet(
            "border:none; background:#27AE60; padding:5px 10px; border-radius:3px; font-weight:bold;")
        btn_export.clicked.connect(self.export_as_image)
        h.addWidget(btn_export)

        btn_save = QPushButton("💾 Salvează")
        btn_save.setStyleSheet("border:none; background:#185E8A; padding:5px; border-radius:3px;")
        btn_save.clicked.connect(self.save_project)
        h.addWidget(btn_save)

        btn_load = QPushButton("📂 Deschide")
        btn_load.setStyleSheet("border:none; background:#185E8A; padding:5px; border-radius:3px;")
        btn_load.clicked.connect(self.load_project)
        h.addWidget(btn_load)

        btn_back = QPushButton("🏠 Meniu")
        btn_back.setStyleSheet("border:none; background:#185E8A; padding:5px; border-radius:3px;")
        btn_back.clicked.connect(lambda: self.dashboard.update_page("main"))
        h.addWidget(btn_back)

        return w

    def create_left_panel(self):
        """ Creeaza panoul din stanga continand sabloane, unelte si biblioteca de obiecte. """
        w = QWidget()
        w.setFixedWidth(250)
        w.setStyleSheet("background-color: #F7F3E8;")
        v = QVBoxLayout(w)
        v.setContentsMargins(5, 10, 5, 5)

        gb_view = QGroupBox("Vizualizare")
        v_view = QVBoxLayout(gb_view)

        self.chk_grid = QCheckBox("Arată Grila")
        self.chk_grid.setChecked(True)
        self.chk_grid.toggled.connect(lambda val: setattr(self.canvas, 'grid_visible', val) or self.canvas.update())
        v_view.addWidget(self.chk_grid)

        self.chk_snap = QCheckBox("Snap to Grid")
        self.chk_snap.setChecked(True)
        self.chk_snap.toggled.connect(lambda val: setattr(self.canvas, 'snap_to_grid', val))
        v_view.addWidget(self.chk_snap)

        # Selector Unitati
        v_view.addWidget(QLabel("Unitati:"))
        self.combo_units = QComboBox()
        self.combo_units.addItems(["Metri (m)", "Centimetri (cm)", "Milimetri (mm)"])
        self.combo_units.currentIndexChanged.connect(self.on_unit_changed)
        v_view.addWidget(self.combo_units)

        v.addWidget(gb_view)

        self.toolbox = QToolBox()
        self.toolbox.setStyleSheet("""
            QToolBox::tab { background: #E0D8C0; border: 1px solid #aaa; border-radius: 2px; color: black; font-weight: bold; }
            QListWidget { border: none; background: #F7F3E8; }
        """)

        # Sectiune Structura
        list_struct = QListWidget()
        list_struct.setIconSize(QSize(32, 32))

        item_ruler = QListWidgetItem("Rigla (Masurare)")
        item_ruler.setData(Qt.UserRole, "CMD_RULER")
        list_struct.addItem(item_ruler)

        # Sectiune Sabloane
        list_templates = QListWidget()
        list_templates.itemClicked.connect(self.on_template_clicked)

        item_studio = QListWidgetItem("🏠 Garsonieră (Studio)")
        item_studio.setData(Qt.UserRole, "APARTAMENT_STUDIO")
        list_templates.addItem(item_studio)

        item_2cam = QListWidgetItem("🏢 Apartament 2 Camere")
        item_2cam.setData(Qt.UserRole, "APARTAMENT_2_CAMERE")
        list_templates.addItem(item_2cam)

        self.toolbox.addItem(list_templates, "Șabloane Apartament")

        item_wall = QListWidgetItem("Perete (Linie)")
        item_wall.setData(Qt.UserRole, "CMD_WALL")
        list_struct.addItem(item_wall)

        item_win = QListWidgetItem("Fereastră (Albastru)")
        item_win.setData(Qt.UserRole, "CMD_WINDOW")
        list_struct.addItem(item_win)

        item_floor = QListWidgetItem("Zonă / Cameră (m²)")
        item_floor.setData(Qt.UserRole, "CMD_FLOOR")
        list_struct.addItem(item_floor)

        list_struct.itemClicked.connect(self.on_menu_item_clicked)
        self.toolbox.addItem(list_struct, "Structură")

        # Incarcare dinamica a resurselor SVG
        self.load_assets_structured()

        v.addWidget(self.toolbox)

        btn_clear = QPushButton("Sterge Tot")
        btn_clear.setStyleSheet("background: #E74C3C; color: white; padding: 5px;")
        btn_clear.clicked.connect(self.ask_clear_scene)
        v.addWidget(btn_clear)

        return w

    def on_unit_changed(self, index):
        """ Schimba unitatea de masura in sistemul de coordonate al canvas-ului. """
        unit_map = {0: 'm', 1: 'cm', 2: 'mm'}
        selected_unit = unit_map.get(index, 'm')

        self.canvas.coords.set_display_unit(selected_unit)

        self.canvas.update()

        self.canvas.status_message_signal.emit(f"Unitate schimbata in: {selected_unit}")

    def load_assets_structured(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        possible_paths = [
            os.path.join(root_dir, "resources", "assets"),
            os.path.join(current_dir, "resources", "assets")
        ]
        assets_dir = None
        for p in possible_paths:
            if os.path.exists(p):
                assets_dir = p
                break

        if not assets_dir:
            return

        doors_path = os.path.join(assets_dir, "doors")
        if os.path.exists(doors_path):
            self.add_grid_category("Uși", doors_path)

        furn_path = os.path.join(assets_dir, "furniture")
        if os.path.exists(furn_path):
            subfolders = sorted([d for d in os.listdir(furn_path) if os.path.isdir(os.path.join(furn_path, d))])
            for folder_name in subfolders:
                full_path = os.path.join(furn_path, folder_name)
                self.add_grid_category(folder_name.capitalize(), full_path)

    def add_grid_category(self, title, path):
        """ Adauga o noua categorie in Toolbox cu iconite pentru fisierele din path. """
        list_w = QListWidget()
        list_w.setViewMode(QListWidget.IconMode)
        list_w.setResizeMode(QListWidget.Adjust)
        list_w.setIconSize(QSize(65, 65))
        list_w.setSpacing(10)
        list_w.setMovement(QListWidget.Static)
        list_w.setWordWrap(True)
        list_w.itemClicked.connect(self.on_menu_item_clicked)

        try:
            files = sorted([f for f in os.listdir(path) if f.lower().endswith(('.svg', '.png'))])
            for f in files:
                clean_name = os.path.splitext(f)[0].replace('AdobeStock_', '').replace('_', ' ').title()
                if len(clean_name) > 15:
                    clean_name = clean_name[:12] + "..."
                item = QListWidgetItem(clean_name)
                full_path = os.path.join(path, f)
                item.setData(Qt.UserRole, full_path)
                item.setToolTip(os.path.splitext(f)[0].replace('_', ' ').title())
                pix = QPixmap(full_path)
                if not pix.isNull():
                    item.setIcon(QIcon(pix))
                list_w.addItem(item)
            if list_w.count() > 0:
                self.toolbox.addItem(list_w, title)
        except Exception as e:
            print(f"Error loading category {title}: {e}")

    def on_menu_item_clicked(self, item):
        """ Gestioneaza selectia unei unelte sau a unui obiect din Toolbox. """
        data = item.data(Qt.UserRole)
        if data == "CMD_WALL":
            self.canvas.set_tool_wall()
        elif data == "CMD_WINDOW":
            self.canvas.set_tool_window()
        elif data == "CMD_FLOOR":
            self.canvas.set_tool_floor()
        elif data == "CMD_RULER":
            self.canvas.set_tool_ruler()
        elif data:
            self.canvas.set_tool_svg(data)

    def create_right_panel(self):
        """ Creeaza panoul din dreapta pentru unelte rapide si proprietati obiect. """
        w = QWidget()
        w.setFixedWidth(240)
        w.setStyleSheet("background-color: #FEFCF3; border-left: 1px solid #ccc;")
        v = QVBoxLayout(w)

        gb_tools = QGroupBox("Unelte Rapide")
        v_tools = QVBoxLayout(gb_tools)

        btn_add_floor = QPushButton("➕ Adauga Zona (m²)")
        btn_add_floor.setMinimumHeight(40)
        btn_add_floor.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #45a049; }
        """)
        btn_add_floor.clicked.connect(self.canvas.set_tool_floor)
        v_tools.addWidget(btn_add_floor)
        v.addWidget(gb_tools)

        gb_stats = QGroupBox("Statistici Proiect")
        v_stats = QVBoxLayout(gb_stats)
        self.lbl_total_area = QLabel("Total Arie: 0.00 m²")
        self.lbl_total_area.setStyleSheet("font-weight: bold; font-size: 14px; color: #2E7D32;")
        v_stats.addWidget(self.lbl_total_area)
        v.addWidget(gb_stats)

        self.gb_props = QGroupBox("Proprietăți")
        vp = QVBoxLayout(self.gb_props)

        self.lbl_name = QLabel("Nume: -")
        vp.addWidget(self.lbl_name)

        vp.addWidget(QLabel("Rotatie (°):"))
        self.spin_rot = QSpinBox()
        self.spin_rot.setRange(0, 360)
        self.spin_rot.setSingleStep(45)
        self.spin_rot.valueChanged.connect(self.on_rotation_changed)
        vp.addWidget(self.spin_rot)

        vp.addWidget(QLabel("Lățime (cm/px):"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(10, 2000)
        self.spin_width.setSingleStep(10)
        self.spin_width.valueChanged.connect(self.on_width_changed)
        vp.addWidget(self.spin_width)

        vp.addWidget(QLabel("Înălțime/Grosime (cm/px):"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(5, 2000)
        self.spin_height.setSingleStep(5)
        self.spin_height.valueChanged.connect(self.on_height_changed)
        vp.addWidget(self.spin_height)

        vp.addSpacing(10)
        self.btn_delete_obj = QPushButton("🗑️ Sterge Element")
        self.btn_delete_obj.setMinimumHeight(35)
        self.btn_delete_obj.setStyleSheet("""
            QPushButton { background-color: #ff4444; color: white; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #cc0000; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        self.btn_delete_obj.clicked.connect(self.canvas.delete_selection)
        self.btn_delete_obj.setEnabled(False)
        vp.addWidget(self.btn_delete_obj)

        self.gb_props.setEnabled(False)
        v.addWidget(self.gb_props)

        v.addStretch()
        return w

    def on_rotation_changed(self, val):
        """ Slot apelat la modificarea spinbox-ului de rotatie. """
        obj = self.canvas.selected_object
        if obj and not isinstance(obj, Wall):
            obj.rotation = val
            self.canvas.check_collisions()
            self.canvas.update()

    def on_width_changed(self, val):
        """ Slot apelat la modificarea spinbox-ului de latime. """
        obj = self.canvas.selected_object
        if obj:
            if isinstance(obj, Wall):
                pass
            else:
                obj.width = val
                self.canvas.check_collisions()
                self.canvas.update()
                self.refresh_stats()

    def on_height_changed(self, val):
        """ Slot apelat la modificarea spinbox-ului de inaltime. """
        obj = self.canvas.selected_object
        if obj:
            if isinstance(obj, Wall):
                obj.thickness = val
            else:
                obj.height = val
            self.canvas.check_collisions()
            self.canvas.update()
            self.refresh_stats()

    def create_footer(self):
        """ Creeaza bara de status din josul paginii. """
        w = QWidget()
        w.setStyleSheet("background:#185E8A; color:white;")
        h = QHBoxLayout(w)
        self.lbl_status = QLabel("Gata.")
        h.addWidget(self.lbl_status)
        return w

    def refresh_stats(self):
        """ Recalculeaza aria totala a camerelor din proiect. """
        total_m2 = 0.0
        if RoomFloor is not None:
            for obj in self.canvas.objects:
                if isinstance(obj, RoomFloor):
                    total_m2 += float(getattr(obj, "area_m2", 0.0))
        if hasattr(self, "lbl_total_area"):
            self.lbl_total_area.setText(f"Total Arie: {total_m2:.2f} m²")

    def update_properties(self, obj):
        """ Actualizeaza panoul de proprietati cand un obiect este selectat. """
        if obj:
            self.gb_props.setEnabled(True)
            if hasattr(self, "btn_delete_obj"):
                self.btn_delete_obj.setEnabled(True)

            self.spin_rot.blockSignals(True)
            self.spin_width.blockSignals(True)
            self.spin_height.blockSignals(True)

            if isinstance(obj, Wall):
                self.lbl_name.setText("Perete")
                self.spin_rot.setEnabled(False)
                self.spin_rot.setValue(0)

                self.spin_width.setEnabled(False)
                self.spin_width.setValue(0)

                self.spin_height.setEnabled(True)
                self.spin_height.setValue(int(obj.thickness))

            elif RoomFloor is not None and isinstance(obj, RoomFloor):
                self.lbl_name.setText(f"Camera ({getattr(obj, 'area_m2', 0)} m²)")
                self.spin_rot.setEnabled(False)
                self.spin_rot.setValue(0)

                self.spin_width.setEnabled(True)
                self.spin_width.setValue(int(getattr(obj, "width", 0)))

                self.spin_height.setEnabled(True)
                self.spin_height.setValue(int(getattr(obj, "height", 0)))

            elif isinstance(obj, Window):
                self.lbl_name.setText("Fereastră")
                self.spin_rot.setEnabled(True)
                self.spin_rot.setValue(int(obj.rotation))

                self.spin_width.setEnabled(True)
                self.spin_width.setValue(int(obj.width))

                self.spin_height.setEnabled(True)
                self.spin_height.setValue(int(obj.height))

            else:
                self.lbl_name.setText(getattr(obj, 'name', 'Obiect'))
                self.spin_rot.setEnabled(True)
                self.spin_rot.setValue(int(obj.rotation))

                self.spin_width.setEnabled(True)
                self.spin_width.setValue(int(obj.width))

                self.spin_height.setEnabled(True)
                self.spin_height.setValue(int(obj.height))

            self.spin_rot.blockSignals(False)
            self.spin_width.blockSignals(False)
            self.spin_height.blockSignals(False)
        else:
            self.gb_props.setEnabled(False)
            self.lbl_name.setText("-")
            if hasattr(self, "btn_delete_obj"):
                self.btn_delete_obj.setEnabled(False)

    def action_cancel(self):
        self.canvas.current_tool_mode = None
        self.canvas.is_drawing_wall = False
        self.canvas.is_drawing_floor = False
        self.canvas.wall_start_pt = None
        self.canvas.wall_temp_end = None
        self.canvas.floor_start_pt = None
        self.canvas.floor_temp_rect = None
        self.canvas.select_object(None)
        self.lbl_status.setText("Anulat.")
        self.canvas.setCursor(Qt.ArrowCursor)

    def ask_clear_scene(self):
        """ Afiseaza dialog de confirmare pentru stergerea intregului proiect. """
        reply = QMessageBox.question(
            self,
            "Confirmare Stergere",
            "Esti sigur ca vrei sa stergi TOT proiectul? Actiunea nu poate fi anulata.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.canvas.clear_scene()

    def save_project(self):
        """ Salveaza starea curenta in format JSON. """
        fname, _ = QFileDialog.getSaveFileName(self, "Salveaza", "", "JSON (*.json)")
        if fname:
            if self.pm.save_project(fname, self.canvas.objects):
                QMessageBox.information(self, "Succes", "Salvat cu succes!")
            else:
                QMessageBox.warning(self, "Eroare", "Nu s-a putut salva.")

    def load_project(self):
        """ Incarca un proiect dintr-un fisier JSON. """
        fname, _ = QFileDialog.getOpenFileName(self, "Deschide", "", "JSON (*.json)")
        if fname:
            objs = self.pm.load_project(fname)
            if objs is not None:
                self.canvas.objects = objs
                self.canvas.check_collisions()
                self.canvas.update()
                self.refresh_stats()
                QMessageBox.information(self, "Succes", "Incarcat cu succes!")
            else:
                QMessageBox.warning(self, "Eroare", "Fisier invalid sau nu s-a putut incarca.")

    def export_as_image(self):
        """ Exporta scena curenta ca imagine (PNG/JPG). """
        fname, filter_selected = QFileDialog.getSaveFileName(
            self, "Exportă Schița", "proiect_casa", "PNG Image (*.png);;JPEG Image (*.jpg)"
        )

        if not fname:
            return

        if not fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            if "png" in filter_selected.lower():
                fname += ".png"
            elif "jpg" in filter_selected.lower():
                fname += ".jpg"

        success = self.canvas.save_to_image(fname)

        if success:
            QMessageBox.information(self, "Export Reușit", f"Imaginea a fost salvată în:\n{fname}")
        else:
            QMessageBox.warning(self, "Eroare", "Nu s-a putut salva imaginea. Verifică permisiunile sau calea aleasă.")

    def on_template_clicked(self, item):
        """ Incarca un sablon cand este selectat din lista. """
        template_id = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, 'Atenție!',
            "Încărcarea unui șablon va șterge tot ce ai desenat până acum. Continui?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.canvas.load_layout_template(template_id)

    def show_tutorial(self):
        """ Deschide fereastra de ajutor (TutorialDialog). """
        dlg = TutorialDialog(self)
        dlg.exec_()
