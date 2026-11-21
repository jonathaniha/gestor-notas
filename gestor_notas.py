from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QListWidget, QLineEdit, QTextEdit, QInputDialog,
    QHBoxLayout, QVBoxLayout, QMessageBox
)
import sys
import os

# ── Persistencia ────────────────────────────────────────────────────────────

NOTES_DIR = "notes_data"
os.makedirs(NOTES_DIR, exist_ok=True)


def note_path(index):
    return os.path.join(NOTES_DIR, f"{index}.txt")


def load_notes():
    """Carga todas las notas guardadas en disco."""
    notes = []
    index = 0
    while True:
        path = note_path(index)
        if not os.path.exists(path):
            break
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        name = lines[0] if len(lines) > 0 else ""
        body = lines[1] if len(lines) > 1 else ""
        raw_tags = lines[2] if len(lines) > 2 else ""
        # Filtra strings vacíos que quedaban con el split anterior
        tags = [t for t in raw_tags.split(" ") if t.strip()]
        notes.append([name, body, tags])
        index += 1
    return notes


def save_note_to_disk(index, note):
    """Guarda una nota individual en su archivo."""
    with open(note_path(index), "w", encoding="utf-8") as f:
        f.write(note[0] + "\n")
        f.write(note[1] + "\n")
        f.write(" ".join(note[2]) + "\n")


def rebuild_files(notes):
    """Re-escribe todos los archivos cuando se elimina una nota (re-indexa)."""
    # Borra archivos existentes
    index = 0
    while os.path.exists(note_path(index)):
        os.remove(note_path(index))
        index += 1
    # Vuelve a escribir con índices consecutivos
    for i, note in enumerate(notes):
        save_note_to_disk(i, note)


# ── Interfaz ─────────────────────────────────────────────────────────────────

app = QApplication(sys.argv)

# Cargamos notas ANTES de construir la UI para evitar problemas con el event loop
notes = load_notes()

notes_win = QWidget()
notes_win.setWindowTitle("Notas inteligentes")
notes_win.resize(900, 600)

# Widgets
list_notes      = QListWidget()
list_notes_label = QLabel("Lista de notas")

button_note_create = QPushButton("Crear nota")
button_note_del    = QPushButton("Eliminar nota")
button_note_save   = QPushButton("Guardar nota")

field_text = QTextEdit()

field_tag       = QLineEdit()
field_tag.setPlaceholderText("Ingresar etiqueta...")
button_tag_add    = QPushButton("Añadir etiqueta")
button_tag_del    = QPushButton("Remover etiqueta")
button_tag_search = QPushButton("Buscar notas por etiqueta")
list_tags       = QListWidget()
list_tags_label  = QLabel("Etiquetas de la nota")

# Layout
layout_notes = QHBoxLayout()

col_1 = QVBoxLayout()
col_1.addWidget(field_text)

col_2 = QVBoxLayout()
col_2.addWidget(list_notes_label)
col_2.addWidget(list_notes)

row_1 = QHBoxLayout()
row_1.addWidget(button_note_create)
row_1.addWidget(button_note_del)
col_2.addLayout(row_1)

row_2 = QHBoxLayout()
row_2.addWidget(button_note_save)
col_2.addLayout(row_2)

col_2.addWidget(list_tags_label)
col_2.addWidget(list_tags)
col_2.addWidget(field_tag)

row_3 = QHBoxLayout()
row_3.addWidget(button_tag_add)
row_3.addWidget(button_tag_del)
col_2.addLayout(row_3)

row_4 = QHBoxLayout()
row_4.addWidget(button_tag_search)
col_2.addLayout(row_4)

layout_notes.addLayout(col_1, stretch=2)
layout_notes.addLayout(col_2, stretch=1)
notes_win.setLayout(layout_notes)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_selected_index():
    """Devuelve el índice de la nota seleccionada, o None si no hay ninguna."""
    items = list_notes.selectedItems()
    if not items:
        return None
    return list_notes.row(items[0])


def refresh_tags(index):
    """Actualiza la lista de etiquetas con la nota indicada."""
    list_tags.clear()
    if index is not None:
        list_tags.addItems(notes[index][2])


# ── Funcionalidad ─────────────────────────────────────────────────────────────

def show_note():
    index = get_selected_index()
    if index is None:
        return
    field_text.setText(notes[index][1])
    refresh_tags(index)


def add_note():
    note_name, ok = QInputDialog.getText(notes_win, "Añadir nota", "Nombre de nota:")
    if ok and note_name.strip():
        note = [note_name.strip(), "", []]
        notes.append(note)
        save_note_to_disk(len(notes) - 1, note)
        list_notes.addItem(note[0])
        # Selecciona la nota recién creada
        list_notes.setCurrentRow(len(notes) - 1)
        field_text.clear()
        refresh_tags(len(notes) - 1)


def delete_note():
    index = get_selected_index()
    if index is None:
        QMessageBox.warning(notes_win, "Aviso", "Selecciona una nota para eliminar.")
        return
    confirm = QMessageBox.question(
        notes_win, "Confirmar",
        f"¿Eliminar la nota «{notes[index][0]}»?",
        QMessageBox.Yes | QMessageBox.No
    )
    if confirm == QMessageBox.Yes:
        notes.pop(index)
        rebuild_files(notes)
        list_notes.takeItem(index)
        field_text.clear()
        list_tags.clear()


def save_note():
    index = get_selected_index()
    if index is None:
        QMessageBox.warning(notes_win, "Aviso", "Selecciona una nota para guardar.")
        return
    notes[index][1] = field_text.toPlainText()
    save_note_to_disk(index, notes[index])


def add_tag():
    index = get_selected_index()
    if index is None:
        QMessageBox.warning(notes_win, "Aviso", "Selecciona una nota primero.")
        return
    tag = field_tag.text().strip()
    if not tag:
        return
    if tag in notes[index][2]:
        QMessageBox.information(notes_win, "Info", "Esa etiqueta ya existe en la nota.")
        return
    notes[index][2].append(tag)
    save_note_to_disk(index, notes[index])
    refresh_tags(index)
    field_tag.clear()


def remove_tag():
    index = get_selected_index()
    if index is None:
        QMessageBox.warning(notes_win, "Aviso", "Selecciona una nota primero.")
        return
    selected_tags = list_tags.selectedItems()
    if not selected_tags:
        QMessageBox.warning(notes_win, "Aviso", "Selecciona una etiqueta para remover.")
        return
    tag = selected_tags[0].text()
    notes[index][2].remove(tag)
    save_note_to_disk(index, notes[index])
    refresh_tags(index)


def search_by_tag():
    tag, ok = QInputDialog.getText(notes_win, "Buscar por etiqueta", "Etiqueta:")
    if not ok or not tag.strip():
        return
    tag = tag.strip()
    results = [note[0] for note in notes if tag in note[2]]
    if results:
        QMessageBox.information(
            notes_win, "Resultados",
            f"Notas con la etiqueta «{tag}»:\n\n" + "\n".join(f"• {r}" for r in results)
        )
    else:
        QMessageBox.information(notes_win, "Resultados", f"No hay notas con la etiqueta «{tag}».")


# ── Eventos ───────────────────────────────────────────────────────────────────

list_notes.itemClicked.connect(show_note)
button_note_create.clicked.connect(add_note)
button_note_del.clicked.connect(delete_note)
button_note_save.clicked.connect(save_note)
button_tag_add.clicked.connect(add_tag)
button_tag_del.clicked.connect(remove_tag)
button_tag_search.clicked.connect(search_by_tag)


# ── Inicio ────────────────────────────────────────────────────────────────────

# Poblar la lista con las notas cargadas desde disco
for note in notes:
    list_notes.addItem(note[0])

notes_win.show()
sys.exit(app.exec_())