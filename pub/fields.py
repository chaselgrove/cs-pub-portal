class BaseField:

    """base class for fields"""

    def __init__(self, display_name):
        self.display_name = display_name
        self.reset()
        return

    def reset(self):
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

class URLField(Field):

    """URL"""

    def render_value(self):
        if self.value is None:
            return ''
        return '<a href="%s">%s</a>' % (self.value, self.value)

class DOIField(Field):

    """DOI"""

    def render_value(self):
        if self.value is None:
            return ''
        fmt = '<a href="http://dx.doi.org/%s">%s</a>'
        return fmt % (self.value, self.value)

class NITRCIDField(Field):

    """NITRC ID"""

    def render_value(self):
        if self.value is None:
            return ''
        fmt = '<a href="http://www.nitrc.org/projects/%s">%s</a>'
        return fmt % (self.value, self.value)

class RRIDField(Field):

    """RRID"""

    def render_value(self):
        if self.value is None:
            return ''
        fmt = '<a href="https://scicrunch.org/resolver/%s">%s</a>'
        return fmt % (self.value, self.value)

class MultiField(BaseField):

    """basic field with multiple unique values"""

    def __init__(self, display_name):
        BaseField.__init__(self, display_name)
        return

    def set(self, value):
        if not self.value:
            self.value = []
        if value not in self.value:
            self.value.append(value)
        return

    def render_value(self):
        if self.value is None:
            return ''
        return ', '.join(self.value)

# eof
