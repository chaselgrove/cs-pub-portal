import psycopg2
from . import config

def connect():
    c = config.Config()
    db = psycopg2.connect(host=c.get('db', 'host'), 
                          dbname=c.get('db', 'database'), 
                          user=c.get('db', 'user'), 
                          password=c.get('db', 'password'))
    return db

# eof
