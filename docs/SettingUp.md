#Frontend

[Репозиторий фронтенда](https://github.com/imterana/MVFrontend)


### Установка зависимостей

    $ npm install
    
### Запуск
    $ sudo PORT=80 HOST='0.0.0.0' npm start
    
#Backend

[Репозиторий бэкенда](https://github.com/imterana/MVBackend)

### Сброрка и запуск

    $ docker-compose up --build
    
#Авторизация

1) [Создать github приложение](https://github.com/settings/applications/new)  
Homepage URL: `localhost`  
Authorization callback URL: `http://localhost/accounts/github/login/callback`

2) Создать суперпользователя в django

       $ docker exec -it mvbackend_gunicorn_1 python3 manage.py createsuperuser

3) Добавить github приложение в [django админке](localhost/admin)  
SOCIAL ACCOUNTS -> Social applications -> Add  
Client id и Secret Key взять из приложения на github

4) [Браво, Вы великолепны!](http://localhost/accounts/github/login)