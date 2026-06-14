# AGENTS.md

## Назначение
Репозиторий содержит `permit-system` — внутреннюю Django-систему для создания, согласования, хранения и печати нарядов-допусков по DOCX-шаблонам. Область действия файла — весь репозиторий.

## Стек
- Python, Django, Django templates.
- PostgreSQL в Docker/production; SQLite для локальных проверок без PostgreSQL.
- Docker/Docker Compose для локального полного стека.
- `docxtpl` / `python-docx` для DOCX.
- `pytest` или стандартные Django tests.
- React не используется и не должен добавляться без отдельного архитектурного решения.

## Приложения
- `users` — пользователи, роли, `setup_roles`; auth User model не менять.
- `permits` — наряды, справочники, персонал, участники.
- `approvals` — workflow согласований.
- `documents` — DOCX-шаблоны, генерация, проверка шаблонов, подготовительный PDF-слой.
- `audit` — журнал значимых действий.

## Обязательные правила
1. Не менять бизнес-логику без явного запроса.
2. Не менять workflow согласований без явного запроса.
3. Не менять auth User model без отдельного архитектурного решения.
4. Не дублировать модели, формы, views, urls, templates и сервисы.
5. Перед добавлением сущности искать существующую реализацию.
6. Бизнес-логику держать в `services.py`, а не во views.
7. Использовать Django templates; не добавлять React.
8. Не использовать внешние CDN, Google Fonts, unpkg, Bootstrap CDN, Font Awesome CDN и аналогичные ресурсы.
9. Не хранить секреты в коде; использовать переменные окружения.
10. Не использовать screenshot-команды в Codex Cloud.
11. Не переводить DOCX-переменные на кириллицу. Для новых шаблонов использовать транслит-переменные (`nomer_naryada`, `mesto_rabot`, `uchastniki_rabot`).
12. Не писать в документации, что функция реализована, если она только planned/pending.
13. При изменениях добавлять или обновлять тесты.

## Инварианты
- `DocumentTemplate` — единственный источник правды для DOCX-шаблонов.
- `GeneratedDocument` — единственный источник правды для готовых документов.
- `generate_permit_docx` — основной сервис DOCX-генерации.
- Согласования проходят через существующие approvals-сервисы.
- Аудит значимых действий сохраняется через `AuditLog`.

## Обязательные проверки
Перед сдачей изменений выполнить из корня:
```bash
python manage.py makemigrations --check --dry-run
python manage.py check
python manage.py test
```
Если зависимости отсутствуют, сначала попробовать:
```bash
python -m pip install -r requirements-dev.txt
```
Недоступность package index/network считать ограничением окружения, а не ошибкой кода.

## Документация
- Обновлять `PROJECT_STATE.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `README.md`, `DOCX_TEMPLATE_MAPPING.md`, `LOCAL_TEST_CHECKLIST.md`, `DEPLOYMENT_PLAN.md`, `USER_FEEDBACK_QUESTIONS.md` по факту изменения.
- Pending-функции явно помечать как pending.
- FAQ поддерживать в `FAQ.md` и на странице `/faq/`.
