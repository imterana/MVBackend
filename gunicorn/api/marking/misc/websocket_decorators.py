def require_group_message_param(required):
    """
    Decorator for group messages.
    Checks requests parameters for presence, retrieves params from message.
    :param required: list with required parameters
    :return:
    """

    def decorator(func):
        def wrapper(self, event):
            print(event)
            params = event.get('params')
            if params is None:
                return

            for param in required:
                if param not in params:
                    return
            return func(self, params)

        return wrapper

    return decorator


def require_client_message_param(required):
    """
    Decorator for client messages.
    Checks requests parameters for presence, sends error if not present.
    :param required: list with required parameters
    :return:
    """

    def decorator(func):
        def wrapper(self, params):

            for param in required:
                if param not in params:
                    self.send_json({"result": "error", "error_msg": "{} is missing".format(param)})
                    return
            return func(self, params)

        return wrapper

    return decorator


def ignore_myself(func):
    """
        Decorator for group messages.
        Checks if sender is current consumer and ignores the message in that case.
        :param
        :return:
        """

    def wrapper(self, params):
        sender = params['sender']
        if sender == self.channel_name:
            return
        return func(self, params)

    return wrapper
