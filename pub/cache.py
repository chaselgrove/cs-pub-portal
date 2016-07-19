import os
import bsddb
from .debug import debug

if not os.environ.has_key('CSPUB_CACHE'):
    _cache = None
else:
    _cache = os.environ['CSPUB_CACHE']

def set_cache(cache):
    global _cache
    _cache = cache
    return

class Cache:

    # cache object (persistent cache dictionary)
    #
    # if CSPUB_CACHE is not set or if there is an error opening it, 
    # gets will act as if the cache is empty (KeyError is always raised), and 
    # sets will appear to succeed
    #
    # c = Cache()
    # print c[key1]
    # c[key2] = value
    # c.close()
    #
    # can also be used as a context manager:
    # with Cache() as c:
    #     print c[key1]
    #     c[key2] = value

    def __init__(self):
        if not _cache:
            debug('no cache')
            self.db = None
            self.is_open = False
            return
        try:
            self.db = bsddb.hashopen(_cache)
            self.is_open = True
            debug('cache open: %s' % _cache)
        except:
            debug('error opening cache: %s' % _cache)
            self.db = None
            self.is_open = False
        return

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()
        return False

    def __getitem__(self, key):
        if self.db is None:
            raise KeyError(key)
        return self.db[key]

    def __setitem__(self, key, value):
        if self.is_open:
            self.db[key] = value
        return

    def close(self):
        if self.is_open:
            self.db.close()
        return

# eof
