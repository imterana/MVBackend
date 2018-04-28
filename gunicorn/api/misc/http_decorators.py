"""
Preprocessing request POST OR GET parameters decorators
"""

from .response import APIMissingArgumentResponse


def require_arguments(required):
    """
    Decorator for views with GET or POST requests.
    Checks requests parameters for presense.
    :param required: list with required parameteres
    :return:
    """
    def decorator(func):
        def wrapper(request):
            request_params = get_dict_from_request(request)
            for param in required:
                if param not in request_params:
                    return APIMissingArgumentResponse(error_msg=param)
            return func(request)
        return wrapper
    return decorator


def cast_arguments(cast_dict):
    """
    Decorator for views with GET or POST requests.
    Performs casting request parameters before calling a view.
    :param cast_dict: param_name in request -> cast function
    :return:
    """
    def decorator(func):
        def wrapper(request):
            request_params = get_dict_from_request(request)
            request_params = request_params.copy()
            for param in cast_dict:
                if param not in request_params:
                    continue
                try:
                    request_params[param] = cast_dict[param](
                                                request_params[param])
                except ValueError:
                    return APIInvalidArgumentResponse(error_msg=str(ValueError))
            request.GET = request_params
            return func(request)
        return wrapper
    return decorator


def get_dict_from_request(request):
    """
    Returns request.GET or request.POST
    :param request: GET or POST request
    :return: request.GET or request.POST or raises NotImplemented
    """
    if request.method == 'GET':
        return request.GET
    elif request.method == 'POST':
        return request.POST
    else:
        raise NotImplemented
