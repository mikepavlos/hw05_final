# Проект Yatube

### Описание проекта:

Проект дневника для блогеров, предоставляющий возможности:
- создание постов, 
- разделение их в определенные группы, 
- добавление изображений, 
- комментариев на отдельные посты, 
- подписки на авторов постов.

В проекте использована система регистрации пользователей, их аутентификация, 
изменение и восстановление пароля.

### Задействованные технологии:

- Python 3.7
- Django 2.2.16
- SQL
- HTML5
- Bootstrap 5

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/mikepavlos/hw05_final.git
```

```
cd hw05_final
```

Создать и активировать виртуальное окружение:

```
python -m venv env
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
python manage.py runserver
```

Дневник предоставляет возможность незарегистрированным пользователям 
просматривать посты, комментарии к ним, группы и подробную информацию каждого поста.  
Для создания постов, оставления комментариев, подписки на авторов необходима 
регистрация и авторизация.

### Автор проекта:

Михаил Павлов <pavlovichmihaylovich@yandex.ru>, telegram @miha1is

