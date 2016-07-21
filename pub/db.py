import psycopg2
from . import config

class DB:

    def __init__(self):
        c = config.Config()
        self._db = psycopg2.connect(host=c.get('db', 'host'), 
                                    dbname=c.get('db', 'database'), 
                                    user=c.get('db', 'user'), 
                                    password=c.get('db', 'password'))
        return

    def close(self):
        self._db.close()
        return

# eof
