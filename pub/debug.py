import os

if not 'CSPUB_DEBUG' in os.environ:
    _debug_flag = False
elif not 'CSPUB_DEBUG' in os.environ:
    _debug_flag = False
else:
    _debug_flag = True

def debug(message):
    if _debug_flag:
        print(message)
    return

def set_debug(val):
    global _debug_flag
    _debug_flag = bool(val)
    return

# eof
