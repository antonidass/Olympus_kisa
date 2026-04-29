"""Лаунчер video_runner для мифа «Сизифов Труд».

Нужен потому что cmd.exe на русской Windows читает .bat в cp866 и разрывает
кириллицу в путях. Python обрабатывает UTF-8 в исходниках корректно, поэтому
здесь путь с кириллицей безопасно хранится как Python-строка.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Подключаем automation/ в sys.path чтобы импортировать video_runner
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import video_runner  # noqa: E402

if __name__ == "__main__":
    markdown = HERE.parent / "content" / "Сизифов Труд" / "prompts" / "video.md"
    if not markdown.exists():
        print(f"❌ Файл не найден: {markdown}")
        sys.exit(1)
    video_runner.run(markdown, scenes_filter=None, start_from=18, headless=False)
