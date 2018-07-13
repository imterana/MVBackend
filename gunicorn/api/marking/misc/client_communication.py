class ErrorMessages:
    """
    Error messages to display to a user.
    """

    NO_EVENT = "Выбери пару"
    NO_MESSAGE = "Нет сообщения"
    INVALID_EVENT = "Кажеся, пары не существует"
    NOT_RUNNING_EVENT = "Сейчас эта пара не идет"
    PAST_EVENT = "Пара уже закончилась"
    NOT_PERMITTED = "Нельзя так!"
    ALREADY_HAVE_USER = "Ты уже выбрал пользователя"
    USER_ALREADY_CHOSEN = "Его уже отмечают"


class EncouragingMessages:
    """
    Messages to display to a user when he/she marks somebody.
    """

    general_delta = 50
    general = ["Ты такой молодец, я не могу! ^_^' +{} к карме!".format(general_delta),
               "Круто! +{} к карме!".format(general_delta),
               "Огонь! +{} к карме!".format(general_delta),
               "От души! +{} к карме!".format(general_delta)]
    double_combo = []
    triple_combo = []
    great = []


class ClientMessages:
    """
    API messages for communication with websocket client.
    """

    MARKED = "marked"
    WAS_MARKED = "was_marked"
    MARKING_LIST = "marking_list"
    PREPARED = "prepared"
    REFUSED = "refused"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"


class ClientResponse:
    """
    API responses for communication with websocket client.
    """

    @staticmethod
    def response_ok(message, params=None):
        response = {"result": "ok", "message": message}
        if params:
            response["params"] = params
        return response

    @staticmethod
    def response_error(message):
        return {"result": "error", "message": message}
