# DEPLOYMENT_PLAN.md

## Назначение
План тестового/production-развёртывания `permit-system` во внутренней инфраструктуре.

## .env и переменные окружения
Создайте `.env` из `.env.example` и не храните реальные секреты в Git.

Обязательные настройки:
- `DJANGO_SECRET_KEY` — длинный случайный секрет.
- `DJANGO_DEBUG=0` — для сервера.
- `DJANGO_ALLOWED_HOSTS` — домены/IP через запятую.
- `CSRF_TRUSTED_ORIGINS` — доверенные HTTPS-origin, если используется reverse proxy/TLS.
- `DATABASE_URL` — PostgreSQL для сервера.
- `STATIC_ROOT` — каталог собранной статики.
- `MEDIA_ROOT` — постоянный каталог/volume для DOCX-шаблонов и готовых документов.
- `PDF_CONVERTER_ENABLED` — `0` по умолчанию; `1` только после проверки LibreOffice.
- `SOFFICE_PATH` — путь к LibreOffice/`soffice`, если PDF включён.

## Static и media
- Выполнить `python manage.py collectstatic --noinput`.
- Настроить отдачу static через reverse proxy или согласованный production-способ.
- `MEDIA_ROOT` должен быть постоянным volume/каталогом и входить в backup.
- DOCX-шаблоны и сформированные DOCX/PDF нельзя терять при пересборке контейнера.

## Базовый порядок запуска
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_roles
python manage.py createsuperuser
```
`seed_demo_data` разрешён только для демонстрационного стенда; перед production-данными demo-записи нужно удалить или не создавать.

## Docker Compose
`docker-compose.yml` можно использовать как базу для тестового стенда. Перед эксплуатацией нужно отдельно настроить домен, reverse proxy, TLS, backup и доступы.

## Резервное копирование
Backup должен включать:
- PostgreSQL database dump;
- весь `MEDIA_ROOT`;
- информацию о версии кода/commit;
- копию `.env` в защищённом хранилище или перечень значений, необходимых для восстановления.

Перед пилотом нужно выполнить тестовое восстановление.

## PDF / LibreOffice
PDF-конвертация опциональна. Если нужна:
- установить LibreOffice/`soffice` на сервер;
- задать `PDF_CONVERTER_ENABLED=1` и `SOFFICE_PATH`;
- проверить результат на официальном DOCX-шаблоне;
- оставить выключенной, если LibreOffice недоступен или форматирование не подтверждено.

## Готовность к пилоту
- `DEBUG=0`.
- `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` соответствуют домену.
- PostgreSQL подключён через `DATABASE_URL`.
- Static собрана, media постоянна.
- Роли и superuser созданы.
- Backup БД и media настроен и проверен восстановлением.
- Официальный DOCX-шаблон загружен и проверен.
- FAQ доступен пользователям.
