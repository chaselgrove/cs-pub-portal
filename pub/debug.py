import os

def debug(message):
    if not os.environ.has_key('CSPUB_DEBUG'):
        return
    if not os.environ['CSPUB_DEBUG']:
        return
    print message
    return

# eof
