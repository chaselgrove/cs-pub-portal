import os

if not os.environ.has_key('CSPUB_DEBUG'):
    _debug_flag = False
elif not os.environ['CSPUB_DEBUG']:
    _debug_flag = False
else:
    _debug_flag = True

def debug(message):
    if _debug_flag:
        print message
    return

def set_debug(val):
    global _debug_flag
    _debug_flag = bool(val)
    return

# eof
