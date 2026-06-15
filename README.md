# permit-system

Внутренняя веб-система для создания, согласования, хранения и печати нарядов-допусков по DOCX-шаблонам.

## Назначение проекта
Система помогает оператору создать наряд, мастеру и начальнику согласовать его, администратору загрузить DOCX-шаблон, а пользователям скачать сформированный DOCX. UI реализован на Django templates без React и внешних CDN.

## Быстрый локальный запуск
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
unset DATABASE_URL
python manage.py migrate
python manage.py setup_roles
python manage.py seed_demo_data
python manage.py runserver
```
Откройте `http://127.0.0.1:8000/`. Если `DATABASE_URL`/`POSTGRES_HOST` не задан, используется SQLite `db.sqlite3`.

## Установка зависимостей
```bash
python -m pip install -r requirements-dev.txt
```
Runtime-зависимости перечислены в `requirements.txt`, dev/test-зависимости — в `requirements-dev.txt`.

## Миграции
```bash
python manage.py migrate
```
Для проверки отсутствия новых миграций:
```bash
python manage.py makemigrations --check --dry-run
```

## Создание superuser
```bash
python manage.py createsuperuser
```

## Роли и demo data
```bash
python manage.py setup_roles
python manage.py seed_demo_data
```
`seed_demo_data` создаёт demo-пользователей `operator`, `master`, `chief`, `admin` с паролем `demo12345`, справочники, персонал, наряды, участников и demo DOCX-шаблон. Не используйте эти данные как production-данные.

## Запуск сервера
```bash
python manage.py runserver
```

## Запуск тестов
```bash
python manage.py check
python manage.py test
```

## Docker Compose
```bash
docker compose up --build
```
В Compose поднимаются Django и PostgreSQL. Для обслуживания используйте `docker compose run --rm web python manage.py <command>`.

## Как создать наряд
1. Войдите пользователем с нужной ролью.
2. Нажмите «Создать наряд».
3. Заполните номер, даты, место, участок, вид работ, описание, ответственных пользователей и справочники.
4. Добавьте участников в блоке «Участники и ответственные».
5. Сохраните черновик и отправьте его на согласование из карточки наряда.

## Как использовать справочник персонала
`PersonnelGroup` и `Personnel` управляются через Django admin. Работники из справочника не являются пользователями сайта и не получают логин/пароль. Неактивные работники скрываются в новых формах, но сохраняются в старых нарядах.

## Как добавить участников наряда
В форме Permit выберите роль участника. Затем либо выберите `Personnel`, либо заполните ручной ввод участника. Можно добавить примечание; оно попадёт в отображение и DOCX context.

## Как создать DOCX-шаблон
Создайте DOCX-файл с переменными вида `{{ nomer_naryada }}`, загрузите его в `DocumentTemplate` через Django admin, задайте `document_type="permit"` и включите `is_active`. При генерации используется активный шаблон типа `permit`.

## Как проверить DOCX-шаблон
В Django admin для `DocumentTemplate` используйте проверку шаблона на demo-данных. Она формирует тестовый DOCX и не создаёт `GeneratedDocument`.

## Почему DOCX-переменные транслитом
Не используйте кириллицу внутри `{{ ... }}`. Транслит-переменные (`nomer_naryada`, `mesto_rabot`, `uchastniki_rabot`) стабильнее для `docxtpl`/Jinja и разметки Word. Подробная карта — в `DOCX_TEMPLATE_MAPPING.md`.

## Где находится FAQ
- Файл для чтения в репозитории: `FAQ.md`.
- Страница сайта: `/faq/`.
- Ссылка `FAQ` добавлена в меню.
- FAQ доступен без авторизации, чтобы справка была видна до входа.

## Известные ограничения
- Production deployment требует `.env`: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, `STATIC_ROOT`, `MEDIA_ROOT`.
- Реальный официальный DOCX-шаблон организации нужно загрузить отдельно.
- PDF-кнопка и сервисная заготовка реализованы, но конвертер выключен по умолчанию через `PDF_CONVERTER_ENABLED=0` и требует LibreOffice/`soffice`; production-ready PDF-сценарий остаётся pending.
- Полноценный autocomplete персонала pending; сейчас есть select и endpoint `/personnel/search/?q=`.
- Ручной выбор конкретного активного шаблона в пользовательском UI pending.
- React и внешние CDN не используются.
