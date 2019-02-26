import configparser

_config = None

def set_config(fname):
    global _config
    _config = fname
    return

class Config(configparser.ConfigParser):

    def __init__(self):
        configparser.ConfigParser.__init__(self)
        self.read(_config)
        return

# eof
