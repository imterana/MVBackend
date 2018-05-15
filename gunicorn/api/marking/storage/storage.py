import redis

settings = {'port': 6379,
            'host': 'redis'}


class ConnectionPool(object):
    __connection_pool = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if ConnectionPool.__connection_pool is None:
            ConnectionPool.__connection_pool = redis.ConnectionPool(host=settings['host'], port=settings['port'])
        return ConnectionPool.__connection_pool


def add_to_list(listname, value):
    r = redis.Redis(connection_pool=ConnectionPool())
    r.rpush(listname, value)


def get_list(listname):
    r = redis.Redis(connection_pool=ConnectionPool())
    return r.lrange(listname, 0, r.llen(listname))
