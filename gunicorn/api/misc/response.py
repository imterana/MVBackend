from django.http import JsonResponse


class ResponseCode:
    """
    An enumerator for various status codes of API.
    """
    RESPONSE_OK = 0
    RESPONSE_INVALID_ARGUMENT = 1
    RESPONSE_MISSING_ARGUMENT = 2
    RESPONSE_NOT_PERMITTED = 3
    RESPONSE_UNKNOWN_ERROR = -1
    RESPONSE_UNSUPPORTED_MEDIA_TYPE = 4


class APIResponse(JsonResponse):
    """
    An HTTP response class for backend api responses.

    :param error: Error code of the response. Defaults to RESPONSE_OK.
    :param error_msg: String description of the error. Defaults to empty string.
    :param response: A value to be send as "response" field. If not present,
      field "response" is not present in the JSON.
    """
    response_code = ResponseCode.RESPONSE_OK

    def __init__(self, error=None,
                 error_msg="", response=None, **kwargs):
        if error is None:
            error = self.response_code

        data = {
            "error": int(error),
            "error_msg": str(error_msg),
        }

        if response is not None:
            data["response"] = response

        super().__init__(data, safe=False, **kwargs)


class APIInvalidArgumentResponse(APIResponse):
    """
    An API response class to return when one of the arguments is of the
    wrong type or in invalid range.
    """
    response_code = ResponseCode.RESPONSE_INVALID_ARGUMENT


class APIMissingArgumentResponse(APIResponse):
    """
    An API response class to return when one of the arguments is missing.
    """
    response_code = ResponseCode.RESPONSE_MISSING_ARGUMENT


class APINotPermittedResponse(APIResponse):
    """
    An API response class to return when action attempted is not permitted.
    """
    response_code = ResponseCode.RESPONSE_NOT_PERMITTED


class APIUnsupportedMediaTypeResponse(APIResponse):
    """
    An API response class to return when content-type is unsupported.
    """
    response_code = ResponseCode.RESPONSE_UNSUPPORTED_MEDIA_TYPE


class APIUnknownErrorResponse(APIResponse):
    """
    An API response class to return when error does not fit any other category.
    """
    response_code = ResponseCode.RESPONSE_UNKNOWN_ERROR
