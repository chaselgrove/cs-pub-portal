import cgi
from .utils import annot_url

class BaseMarkupError:

    """base class for markup errors

    these are not derived from Exception because they are not errors to be 
    caught in code
    """

class BaseAnnotationError(BaseMarkupError):

    """errors not associated with entities (but we keep track of 
    the annotations they come from)
    """

    def __init__(self, annotation_id):
        self.annotation_id = annotation_id
        return

    def render(self):
        fmt = '<a href="%s">%s</a>'
        return fmt % (annot_url(self.annotation_id), cgi.escape(self.msg))

class MissingOrUnknownTypeError(BaseAnnotationError):

    """missing or unknown entity type"""

    def __init__(self, annot_id):
        BaseAnnotationError.__init__(self, annot_id)
        self.data = None
        self.msg = 'Missing or unknown entity type'
        return

class BadFieldDefinitionError(BaseAnnotationError):

    """bad field definition line"""

    def __init__(self, annot_id):
        BaseAnnotationError.__init__(self, annot_id)
        self.data = None
        self.msg = 'Bad field definition'
        return

class DuplicateIDError(BaseAnnotationError):

    """duplicate entity ID"""

    def __init__(self, annot_id, id):
        BaseAnnotationError.__init__(self, annot_id)
        self.data = id
        self.msg = 'Duplicate ID %s' % id
        return

class MissingIDError(BaseAnnotationError):

    """missing entity ID"""

    def __init__(self, annot_id):
        BaseAnnotationError.__init__(self, annot_id)
        self.data = None
        self.msg = 'No ID given'
        return

class UnknownIDError(BaseAnnotationError):

    """unknown entity ID in extension"""

    def __init__(self, annot_id, id):
        BaseAnnotationError.__init__(self, annot_id)
        self.data = id
        self.msg = 'Unknown ID %s' % id
        return

class BaseEntityError(BaseMarkupError):

    """errors associated with entities

    annotations are usually lost by the time we create entities, so we don't 
    have annotation IDs to keep track of here
    """

    def __init__(self):
        return

    def render(self):
        return cgi.escape(self.msg)

class LinkError(BaseEntityError):

    """inter-entity link error"""

    def __init__(self, msg):
        BaseEntityError.__init__(self)
        self.data = None
        self.msg = msg
        return

class UnknownFieldError(BaseEntityError):

    """unknown field in entity definition"""

    def __init__(self, name):
        BaseEntityError.__init__(self)
        self.data = name
        self.msg = 'Unknown field "%s"' % name
        return

# eof
