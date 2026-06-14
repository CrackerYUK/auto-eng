# ARCHITECTURE.md

## Назначение
Документ фиксирует фактическую архитектуру `permit-system` и правила, которые нужно учитывать при развитии проекта.

## Общая схема
`permit-system` — классическое Django-приложение: backend, URL, forms, views и templates находятся в Django; UI строится на Django templates без React и без внешних CDN. PostgreSQL используется в Docker/production, SQLite — для локальных проверок без настроенного PostgreSQL.

## Приложения
- `users` — роли через стандартные Django Users/Groups. Auth User model не заменён. Команда `setup_roles` создаёт/обновляет группы `operator`, `master`, `chief`, `admin`.
- `permits` — модель `Permit`, справочники, персонал, участники, формы и web views нарядов.
- `approvals` — `ApprovalAction` и сервисы переходов workflow.
- `documents` — `DocumentTemplate`, `GeneratedDocument`, DOCX-генерация, demo-check шаблона и подготовительный PDF-сервис.
- `audit` — `AuditLog` для значимых действий.

## Справочники и персонал
Справочники работ: `WorkArea`, `Equipment`, `WorkType`, `Hazard`, `SafetyMeasure`.

Персонал хранится отдельно от пользователей сайта:
- `PersonnelGroup` — группа работников;
- `Personnel` — работник справочника без логина и пароля;
- `PermitParticipant` — участник конкретного наряда с ролью, ссылкой на `Personnel` или ручным вводом.

`User` нужен для входа, ролей, прав и аудита. `Personnel` нужен для заполнения наряда и DOCX. Эти сущности нельзя смешивать без отдельного архитектурного решения.

## Бизнес-логика
Бизнес-логика должна находиться в `services.py`, а не во views:
- workflow согласований — `approvals/services.py`;
- генерация DOCX/PDF — `documents/services.py`;
- views только принимают HTTP-запросы, проверяют доступ, обрабатывают forms и вызывают сервисы.

## Workflow согласований
Workflow проходит через существующие сервисы approvals. При изменениях нужно проверить исходный статус, целевой статус, роль, запись `ApprovalAction`, запись `AuditLog` и влияние на генерацию документов. Текущий запрос документации не меняет workflow.

## DOCX generation
`DocumentTemplate` — единственный источник правды для DOCX-шаблонов. `GeneratedDocument` — единственный источник готовых документов. Основной сервис — `generate_permit_docx(permit_id, template_id, user)`.

DOCX context собирается в `documents/services.py` в `_build_permit_context()`. Контекст содержит:
- совместимые старые английские ключи `permit.*`;
- основные транслит-переменные: `nomer_naryada`, `mesto_rabot`, `data_nachala`, `uchastniki_rabot`, `mery_bezopasnosti` и др.;
- переменные участников по ролям: `otvetstvennye_rukovoditeli`, `proizvoditeli_rabot`, `ispolniteli`, `chleny_brigady`, `dopuskayushchie`, `nablyudayushchie`, `prochie_uchastniki`.

Кириллицу внутри `{{ ... }}` для новых шаблонов не использовать.

## Проверка шаблонов
Проверка DOCX-шаблона на demo-данных реализована в `documents/services.py` через `generate_template_demo_docx()` и `_build_demo_template_context()`. Проверка не создаёт `GeneratedDocument` и нужна для безопасной проверки переменных/скобок до использования реального наряда.

## seed_demo_data
`users/management/commands/seed_demo_data.py` создаёт только demo-данные: пользователей, роли, справочники, персонал, наряды, участников и demo DOCX-шаблон. Это не production seed.

## FAQ
Публичная страница `/faq/` подключена в корневых URL через `TemplateView` и шаблон `templates/faq.html`. Она доступна без авторизации, потому что содержит справку по входу, запуску и базовым сценариям.

## Ограничения
- Не добавлять React и CDN.
- Не менять auth User model без отдельного решения.
- Не менять workflow согласований в документационных PR.
- Не обходить `generate_permit_docx` альтернативной DOCX-генерацией.
- PDF зависит от LibreOffice/`soffice` и выключен по умолчанию.
