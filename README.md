![example workflow](https://github.com/Marymarian/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg)

# Адрес проекта
* http://158.160.8.9/admin
* http://158.160.8.9/

# Проект Foodgram
Cайт Foodgram - «Продуктовый помощник». Это онлайн-сервис и API для него. На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

## Распаковка проекта
### Запуск проекта в dev-режиме
- Установите и активируйте виртуальное окружение
```
python -m venv venv
``` 
```
source venv/Scripts/activate
``` 
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- В папке с файлом manage.py выполните команды:
```
python3 manage.py migrate
```
```
python3 manage.py runserver
```
# Запуск проекта в контейнерах Docker
Установите на сервере docker и docker-compose.
Создайте файл /infra/.env. 
# Шаблон наполнения env-файла

DB_ENGINE= указываем базу, с которой работаем: django.db.backends.postgresql
DB_NAME= имя БД
POSTGRES_USER= логин для подключения
POSTGRES_PASSWORD= пароль для подключения
DB_HOST= название контейнера
DB_PORT= порт для подключения к БД, например 5432

Перейдите в раздел infra для сборки docker-compose:
```
docker-compose up -d --buld.
```
Выполнить миграции:

```
docker-compose exec backend python manage.py migrate
```
Создать суперпользователя:

```
docker-compose exec backend python manage.py createsuperuser.
```
Изменить пароль для пользователя admin:

```
docker-compose exec backend python manage.py changepassword admin
```
Собратить файлы статики:

```
docker-compose exec backend python manage.py collectstatic --no-input
```
Заполнить базу можно готовыми ингредиентами или создавать свои:
```
docker-compose exec backend python manage.py load_ingredients
```
Для корректного создания рецепта, необходимо создать пару тегов в базе через админ-панель.

## Пользовательские роли и права доступа
* Гость (неавторизованный пользователь) - может создать аккаунт, просматривать рецепты, страницы пользователей.
* Авторизованный пользователь (user) - может оздавать/редактировать/удалять собственные рецепты, просматривать рецепты, страницы пользователей, работать с избранным и списком покупок, подписываться на авторов.
* Администратор (admin) — полные права на управление всем контентом проекта. 
* Суперюзер Django должен всегда обладать правами администратора, пользователя с правами admin. Даже если изменить пользовательскую роль суперюзера — это не лишит его прав администратора. Суперюзер — всегда администратор, но администратор — не обязательно суперюзер.

## Технологии
Python 3.7, Django 2.2.27, Django REST, Docker.

## Авторы
Марина Чухарева
- [@Marymarian](https://www.github.com/Marymarian)


