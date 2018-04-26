from time import sleep

import psycopg2

from backend.settings import DATABASES


def connect_to(db_dict):
    assert(db_dict['ENGINE'] == 'django.db.backends.postgresql_psycopg2')
    kwargs = {
            'dbname': db_dict['NAME'],
            'user': db_dict['USER'],
            'password': db_dict['PASSWORD'],
            'host': db_dict['HOST'],
    }
    if db_dict['PORT']:
        kwargs['port'] = db_dict['PORT']
    conn = psycopg2.connect(**kwargs)
    conn.close()


if __name__ == '__main__':
    for db_name in DATABASES:
        while True:
            try:
                connect_to(DATABASES[db_name])
                break
            except psycopg2.OperationalError as e:
                print(e)
                sleep(1)
