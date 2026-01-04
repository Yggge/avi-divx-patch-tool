import os
import sys
import shutil
import struct
from tkinter import Tk, Canvas, PhotoImage

# PyInstaller-safe path
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ======================
# Настройки патча
# ======================
PATCH_WIDTH = 384
FOURCC = b'divx'  # именно 'divx' в нижнем регистре
VIDEO_EXTENSIONS = {'.avi', '.AVI'}

# ======================
# Склонение
# ======================
def plural_files(n):
    if n % 10 == 1 and n % 100 != 11:
        return "файл"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return "файла"
    else:
        return "файлов"

# ======================
# Проверка и патч одного файла
# ======================
def patch_avi(file_path):
    """
    Возвращает:
      (True, "already_patched")  — если файл уже соответствует нужным параметрам
      (True, None)               — если патч успешно применён
      (False, error_message)     — если ошибка
    """
    try:
        with open(file_path, "rb") as f:
            # Читаем текущие значения
            f.seek(0xB1)
            planes = struct.unpack('<H', f.read(2))[0]
            
            f.seek(0xB4)
            width = struct.unpack('<H', f.read(2))[0]
            
            f.seek(0xBC)
            fourcc = f.read(4)

        # Уже пропатчен? (planes = 1 или 2 + ширина + fourcc)
        if (planes in (1, 2) and 
            width == PATCH_WIDTH and 
            fourcc == FOURCC):
            return True, "already_patched"

        # Патчим (всегда ставим planes = 1)
        bak_path = file_path + ".bak"
        if not os.path.exists(bak_path):
            shutil.copy2(file_path, bak_path)

        with open(file_path, "r+b") as f:
            f.seek(0xB1)
            f.write(struct.pack('<H', 1))          # фиксируем на 1
            
            f.seek(0xB4)
            f.write(struct.pack('<H', PATCH_WIDTH))
            
            f.seek(0xBC)
            f.write(FOURCC)

        return True, None

    except Exception as e:
        return False, str(e)

# ======================
# GUI
# ======================
WIDTH, HEIGHT = 900, 600
root = Tk()
root.title("AVI DivX Patch Tool v1.0 by Yggge")
root.geometry(f"{WIDTH}x{HEIGHT}")
root.resizable(False, False)

canvas = Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0)
canvas.pack()

# Константы размещения
INFO_X, INFO_Y = 530, 170
INFO_W = 235

# Фон и кнопки
logo_img = PhotoImage(file=resource_path("logo.png"))
canvas.create_image(0, 0, anchor="nw", image=logo_img)

patch_default   = PhotoImage(file=resource_path("patch_button_default.png"))
patch_pressed   = PhotoImage(file=resource_path("patch_button_pressed.png"))
exit_default    = PhotoImage(file=resource_path("exit_button_default.png"))
exit_pressed    = PhotoImage(file=resource_path("exit_button_pressed.png"))

# Текстовая область с КОПИРАЙТОМ YGGGE 🔥
START_TEXT = (
    "AVI DivX Patch Tool v1.0\n\n"
    "Игры:\n"
    " • За стеной\n"
    " • За стеной 2\n\n"
    "Назначение:\n"
    " Исправление AVI-видео\n"
    " для корректного запуска.\n\n"
    "Готов к работе.\n"
    "Нажмите PATCH.\n\n"
    "© 2026 Yggge"
)

info_text = canvas.create_text(
    INFO_X + 5, INFO_Y + 5,
    anchor="nw",
    width=INFO_W - 10,
    fill="#E0E0E0",
    font=("Segoe UI", 12, "bold"),  # ← ИСПРАВЛЕННЫЙ ШРИФТ (кортеж)
    text=START_TEXT
)

def log(message):
    canvas.itemconfig(info_text, text=message)
    root.update_idletasks()

# Кнопки
patch_btn = canvas.create_image(63, 395, anchor="nw", image=patch_default)
exit_btn  = canvas.create_image(63, 485, anchor="nw", image=exit_default)

patch_enabled = True

# ======================
# Логика патча (ИСПРАВЛЕНО ДЛЯ .EXE)
# ======================
def patch_action():
    global patch_enabled
    if not patch_enabled:
        return

    patch_enabled = False
    canvas.itemconfig(patch_btn, image=patch_pressed)

    # 🔥 ИСПРАВЛЕНИЕ ДЛЯ PyInstaller .exe 🔥
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        game_root = os.path.dirname(sys.executable)  # папка .exe
    else:
        game_root = os.path.dirname(os.path.abspath(__file__))  # папка .py

    log(f"Поиск AVI файлов в:\n{game_root}")

    avi_files = []
    for root_dir, _, files in os.walk(game_root):
        for file in files:
            if os.path.splitext(file)[1].lower() in VIDEO_EXTENSIONS:
                avi_files.append(os.path.join(root_dir, file))

    total = len(avi_files)
    if total == 0:
        log(
            "AVI файлы не найдены.\n\n"
            "Поместите AVIDXpatchtool в папку с игрой\n"
            "и запустите его повторно."
        )
        reset_button()
        return

    preview = "\n".join(
        f"• {os.path.relpath(p, game_root)}"
        for p in avi_files[:4]
    )
    if total > 4:
        preview += f"\n... и ещё {total-4} {plural_files(total-4)}"

    log(
    f"Найдено {total} {plural_files(total)}\n\n"
    f"Примеры:\n{preview}\n\n"
    "Применение патча...\n"
    "Пожалуйста, подождите."
    )

    success = 0      # реально изменённые
    skipped = 0      # уже были в нужном состоянии
    errors_cnt = 0

    for i, path in enumerate(avi_files, 1):
        rel = os.path.relpath(path, game_root)
        ok, msg = patch_avi(path)

        if ok:
            if msg == "already_patched":
                skipped += 1
            else:
                success += 1
        else:
            errors_cnt += 1

        if i % 30 == 0 or i == total:
            log(
               f"Прогресс: {i}/{total}\n"
               f"Успешно: {success}\n"
               f"Пропущено: {skipped}\n\n"
               f"Текущий файл:\n{rel}"
               )

        msg = "Патч завершён.\n\n"
        msg += f"Успешно пропатчено: {success} {plural_files(success)}\n"
        msg += f"Уже были готовы:    {skipped} {plural_files(skipped)}\n"
        msg += f"Всего файлов:       {total} {plural_files(total)}\n"
        if errors_cnt:
            msg += f"Ошибок:             {errors_cnt}"
        msg += "\n\n© 2026 Yggge"

    log(msg)
    reset_button()

def reset_button():
    global patch_enabled
    canvas.itemconfig(patch_btn, image=patch_default)
    patch_enabled = True

# ======================
# События кнопок (НАДЁЖНЫЕ)
# ======================
def exit_press(e):
    canvas.itemconfig(exit_btn, image=exit_pressed)

def exit_release(e):
    canvas.itemconfig(exit_btn, image=exit_default)
    root.destroy()

canvas.tag_bind(patch_btn, "<Button-1>", lambda e: patch_action())
canvas.tag_bind(exit_btn, "<ButtonPress-1>", exit_press)
canvas.tag_bind(exit_btn, "<ButtonRelease-1>", exit_release)
canvas.tag_bind(exit_btn, "<Button-1>", lambda e: root.destroy())

root.bind("<Escape>", lambda e: root.destroy())
root.protocol("WM_DELETE_WINDOW", root.destroy)

root.mainloop()
