class PubError(Exception):

    """base class for exceptions"""

class PubMedError(PubError):

    """error in PubMed Central request/response"""

class PublicationNotFoundError(PubError):

    """publication not found"""

    def __init__(self, id_type, id):
        self.id_type = id_type
        self.id = id
        return

    def __str__(self):
        return '%s %s not found' % (self.id_type, self.id)

class HypothesisError(PubError):

    """error in hypothes.is call"""

# eof
