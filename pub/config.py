import ConfigParser

_config = None

def set_config(fname):
    global _config
    _config = fname
    return

class Config(ConfigParser.ConfigParser):

    def __init__(self):
        ConfigParser.ConfigParser.__init__(self)
        self.read(_config)
        return

# eof
