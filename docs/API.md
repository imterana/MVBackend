# Общий вид ответа от API
```
{
    "error": код ошибки,
    "error_msg": сообщение ошибки,
    "response": словарь с результатом
}
```

Далее во всех функциях в пункте "Возвращаемое значение" будет описываться только вид `"response"`.

# Auth

## Logout

Делает log out текущего пользователя

### URL

`POST /accounts/logout/`

### Входные параметры

N/A

### Возвращаемое значение

N/A

## GetCurrentUserId

Возвращает id текущего пользователя.

### URL

`GET /api/auth/GetCurrentUserId`

### Входные параметры

N/A

### Возвращаемое значение

`user_id` - id пользователя

# Profile

## GetProfile

Получает профиль произвольного пользователя.

### URL

`GET /api/profile/GetProfile`

### Входные параметры

`user_id` - id требуемого пользователя

### Возвращаемое значение

`pic` - url аватарки пользователя  
`display_name` - имя пользователя  
`confirmed` - `true/false`, в зависимости от статуса подтверждения пользователя  
`bio` - группа/факультет/вуз пользователя  
`karma` - рейтинг пользователя

## UpdateProfilePicture

Обновляет картинку авторизованного пользователя.

### URL

`POST /api/profile/UpdateProfilePicture`

### Входные параметры

`image` - файл с картинкой
`name` - имя файла с расширением

### Возвращаемое значение

N/A

## UpdateProfileInfo

Обновляет данные авторизованного пользователя.

### URL

`POST /api/profile/UpdateProfileInfo`

### Входные параметры

Достаточно одного из следующих параметров:

`display_name` - новое имя пользователя

`bio` - новое био пользователя

### Возвращаемое значение

N/A

## UploadProfileConfirmation

Добавляет новый скан зачетки. Если уже имеется, то заменяет старый (с потерей галочки).

### URL

`POST /api/profile/UploadProfileConfirmation`

### Входные параметры

`image` - файл с картинкой

### Возвращаемое значение

N/A

## FindByName

Ищет пользователей по части имени.

### URL

`GET /api/profile/FindByName`

### Входные параметры

`display_name_part` - часть имени (не менее 4 символов)

### Возвращаемые значения

`users` - массив пользователей в следующем формате:

* `user_id` - id пользователя
* `display_name` - имя пользователя

# Friends

## GetFriendList

Получить список друзей авторизованного пользователя.

### URL

`GET /api/friends/GetFriendList`

### Входные параметры

N/A

### Возвращаемое значение

`friends` - список профилей друзей, в следующем формате:

* `user_id` - id пользователя
* `display_name` - имя пользователя
* `pending` - `true`, если приглашение отправлено авторизованным пользователем, но еще не принято

## SendFriendRequest

Отправляет запрос в друзья пользователю.

### URL

`POST /api/friends/SendFriendRequest`

### Принимаемые параметры

`user_id` - id приглашаемого пользователя

### Возвращаемые значения

N/A

## GetFriendRequests

### URL

`GET /api/friends/GetFriendRequests`

### Принимаемые параметры

N/A

### Возвращаемые значения

`requests` - список `user_id` пользователей, отправивших запрос

## RemoveFriend

### URL

`POST /api/friends/RemoveFriend`

Отменяет отправленное приглашение или удаляет из списка друзей

### Принимаемые параметры

`user_id` - id пользователя, которого надо убрать из друзей

### Возвращаемое значение

N/A

# Events

## CreateEvent

### URL

`POST /api/events/CreateEvent`

### Принимаемые параметры

`name` - Названия события, должно быть уникально

`time_to` - Время начала, UNIX timestamp (sec)

`time_from` - Время конца, UNIX timestamp (sec)

### Возвращаемое значение

`event_id` - UUID созданного события

## GetEventByID

### URL

`GET /api/events/GetEventByID`

### Принимаемые параметры

`event_id`

### Возвращаемое значение

`name` - Имя события  

`event_id` - UUID события

`time_to` - Время начала, UNIX timestamp (sec)

`time_from` - Время конца, UNIX timestamp (sec)

`creator_id` - ID создателя события

## GetEvents

Поиск событий.

### URL

`GET /api/events/GetEvents`

### Принимаемые параметры

`name` - опциональный параметр, подстрока, которую надо найти в названии потока (без учета регистра), длиной не менее 3 символов. Если отсутствует, будут возвращены все события.

### Возвращаемое значение

Массив событий следующего вида:  

`name` - Имя события  

`event_id` - UUID события

`time_to` - Время начала, UNIX timestamp (sec)

`time_from` - Время конца, UNIX timestamp (sec)

`creator_id` - ID создателя события

## JoinEvent

Присоединиться к событию.

### URL

`POST /api/events/JoinEvent`

### Принимаемые параметры:

`event_id` - UUID события

### Возвращаемые параметры:

N/A

## LeaveEvent

### URL

`POST /api/events/LeaveEvent`

### Принимаемые параметры:

`event_id` - UUID события

### Возвращаемые параметры:

N/A

## DeleteEvent

### URL

`POST /api/events/DeleteEvent`

### Принимаемые параметры:

`event_id` - UUID события

### Возвращаемые параметры:

N/A

## GetCreatedEvents

### URL

`GET /api/events/GetCreatedEvents`

### Принимаемые параметры

N/A

### Возвращаемое значение

Список событий, созданных пользователем (он не обязательно в них состоит), в формате:  
`name`: Название события  
`event_id`: UUID события  

## GetJoinedEvents

### URL

`GET /api/events/GetJoinedEvents`

### Принимаемые параметры

N/A

### Возвращаемое значение

Список событий, в которых пользователь состоит, в формате:  
`name`: Название события  
`event_id`: UUID события  
`creator`: `true`, если событие было создано отправителем запроса

# Marking

Общий вид запроса:

*Client -> Server:* `{"message": "some_msg", "params": {"param":"value"...}}`

Общий вид ответа:

`{"result": "ok", "message": "some action", ["params": {"param": "value"}]}`
 
`{"result": "error", "message": "some description"}` 

## MarkMe

### Установка соединения

`/ws/mark_me?event_id=1234`

### Ответ
N/A в случае успешного соединения

### Уведомление об отметке и закрытие сокета

*Server -> Client:* `{"result": "ok", "message": "was_marked",
                      "params": {'user_id': 1234}}`
                      
user_id - Id отметившего пользователя
## ReadyToMark

### Установка соединения

`/ws/marking?event_id=1234`

### Ответ
Список людей, которых можно отметить

*Server -> Client:* `{"result": "ok", "message": 'marking_list', 
                    "params": {"marking_list": [user_id1, user_id2...]}}`


### Обновление о новом пользователе в списке отмечаемых
*Server -> Client:* `{"result": "ok", 'message': 'user_joined',
			        "params": {'user_id': 1234}}`
			        
### Обновление об исключении пользователя из списка отмечамых
 
*Server -> Client:* `{"result": "ok", 'message': 'user_left',
		            "params": {'user_id': 1234}`
		                     
### Выбор пользователя для отметки

*Client -> Server:* `{'message': 'prepare_to_mark',
			          "params": {'user_id': 1234}`   
			          
  
### Подтверждение отметки

*Client -> Server:* `{'message': 'confirm_marking'}`	 
			         
*Server -> Client:* `{'result': 'ok', "message": "marked", 
"params": {"display_msg": "some message to show to the user"}`
       

### Отказ отмечать

*Client -> Server:* `{'message': 'refuse_to_mark'}`

