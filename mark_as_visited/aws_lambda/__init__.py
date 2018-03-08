lambda_functions = {}


def lambda_function(name):
    def lambda_function_wrapper(function):
        lambda_functions[name] = function
        return function
    return lambda_function_wrapper


@lambda_function('/')
def hello(event, context):
    return "Hi!"
