# PROJECT_STATE.md

## Назначение
`permit-system` — внутренняя веб-система для создания, согласования, хранения и печати нарядов-допусков по DOCX-шаблонам. Django-проект находится в корне репозитория; команды запускаются рядом с `manage.py`.

## Текущая структура
- `permit_system/` — настройки, корневые URL, healthcheck и публичная страница `/faq/`.
- `users/` — роли и management-команда `setup_roles`; auth User model не заменён.
- `permits/` — наряды, справочники, персонал, участники, формы, views, URL и templates.
- `approvals/` — workflow согласований и `ApprovalAction`.
- `documents/` — `DocumentTemplate`, `GeneratedDocument`, генерация DOCX и проверка шаблона.
- `audit/` — `AuditLog`.
- `templates/` — Django templates без React и без внешних CDN.
- `tests/` — проектные тесты, включая smoke-тесты документации и FAQ.

## Реализовано
- Базовый Django-проект с Docker Compose, PostgreSQL для стека и SQLite по умолчанию без `DATABASE_URL`/`POSTGRES_HOST`.
- Роли пользователей через Django Groups: `operator`, `master`, `chief`, `admin`.
- Permit workflow: черновик, отправка мастеру, возврат, согласование мастером, утверждение начальником, отклонение, закрытие и архивные статусы.
- Справочники `WorkArea`, `Equipment`, `WorkType`, `Hazard`, `SafetyMeasure`.
- Справочник персонала `PersonnelGroup` и `Personnel`.
- Участники наряда через `PermitParticipant` с ролями, выбором работника из справочника и ручным вводом участника.
- Базовый русский интерфейс на Django templates: dashboard, список, карточка, создание и редактирование наряда, действия workflow.
- DOCX-генерация через `generate_permit_docx`.
- `DocumentTemplate` как единственный источник DOCX-шаблонов и `GeneratedDocument` как источник готовых документов.
- Проверка DOCX-шаблона на demo-данных в Django admin без создания `GeneratedDocument`.
- Безопасные транслит-переменные DOCX: `nomer_naryada`, `mesto_rabot`, `uchastniki_rabot` и др.; старые английские переменные сохранены для совместимости.
- Demo setup через `seed_demo_data`: пользователи, роли, справочники, персонал, наряды, участники и demo DOCX-шаблон.
- Аудит значимых действий через `AuditLog` и история согласований через `ApprovalAction`.
- Подготовительный PDF-слой: `file_pdf`, `convert_docx_to_pdf`, `PDF_CONVERTER_ENABLED`, `SOFFICE_PATH`; по умолчанию выключен.
- FAQ: файл `FAQ.md`, публичная страница `/faq/` и ссылка `FAQ` в меню. FAQ доступен всем, чтобы помощь была видна до входа.

## Частично реализовано
- PDF: есть сервисная заготовка и тесты через mock, но пользовательский PDF-сценарий не включён по умолчанию и зависит от LibreOffice/`soffice`.
- Выбор персонала: есть обычный select и endpoint `/personnel/search/?q=`, но полноценный autocomplete в форме наряда ещё не подключён.
- Управление DOCX-шаблонами: есть Django admin и проверка шаблона, но отдельный удобный пользовательский UI и версионирование шаблонов ещё не реализованы.
- Аудит изменений наряда покрывает ключевые события, но набор аудируемых полей и сценариев нужно подтвердить с пользователями.

## Не реализовано / pending
- Полноценный autocomplete персонала без внешних CDN — отдельный UX PR, чтобы не менять workflow и формы рискованно в документационном PR.
- Поиск и фильтры нарядов — отдельный PR для list/dashboard UX.
- Ручной выбор конкретного активного DOCX-шаблона при генерации — отдельный UX PR; сейчас выбирается последний активный `permit`-шаблон.
- Версионирование DOCX-шаблонов — отдельное архитектурное решение вокруг `DocumentTemplate`.
- Пользовательский PDF-экспорт — отдельный PR после решения, нужен ли PDF в пилоте.
- Production deployment — требует `.env`, доменов, reverse proxy/TLS, backup и проверки инфраструктуры организации.
- Официальный DOCX-шаблон организации — должен быть загружен отдельно; demo-шаблон не является официальным.
- Аудит безопасности и пользовательское тестирование — отдельные этапы перед пилотом.

## Известные ограничения
- PDF зависит от LibreOffice/`soffice` и может быть выключен через `PDF_CONVERTER_ENABLED=0`.
- Production deployment требует настройки `.env`: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, `STATIC_ROOT`, `MEDIA_ROOT`.
- Реальный официальный DOCX-шаблон нужно загрузить отдельно через `DocumentTemplate`.
- Не используйте кириллицу внутри DOCX-переменных `{{ ... }}`; основные переменные — транслит.
- Полноценный autocomplete персонала pending; текущий UI использует select и ручной ввод.
- Внешние CDN и React не используются.

## Обязательные проверки
```bash
python manage.py makemigrations --check --dry-run
python manage.py check
python manage.py test
```
Если зависимости недоступны из-за package index/network, это ограничение окружения, а не ошибка кода.
