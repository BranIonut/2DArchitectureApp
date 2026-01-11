# 2D Architecture App

O aplicație desktop scrisă în Python pentru proiectarea rapidă a planurilor arhitecturale 2D. Proiectul a fost dezvoltat pentru a oferi o alternativă simplă și intuitivă la programele CAD complexe, fiind accesibilă oricui vrea să schițeze rapid o compartimentare.

🔗 **GitHub Repository:** [Link aici](https://github.com/BranIonut/2DArchitectureApp/tree/main)

## Despre Proiect

Aplicația oferă un canvas pe care poți desena pereți și camere, plasa uși, ferestre și mobilier prin drag-and-drop. Include funcții de "snapping" magnetic pentru aliniere ușoară și calculează automat suprafețele utile.

Totul este construit modular, separând logica de business de interfață, iar datele proiectului sunt salvate în format JSON.

## Funcționalități Principale

* **Sistem de desenare:** Plasare pereți și camere direct pe grid.
* **Bibliotecă de obiecte:** Mobilier, uși și ferestre predefinite (SVG-uri scalabile).
* **Smart Snap & Coliziuni:** Obiectele se "lipesc" magnetic de aliniamentele din jur și nu se pot suprapune accidental.
* **Editare:** Resize (mânere în colțuri), rotire (scroll mouse) și mutare.
* **Măsurători:** Riglă virtuală și calcul automat al ariei camerelor.
* **Export:** Salvare proiect local sau export ca imagine (PNG/JPG).

## Tech Stack

Proiectul rulează pe Python 3.x și folosește următoarele librării:

* **PyQt5** - Pentru GUI și randare grafică (QPainter).
* **Pillow** - Manipulare imagini și texturi.
* **svgwrite** - Gestionare grafică vectorială.
* **reportlab** - Generare rapoarte PDF.

## Instalare și Rulare

Ai nevoie de Python 3.9+ instalat.

1.  Clonează repo-ul:
    ```bash
    git clone [https://github.com/BranIonut/2DArchitectureApp.git](https://github.com/BranIonut/2DArchitectureApp.git)
    cd 2DArchitectureApp
    ```

2.  Instalează dependențele din `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

3.  Pornește aplicația:
    ```bash
    python main.py
    ```

> **Notă:** Structura folderelor (`/Business`, `/Presentation`, `/resources`) trebuie păstrată intactă pentru ca aplicația să-și găsească resursele.

## Utilizare

Interfața e împărțită simplu: Unelte (stânga), Canvas (centru), Proprietăți (dreapta).

* **Pentru a desena un perete:** Selectează "Perete" din stânga, click pe canvas pentru start și click pentru final.
* **Adăugare cameră:** Selectează "Zonă", click și trage (drag) pe diagonală.
* **Mobilă:** Selectezi obiectul din listă și dai click unde vrei să-l pui.
* **Navigare:** Zoom cu `Ctrl + Scroll`, Pan cu `Click rotiță` apăsat.
* **Comenzi rapide:**
    * `Delete` - Șterge obiectul selectat.
    * `Shift + Scroll` - Rotire fină a obiectelor.

## Screenshots

*(Aici pui capturile de ecran din folderul resources)*

* **Dashboard:** `./resources/screenshots/dashboard.png`
* **Exemplu Plan:** `./resources/screenshots/plan_example.png`

## Contributori

* **Alupului Diana** - Export foto, logica de desenare pereți, detecție coliziuni, UI.
* **Bran Ionuț-Alexandru** - Arhitectură (UML), sistem grid & zoom, snapping, resize & rotire.
* **Găină Alexandru** - Gestionare SVG, unități de măsură, documentație, modul Help.
* **Petrea Paul-Alberto** - Undo/Redo, implementare rotire, coliziuni, documentație.
