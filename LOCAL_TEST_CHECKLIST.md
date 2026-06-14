# LOCAL_TEST_CHECKLIST.md

## Автоматические проверки
- [ ] `python manage.py makemigrations --check --dry-run`
- [ ] `python manage.py check`
- [ ] `python manage.py test`

## Подготовка
- [ ] Установить зависимости: `python -m pip install -r requirements-dev.txt`.
- [ ] Применить миграции: `python manage.py migrate`.
- [ ] Создать роли: `python manage.py setup_roles`.
- [ ] Запустить `seed_demo_data`: `python manage.py seed_demo_data`.
- [ ] Запустить сервер: `python manage.py runserver`.

## Ручные проверки UI
- [ ] Вход в систему demo-пользователем.
- [ ] Создание Permit.
- [ ] Редактирование Permit в статусе черновика/возврата.
- [ ] Добавление участников.
- [ ] Выбор работника из справочника.
- [ ] Ручной ввод участника.
- [ ] Отправка на согласование.
- [ ] Согласование мастером.
- [ ] Утверждение начальником.
- [ ] Генерация DOCX.
- [ ] Скачивание DOCX.
- [ ] Проверка DOCX-шаблона на demo-данных в admin.
- [ ] FAQ доступен по `/faq/`, ссылка есть в меню.
- [ ] Русский интерфейс понятен на основных страницах.
- [ ] `seed_demo_data` создаёт пользователей, справочники, персонал, наряды и demo-шаблон.

## Важные ограничения проверки
- Не использовать screenshot-команды в Codex Cloud.
- Отсутствие Chromium/Firefox/wkhtmltoimage не является ошибкой проекта.
- Если на Windows DOCX заблокирован Word/LibreOffice, закрыть файл и повторить проверку.
