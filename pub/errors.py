import cgi
from .utils import annot_url

class MarkupError:

    """base class for markup errors

    these are not derived from Exception because they are not errors to be 
    caught in code
    """

    def __init__(self, msg, annotation_id=None):
        self.msg = msg
        self.annotation_id = annotation_id
        return

    def render(self):
        if self.annotation_id:
            fmt = '<a href="%s">%s</a>'
            return fmt % (annot_url(self.annotation_id), cgi.escape(self.msg))
        else:
            return cgi.escape(self.msg)

class LinkError(MarkupError):

    """inter-entity link error"""

class UnknownFieldError(MarkupError):

    """unknown field in entity definition"""

    def __init__(self, name, annot_id):
        MarkupError.__init__(self, 'Unknown field %s' % name, annot_id)
        return

class MissingOrUnknownTypeError(MarkupError):

    """missing or unknown entity type"""

    def __init__(self, name, annot_id):
        MarkupError.__init__(self, 'Missing or unknown entity type' , annot_id)
        return

class BadFieldDefinitionError(MarkupError):

    """bad field definition line"""

    def __init__(self, annot_id):
        MarkupError.__init__(self, 'Bad field definition', annot_id)
        return

class DuplicateIDError(MarkupError):

    """duplicate entity ID"""

    def __init__(self, id, annot_id):
        MarkupError.__init__(self, 'Duplicate ID %s' % id, annot_id)
        return

class MissingIDError(MarkupError):

    """missing entity ID"""

    def __init__(self, annot_id):
        MarkupError.__init__(self, 'No ID given', annot_id)
        return

class UnknownIDError(MarkupError):

    """unknown entity ID in extension"""

    def __init__(self, id, annot_id):
        MarkupError.__init__(self, 'Unknown ID %s' % id, annot_id)
        return

# eof
