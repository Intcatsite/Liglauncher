# 🚀 LigLauncher (Black Edition)

[![Telegram Channel](https://img.shields.io/badge/Telegram-Channel-229ED9?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/cheb0chik)
[![GitHub release](https://img.shields.io/github/v/release/intcatsite/Liglauncher?style=for-the-badge&color=black)](https://github.com/intcatsite/Liglauncher/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

### 📋 Краткое описание
**LigLauncher** — минималистичный **офлайн** лаунчер Minecraft с чёрным интерфейсом.
Без Microsoft-аккаунта, без премиума, без лишнего мусора. Только ник, версия и кнопка
**ИГРАТЬ**.

* ⚡ Быстрый запуск, нативный Python.
* 🌑 Чёрная тема на CustomTkinter.
* 📦 Portable — не требует установки.
* 🧱 Поддержка **Vanilla / Forge / Fabric / Quilt**.
* 🕹 Все версии Minecraft: релизы, снапшоты, old_alpha, old_beta.
* 👤 Офлайн-аккаунты (детерминированный UUID, как у ванильного сервера в offline-mode).

---

## 📥 Загрузка

<a href="https://github.com/intcatsite/Liglauncher/releases/latest">
  <img src="https://img.shields.io/badge/СКАЧАТЬ_LIGLAUNCHER-FF4500?style=for-the-badge&logo=github&logoColor=white&labelColor=000000" height="60">
</a>

> Релизы под Windows собираются автоматически по тегу `vX.Y.Z`
> через GitHub Actions (см. `.github/workflows/release.yml`).

---

## 🛠 Запуск из исходников

Требуется **Python 3.10+** и установленная **Java** (8 / 17 / 21 — в зависимости
от версии Minecraft; `minecraft-launcher-lib` сам подскажет, если чего-то не хватает).

```bash
git clone https://github.com/intcatsite/Liglauncher.git
cd Liglauncher
pip install -r requirements.txt
python -m liglauncher
```

### Сборка `.exe` (Windows)

```bash
pip install -r requirements.txt pyinstaller
python build.py
# готовый файл — dist/LigLauncher.exe
```

---

## 🗂 Структура проекта

```
liglauncher/
├── core/
│   ├── auth.py        # офлайн-аккаунт: ник → UUID v3 ("OfflinePlayer:<name>")
│   ├── installer.py   # установка vanilla / Forge / Fabric / Quilt
│   ├── launcher.py    # сборка JVM-команды и запуск процесса Minecraft
│   └── versions.py    # списки версий и проверка совместимости лоадеров
├── ui/
│   ├── app.py         # главное окно (CustomTkinter)
│   └── theme.py       # чёрная палитра
├── config.py          # сохранение настроек (config.json)
├── log.py             # логирование с ротацией
├── paths.py           # кросс-платформенные пути
└── __main__.py        # точка входа
```

Данные пользователя:

| OS       | Путь                                              |
|----------|---------------------------------------------------|
| Windows  | `%APPDATA%\LigLauncher\`                          |
| macOS    | `~/Library/Application Support/LigLauncher/`      |
| Linux    | `~/.local/share/LigLauncher/`                     |

Внутри: `config.json`, `logs/launcher.log`, `minecraft/` (игровая директория).

---

## 🔐 Об офлайн-аккаунтах

Лаунчер не общается с серверами Microsoft / Mojang для авторизации.
UUID игрока генерится из его ника по той же формуле, что использует
ванильный Minecraft-сервер при `online-mode=false`:

```
uuid = UUID.nameUUIDFromBytes(("OfflinePlayer:" + name).getBytes("UTF-8"))
```

Это значит:
- На офлайн-серверах ты будешь определяться так же, как при подключении
  обычным клиентом без премиума.
- На официальных премиум-серверах подключиться, конечно, не получится —
  это особенность любого офлайн-лаунчера.

---

## 🌐 Контакты

* **GitHub:** [intcatsite](https://github.com/intcatsite/)
* **TGK:** [@cheb0chik](https://t.me/cheb0chik)

---

**Developed for the intcatsite community.**
