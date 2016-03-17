class PubError(Exception):

    """base class for exceptions"""

class PubMedError(PubError):

    """error in PubMed Central request/response"""

class PublicationNotFoundError(PubError):

    """publication not found"""

    def __init__(self, pmid):
        self.pmid = pmid
        return

    def __str__(self):
        return 'no title or PMC ID found for PMID %s' % self.pmid

class HypothesisError(PubError):

    """error in hypothes.is call"""

# eof
