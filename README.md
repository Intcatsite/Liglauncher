# 🚀 LigLauncher v2

[![Telegram Channel](https://img.shields.io/badge/Telegram-Channel-229ED9?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/cheb0chik)
[![GitHub release](https://img.shields.io/github/v/release/intcatsite/Liglauncher?style=for-the-badge&color=black)](https://github.com/intcatsite/Liglauncher/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/Intcatsite/Liglauncher)

### 📋 Описание

**LigLauncher** — офлайн (пиратский) лаунчер Minecraft с полностью кастомизируемым,
прозрачным интерфейсом без рамок окна. Без Microsoft-аккаунта, без премиума.

* 🎨 **Полная кастомизация**: акцентный цвет, шрифт, фон, прозрачность окна — свой тайтлбар,
  который сливается с фоном; окно можно свернуть, развернуть на весь экран или закрыть без
  системной рамки.
* 👥 **Мультиаккаунты**: создавайте сколько угодно офлайн-профилей (пачками хоть по 1000),
  переименовывайте и удаляйте их одним кликом.
* 🖼 **Скины**: загружаете PNG/JPG (64×64) для каждого аккаунта — отдельно под каждую версию
  Minecraft, либо один "по умолчанию" на все версии. В списке аккаунтов и в профиле аватаркой
  служит голова вашего скина.
* 🌐 **Создать сервер**: одна кнопка — лаунчер качает и поднимает локальный ванильный сервер
  нужной версии и пробрасывает его в интернет через [CraftIP](https://craftip.net), выдавая
  публичный адрес вида `xxxx.craftip.net`.
* 🧱 Поддержка **Vanilla / Forge / Fabric / Quilt**, все версии — релизы, снапшоты, old_alpha/beta.
* 📦 Portable — не требует установки.

---

## 📥 Загрузка

<a href="https://github.com/intcatsite/Liglauncher/releases/latest">
  <img src="https://img.shields.io/badge/СКАЧАТЬ_LIGLAUNCHER-FF4500?style=for-the-badge&logo=github&logoColor=white&labelColor=000000" height="60">
</a>

> Релизы под Windows собираются автоматически по тегу `vX.Y.Z`
> через GitHub Actions (см. `.github/workflows/release.yml`).

---

## 🌍 Сайт-лендинг

В папке [`site/`](site/) — статическая страница-визитка (скриншоты, список
возможностей, кнопка скачать последний релиз). Задеплоить можно куда угодно:

* **Netlify**: кнопка «Deploy to Netlify» вверху README — подключит репозиторий
  и опубликует `site/` без единой настройки (там уже лежит `netlify.toml`).
* **GitHub Pages / Vercel / Cloudflare Pages**: то же самое, укажите `site/`
  как корень публикации — сайт полностью статический, без сборки.

Кнопка «Скачать» на сайте ведёт на
`.../releases/latest/download/LigLauncher.exe` — это стабильная ссылка от
GitHub, которая всегда указывает на актив `LigLauncher.exe` последнего
опубликованного релиза.
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

## 🖌 Кастомизация интерфейса

Всё — на странице **Настройки**:

| Что | Как |
|---|---|
| Акцентный цвет | Кнопка-палитра открывает выбор цвета, применяется сразу |
| Шрифт | Любой шрифт, установленный в системе, + размер |
| Фон окна | Любое изображение (PNG/JPG/WEBP), масштабируется под окно |
| Прозрачность | Ползунок 40–100% |
| Режим окна | Окно / Полный экран, без системной рамки в обоих случаях |

---

## 🔄 Автообновление

Собранный `.exe` при запуске сам проверяет
[GitHub Releases](https://github.com/intcatsite/Liglauncher/releases) и,
если вышла версия новее текущей, предлагает обновиться прямо из
приложения — скачивает новый `LigLauncher.exe`, подменяет себя и
перезапускается. Проверить вручную можно кнопкой «Проверить обновления»
на странице **Настройки**.

**Чтобы это сработало, релиз должен быть настоящим GitHub Release**, а не
просто прогоном workflow — для этого:

1. Поднимите версию в `liglauncher/__init__.py` (`__version__`) и `pyproject.toml`.
2. Запушьте тег: `git tag vX.Y.Z && git push origin vX.Y.Z`.
3. `.github/workflows/release.yml` соберёт `.exe` и опубликует его как Release
   с этим тегом — именно этот Release и находит автообновитель.

Обычные прогоны через "Run workflow" (без тега) не создают Release и
автообновителем не подхватываются — они только для тестовых сборок.

---

## 👥 Мультиаккаунты и скины

На странице **Аккаунты**:

* Добавляйте аккаунты по одному или пачкой (`Player1`…`Player1000` за один клик).
* У каждого аккаунта — детерминированный offline-UUID (как у ванильного сервера
  в `online-mode=false`), поэтому один и тот же ник всегда даёт один и тот же скин/UUID.
* Загружайте свой скин (64×64 PNG/JPG) для конкретной версии или "по умолчанию" на все версии
  — хранится в `<данные лаунчера>/skins/<uuid>/<версия>/skin.png`.

**Важно про скины в игре:** ванильный офлайн-клиент физически не умеет показывать локальные
скины — он спрашивает скин у Mojang, а офлайн-аккаунта там не существует. Поэтому на Fabric/Forge
лаунчер сам ставит мод [CustomSkinLoader](https://github.com/xfl03/MCCustomSkinLoader) и
подкладывает ваш скин в его локальную папку. При первом запуске один раз включите в моде
локальные скины (`/csl gui` в чате, либо `CustomSkinLoader/CustomSkinLoader.json` в папке игры).
На чистом Vanilla без загрузчика модов скин в игре не отобразится — это ограничение самого
движка, не лаунчера.

---

## 🌐 Создать сервер (CraftIP)

На странице **Серверы**: имя, версия, порт → «Создать сервер». Лаунчер:

1. Скачивает ванильный `server.jar` нужной версии и поднимает сервер локально.
2. Как только сервер готов — запускает настоящий клиент
   [CraftIP](https://codeberg.org/craftip/craftip) (независимый opensource-туннель, Rust) и
   получает от их сервиса реальный публичный адрес `xxxx.craftip.net`, который можно сразу
   давать друзьям.

CraftIP не публикует готовые бинарники, поэтому клиент собирается один раз из исходников —
для этого на вашей машине должны быть `git` и `cargo` (Rust, ставится с
[rustup.rs](https://rustup.rs)). Если их нет, кнопка «Собрать CraftIP» покажет, чего не хватает;
сервер при этом всё равно поднимется локально.

---

## 📄 Лицензия

MIT — см. [LICENSE](LICENSE).
