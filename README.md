# Основной адрес проекта
* 127.0.0.1/ (http://<your.ip>/)
# Страница рецептов
* 127.0.0.1/recipes (http://<your.ip>/recipes)
# Админ-панель
* 127.0.0.1/admin (http://<your.ip>/admin)

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
* DB_ENGINE= указываем базу, с которой работаем: django.db.backends.postgresql
* DB_NAME= имя БД
* POSTGRES_USER= логин для подключения
* POSTGRES_PASSWORD= пароль для подключения
* DB_HOST= название контейнера
* DB_PORT= порт для подключения к БД, например 5432
* SECRET_KEY= секретный ключ Джанго

Перейдите в раздел infra для сборки docker-compose:
```
docker-compose up -d --buld.
```
Выполните миграции:

```
docker-compose exec backend python manage.py migrate
```
Создайте суперпользователя:

```
docker-compose exec backend python manage.py createsuperuser.
```
Изменить пароль для пользователя admin:

```
docker-compose exec backend python manage.py changepassword admin
```
Собрать файлы статики:

```
docker-compose exec backend python manage.py collectstatic --no-input
```
Заполнить базу можно готовыми ингредиентами или создавать свои:
```
docker-compose exec backend python manage.py load_ingredients
```
Для корректного создания рецепта, необходимо создать пару тегов в базе через админ-панель.

## Технологии
Python 3.7, Django 2.2.27, Django REST, Docker.

## Авторы
Марина Чухарева
- [@Marymarian](https://www.github.com/Marymarian)


## Демо
### Проект был развернут на удаленном сервере | YandexCloud
### Рецепты
![](https://github.com/Marymarian/foodgram-project-react/blob/master/gif/recipes2.gif) 
### Еще рецепты
![](https://github.com/Marymarian/foodgram-project-react/blob/master/gif/recipes.gif)
### Избранное
![](https://github.com/Marymarian/foodgram-project-react/blob/master/gif/favorites.gif)
### Подписки
![](https://github.com/Marymarian/foodgram-project-react/blob/master/gif/follows.gif)
### Добавление рецепта
![](https://github.com/Marymarian/foodgram-project-react/blob/master/gif/get_recipes.gif)
### Список покупок
![](https://github.com/Marymarian/foodgram-project-react/blob/master/gif/shop_cart.gif)
### Рецепт
![](https://github.com/Marymarian/foodgram-project-react/blob/master/gif/resipe.gif)
### Тэги
![](https://github.com/Marymarian/foodgram-project-react/blob/master/gif/tags.gif)
### Регистрация
![](https://github.com/Marymarian/foodgram-project-react/blob/master/gif/sign_in.gif)
### Вход
![](https://github.com/Marymarian/foodgram-project-react/blob/master/gif/log_in.gif)


