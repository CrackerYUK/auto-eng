# Инструкции для Codex

## Назначение проекта

`permit-system` — Django-приложение для создания, согласования, хранения и печати нарядов-допусков по DOCX-шаблонам.

## Технологический стек

- Python и Django для веб-приложения.
- PostgreSQL как основная база данных в Docker Compose и будущих окружениях развёртывания.
- SQLite как локальная база по умолчанию для проверок без Docker, если `POSTGRES_HOST` не задан.
- Docker Compose для локального запуска полного стека.
- `docxtpl` для генерации DOCX-документов по шаблонам.
- `pytest` или стандартные Django tests для тестирования.

## Правила разработки

- Сохраняйте проект запускаемым через `docker compose up --build`.
- Проверки Codex Cloud не должны требовать Docker или `docker compose config`: Docker в контейнере Codex может отсутствовать.
- Основной cloud-check для Codex:
  - `python manage.py check`
  - `python manage.py test`
- Для локальных проверок без Docker установите dev-зависимости командой `python -m pip install -r requirements-dev.txt`.
- Если установка зависимостей невозможна из-за ограничения сети или package index в Codex Cloud, явно укажите это в отчёте как ограничение окружения, а не ошибку кода.
- Новую бизнес-логику размещайте в соответствующих Django-приложениях:
  - `users` — пользователи, роли, права.
  - `permits` — данные и процессы нарядов-допусков.
  - `approvals` — согласования и маршруты утверждения.
  - `documents` — DOCX-шаблоны, генерация и хранение документов.
  - `audit` — журналирование значимых действий.
- Не храните секреты в коде; используйте переменные окружения.
- При изменениях добавляйте или обновляйте тесты.
- Перед коммитом запускайте релевантные тесты; минимум `python manage.py check` и `python manage.py test` для изменений в Python-коде, если зависимости доступны.

## Codex Cloud visual limitations

- Do not attempt screenshot generation in Codex Cloud.
- Missing chromium/firefox/wkhtmltoimage is not a project failure.
- UI checks must be done with Django test client:
  - `status_code`
  - template rendering
  - expected HTML text
  - expected buttons/links/forms
- Manual visual review is performed locally or on the deployment server.
