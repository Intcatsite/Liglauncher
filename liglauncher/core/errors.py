"""Turn common low-level exception text into a message a player can act on."""
from __future__ import annotations

import re

_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"NameResolutionError|getaddrinfo failed|Failed to resolve|Max retries exceeded|ConnectionError", re.I),
        "Не удалось скачать файлы: ни серверы Mojang, ни резервное зеркало (BMCLAPI) не отвечают.\n\n"
        "Проверьте интернет-соединение и повторите. Если сеть работает, но ошибка "
        "повторяется — попробуйте сменить DNS (например, на 1.1.1.1 или 8.8.8.8) "
        "или включить VPN.",
    ),
    (
        re.compile(r"WinError 32|being used by another process|used by another process", re.I),
        "Файл установки временно занят другим процессом (часто из-за антивируса, "
        "проверяющего скачанный файл). Обычно это проходит само за несколько секунд — "
        "попробуйте установить ещё раз.",
    ),
    (
        re.compile(r"PermissionError|Errno 13|Access is denied", re.I),
        "Нет доступа к файлу или папке лаунчера. Проверьте, что антивирус не блокирует "
        "LigLauncher, и что у вас есть права на запись в папку с игрой.",
    ),
    (
        re.compile(r"No space left|Errno 28", re.I),
        "На диске закончилось свободное место.",
    ),
)


def friendly_message(raw: str) -> str:
    """Return a human-readable explanation for a known error, or the raw text."""
    for pattern, message in _PATTERNS:
        if pattern.search(raw):
            return message
    return raw
