"""
Preprocessing request POST OR GET parameters decorators
"""

from .response import (
    APIMissingArgumentResponse,
    APIInvalidArgumentResponse,
    APIUnsupportedMediaTypeResponse,
    APINotPermittedResponse
)


def require_files(required):
    """
    Decorator for views with file uploads.
    Checks requests parameters for presence.
    :param required: list with required files
    :return:
    """

    def decorator(func):
        def wrapper(request):
            request_files = request.FILES
            for file in required:
                if file not in request_files:
                    return APIMissingArgumentResponse(error_msg=file)
            return func(request)

        return wrapper

    return decorator


def require_arguments(required):
    """
    Decorator for views with GET or POST requests.
    Checks requests parameters for presence.
    :param required: list with required parameters
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
                except (ValueError, TypeError) as e:
                    return APIInvalidArgumentResponse(error_msg=str(e))
            setattr(request, request.method, request_params)
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


def require_content_type(required_type):
    """
    Decorator for views with GET or POST requests that require certain content type.
    Performs overwriting equest.GET or request.POST dictionaries with parsed content.
    :param required_type: expected content type
    :return:
    """

    def decorator(func):
        def wrapper(request):
            if not hasattr(request, required_type):
                return APIUnsupportedMediaTypeResponse(error_msg="{} content expected".format(required_type))
            if request.method == 'GET':
                request.GET = getattr(request, required_type)
            elif request.method == 'POST':
                request.POST = getattr(request, required_type)
            else:
                return APINotPermittedResponse(error_msg="Not permitted request type")
            return func(request)

        return wrapper

    return decorator
