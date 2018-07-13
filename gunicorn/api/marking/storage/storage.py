import redis

settings = {'port': 6379,
            'host': 'redis'}


class ConnectionPool(object):
    """
    Singleton class for redis connection pool.
    """

    __connection_pool = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if ConnectionPool.__connection_pool is None:
            ConnectionPool.__connection_pool = redis.ConnectionPool(host=settings['host'], port=settings['port'])
        return ConnectionPool.__connection_pool


def add_to_list(listname, value):
    """
    Insert a value at the list.
    If a list with name listname does not exist, the new empty list is created before.
    :param listname: name of the list
    :param value: a value to insert
    :return:
    """

    r = redis.Redis(connection_pool=ConnectionPool())
    r.rpush(listname, value)


def get_list(listname):
    """
    Returns all the elements of the list.
    :param listname: name of the list
    :return: list with all the elements of requested list
    """

    r = redis.Redis(connection_pool=ConnectionPool())
    return r.lrange(listname, 0, r.llen(listname))


def remove_from_list(listname, value):
    """
    Removes an element from the list.
    :param listname: name of the list
    :param value: a value to remove
    :return: number of removed elements
    """

    r = redis.Redis(connection_pool=ConnectionPool())
    return r.lrem(listname, value, 0)
