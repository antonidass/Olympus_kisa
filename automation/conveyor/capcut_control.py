"""
Управление приложением CapCut для автоматического конвейера.

Международный CapCut — это QML-приложение, которое НЕ отдаёт дерево
контролов через UI Automation (видно только само окно, но не кнопки/
плитки). Поэтому «изящно нажать кнопку назад в галерею» нельзя — клик
не по чему делать. Зато надёжно определяется СОСТОЯНИЕ окна по ClassName:
  • HomePage* → галерея проектов (файл драфта свободен — можно патчить)
  • MainWindow* → проект открыт в редакторе (CapCut держит файл, затрёт)

Стратегия авто-управления (ensure_writable):
  • галерея / закрыт → патчим сразу, перезапуск не нужен (быстрый путь).
  • редактор → шлём Ctrl+S (сохранить ручные правки), убиваем процесс,
    патчим файл, перезапускаем CapCut (откроется на галерее).

Открыть конкретный проект через дерево/CLI/URL нельзя (QML не отдаёт
дерево, deep-link только для ИИ-инструментов, путь-аргумент игнорируется).
Поэтому после перезапуска делаем системный двойной клик по координате
первой плитки галереи (наш проект свежайший → первый). Координата
относительная (% окна), откалибрована для состояния сразу после запуска.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Literal, Optional

State = Literal["home", "edit", "dialog", "closed"]

LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
CAPCUT_EXE = LOCALAPPDATA / "CapCut" / "Apps" / "CapCut.exe"
CAPCUT_LAUNCH_ARGS = ["--src3"]
CAPCUT_WINDOW_NAME = "CapCut"  # международная версия; китайская — "CapCut专业版"


def _find_window():
    """Возвращает (control, state) верхнего окна CapCut или (None, 'closed')."""
    try:
        import uiautomation as uia  # type: ignore
    except ImportError:
        return None, "closed"

    root = uia.GetRootControl()
    for w in root.GetChildren():
        try:
            name = w.Name
            cls = (w.ClassName or "").lower()
        except Exception:
            continue
        if name != CAPCUT_WINDOW_NAME and "capcut" not in name.lower():
            continue
        if "homepage" in cls:
            return w, "home"
        if "mainwindow" in cls:
            return w, "edit"
        # Диалог поверх (например «Требуется обновление») — отдельное окно.
        if "dialog" in cls or "lvinfo" in cls:
            return w, "dialog"
        # Окно CapCut есть, но класс неизвестен — считаем edit (осторожно).
        return w, "edit"
    return None, "closed"


def get_state() -> State:
    """Текущее состояние CapCut: home / edit / dialog / closed."""
    _, state = _find_window()
    return state  # type: ignore[return-value]


def is_running() -> bool:
    try:
        out = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
        text = out.decode("cp866", errors="ignore") + out.decode("utf-8", errors="ignore")
        return "CapCut.exe" in text
    except Exception:
        return False


def save_active_project(wait_s: float = 1.8) -> bool:
    """Шлёт Ctrl+S активному окну CapCut, чтобы сохранить ручные правки.

    Возвращает True если окно найдено и команда отправлена. Безопасно: если
    окна нет — ничего не делает.
    """
    win, state = _find_window()
    if win is None or state not in ("edit",):
        return False
    try:
        import uiautomation as uia  # type: ignore  # noqa: F401
        win.SetActive()
        time.sleep(0.3)
        # uiautomation: модификатор действует на символы в круглых скобках.
        win.SendKeys("{Ctrl}(s)", waitTime=0.1)
        time.sleep(wait_s)
        return True
    except Exception:
        return False


def kill_capcut(timeout_s: float = 8.0) -> bool:
    """Убивает все процессы CapCut.exe. Ждёт, пока реально завершатся."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "CapCut.exe", "/T"],
            capture_output=True,
        )
    except Exception:
        pass
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if not is_running():
            return True
        time.sleep(0.3)
    return not is_running()


def launch_capcut() -> bool:
    """Запускает CapCut (откроется на галерее проектов)."""
    if not CAPCUT_EXE.is_file():
        return False
    try:
        subprocess.Popen([str(CAPCUT_EXE), *CAPCUT_LAUNCH_ARGS])
        return True
    except Exception:
        return False


def wait_for_home(timeout_s: float = 30.0) -> bool:
    """Ждёт, пока CapCut покажет галерею (home) после запуска."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if get_state() == "home":
            return True
        time.sleep(0.5)
    return False


# Относительные координаты ПЕРВОЙ плитки в секции «Проекты» галереи,
# В СОСТОЯНИИ СРАЗУ ПОСЛЕ ЗАПУСКА CapCut (прокрутка вверху). Свежепропатченный
# проект — самый свежий по дате → первый в списке. Откалибровано на экране
# пользователя; можно переопределить env CAPCUT_TILE_X / CAPCUT_TILE_Y.
PROJECT_TILE_REL_X = float(os.environ.get("CAPCUT_TILE_X", "0.148"))
PROJECT_TILE_REL_Y = float(os.environ.get("CAPCUT_TILE_Y", "0.526"))


def _win32_double_click(x: int, y: int) -> None:
    """Системный двойной клик (надёжнее uia.Click для QML-окон CapCut)."""
    import ctypes
    u = ctypes.windll.user32
    u.SetCursorPos(int(x), int(y))
    time.sleep(0.3)
    for _ in range(2):
        u.mouse_event(2, 0, 0, 0, 0)  # LEFTDOWN
        u.mouse_event(4, 0, 0, 0, 0)  # LEFTUP
        time.sleep(0.06)


def open_first_project_tile(timeout_s: float = 40.0, log=print) -> bool:
    """Двойной клик по первой плитке проекта в галерее (= открыть проект).

    UI-дерево QML недоступно, поэтому клик по относительной координате окна.
    Наш проект после патча — самый свежий, значит первый в списке.
    Координата валидна для состояния галереи сразу после запуска (скролл вверху).
    """
    if not wait_for_home(timeout_s):
        log("  ⚠ галерея не появилась — проект придётся открыть вручную")
        return False
    # Пауза, чтобы плитки прогрузились и прокрутка устаканилась.
    time.sleep(3.5)
    win, state = _find_window()
    if win is None or state != "home":
        return False
    try:
        r = win.BoundingRectangle
        x = int(r.left + r.width() * PROJECT_TILE_REL_X)
        y = int(r.top + r.height() * PROJECT_TILE_REL_Y)
        win.SetActive()
        time.sleep(0.3)
        _win32_double_click(x, y)
        log(f"  ▶ двойной клик по плитке проекта ({x},{y})")
        # Дать CapCut перейти в редактор; проверить, что состояние сменилось.
        time.sleep(2.0)
        return get_state() == "edit"
    except Exception as ex:
        log(f"  ⚠ не удалось кликнуть плитку: {ex}")
        return False


class WriteGuard:
    """Контекст-менеджер безопасной записи в draft_content.json.

    Использование:
        with WriteGuard(auto=True) as g:
            ...патчим файл...
        # g.relaunched == True если CapCut был перезапущен

    На входе:
      • home/closed → ничего не делаем (файл свободен).
      • edit → Ctrl+S + kill (запоминаем, что надо перезапустить).
    На выходе:
      • если убивали CapCut — запускаем заново (галерея).
    """

    def __init__(self, auto: bool = True, log=print):
        self.auto = auto
        self.log = log
        self.killed = False
        self.relaunched = False
        self.entry_state: State = "closed"

    def __enter__(self) -> "WriteGuard":
        self.entry_state = get_state()
        if not self.auto:
            return self
        if self.entry_state == "edit":
            self.log("  CapCut: проект открыт в редакторе → сохраняю (Ctrl+S) и закрываю…")
            save_active_project()
            if kill_capcut():
                self.killed = True
                self.log("  CapCut: закрыт.")
            else:
                self.log("  ⚠ CapCut не закрылся — патч может быть затёрт.")
        elif self.entry_state == "dialog":
            # Диалог (например обновление) поверх галереи — закрываем процесс,
            # чтобы он не держал файл и не мешал.
            self.log("  CapCut: открыт диалог → закрываю приложение…")
            if kill_capcut():
                self.killed = True
        else:
            self.log(f"  CapCut: {self.entry_state} — файл свободен, пишу напрямую.")
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self.killed and exc_type is None:
            self.log("  CapCut: перезапускаю и открываю проект…")
            if launch_capcut():
                self.relaunched = True
                # Авто-открытие проекта: двойной клик по первой плитке
                # (наш проект свежайший → первый в галерее).
                open_first_project_tile(log=self.log)
        return False  # не подавляем исключения
