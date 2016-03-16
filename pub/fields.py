class BaseField:

    """base class for fields"""

    def __init__(self, display_name):
        self.display_name = display_name
        self.value = None
        return

    def render_value(self):
        if self.value is None:
            return ''
        return self.value

class Field(BaseField):

    """basic field"""

    def set(self, value):
        self.value = value
        return

class MultiField(BaseField):

    """basic field with multiple values"""

    def __init__(self, display_name):
        BaseField.__init__(self, display_name)
        self.value = None
        return

    def set(self, value):
        if not self.value:
            self.value = []
        self.value.append(value)
        return

    def render_value(self):
        if self.value is None:
            return self.value
        return ', '.join(self.value)

# eof
