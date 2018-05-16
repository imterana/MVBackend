from calendar import timegm
from datetime import datetime


def datetime_from_string(string):
    return datetime.utcfromtimestamp(int(string))


def datetime_to_string(dt):
    return str(timegm(dt.timetuple()))