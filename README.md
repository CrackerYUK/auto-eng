# permit-system

Внутренняя веб-система для создания, согласования, хранения и печати нарядов-допусков по DOCX-шаблонам.

## Технологии

- Python
- Django
- PostgreSQL
- Docker Compose
- docxtpl для генерации DOCX
- pytest / Django tests

## Структура проекта

- `permit_system/` — настройки и корневые URL Django-проекта.
- `users/` — пользователи и роли.
- `permits/` — наряды-допуски.
- `approvals/` — маршруты и статусы согласования.
- `documents/` — DOCX-шаблоны и генерация документов.
- `audit/` — аудит действий пользователей.
- `tests/` — smoke-тесты каркаса проекта.
- `requirements.txt` — runtime-зависимости приложения.
- `requirements-dev.txt` — зависимости для разработки и тестов.

## Запуск локально через Docker Compose

Docker Compose поднимает полный локальный стек: Django-приложение `web` и PostgreSQL `db`.

Соберите и запустите сервисы:

```bash
docker compose up --build
```

После запуска приложение будет доступно по адресу:

```text
http://localhost:8000/
```

Проверка работоспособности:

```text
http://localhost:8000/health/
```

В контейнере `web` миграции применяются автоматически при старте. При необходимости можно выполнить команду вручную:

```bash
docker compose run --rm web python manage.py migrate
```

Запуск тестов через Docker Compose:

```bash
docker compose run --rm web python manage.py test
```

## Проверки без Docker

Для запуска проверок без Docker создайте и активируйте виртуальное окружение, затем установите dev-зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Если переменная `POSTGRES_HOST` не задана, проект использует SQLite по умолчанию. Это позволяет запускать базовые проверки без Docker и без локального PostgreSQL:

```bash
python manage.py check
python manage.py test
```

При необходимости можно также запускать pytest:

```bash
pytest
```

## Команды для Codex Cloud

В Codex Cloud Docker может отсутствовать, а доступ к package index может быть ограничен. Поэтому `docker compose config` и другие Docker-команды не являются обязательными cloud-check командами.

Основные и обязательные проверки Codex Cloud:

```bash
python manage.py check
python manage.py test
```

В Codex Cloud не нужно выполнять генерацию скриншотов или проверять наличие браузеров/утилит для визуальных снимков. Отсутствие Chromium, Firefox, wkhtmltoimage или аналогичных инструментов не является ошибкой проекта. UI-проверки в Codex Cloud выполняются через Django test client: `status_code`, отрисовку шаблонов, ожидаемый HTML-текст, кнопки, ссылки и формы. Ручной визуальный просмотр выполняется локально или на сервере развёртывания.

Если зависимости ещё не установлены и команда установки завершается ошибкой доступа к package index, например `403 Forbidden`, это ограничение окружения Codex Cloud, а не ошибка кода. В таком случае в итоговом отчёте нужно явно указать, что проверки не были выполнены из-за недоступности зависимостей.


## Базовые роли

Проект использует стандартные Django Groups/Permissions для базовой ролевой модели.
Начальные группы:

- `operator`
- `master`
- `chief`
- `admin`

После применения миграций создайте или обновите группы и их базовые права командой:

```bash
python manage.py setup_roles
```

При запуске через Docker Compose используйте:

```bash
docker compose run --rm web python manage.py setup_roles
```

Команда идемпотентна: её можно запускать повторно, чтобы привести права групп к текущим настройкам проекта.

## Переменные окружения

Основные переменные окружения для Docker Compose и PostgreSQL задаются в `docker-compose.yml`:

- `DJANGO_DEBUG`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Если `POSTGRES_HOST` не задан, Django использует локальную SQLite-базу `db.sqlite3` для проверок и разработки без Docker.
