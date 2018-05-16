def require_group_message_param(required):
    """
    Decorator for group messages.
    Checks requests parameters for presence, retrieves params from message.
    :param required: list with required files
    :return:
    """

    def decorator(func):
        def wrapper(self, event):
            print(event)
            params = event.get('params')
            if params is None:
                print("params is none")
                return

            for param in required:
                if param not in params:
                    print(param, "not in", params)
                    return
            return func(self, params)

        return wrapper

    return decorator


def require_client_message_param(required):
    """
    Decorator for group messages.
    Checks requests parameters for presence, retrieves params from message.
    :param required: list with required files
    :return:
    """

    def decorator(func):
        def wrapper(self, params):

            for param in required:
                if param not in params:
                    self.send_json({"error": "{} is missing".format(param)})
                    return
            return func(self, params)

        return wrapper

    return decorator
