import re
import httplib
import urllib
import json

from .entities import *
from .exceptions import *

pmid_re = re.compile('^\d+$')

class Publication:

    def __init__(self, pmid):
        if not pmid_re.search(pmid):
            raise ValueError('bad PMID')
        self.pmid = pmid
        self.title = None
        self.pmc_id = None
        self.errors = []
        self.entities = {}
        for et in entities:
            self.entities[et] = {}
        self._read_pubmed()
        self._read_annotations()
        for ed in self.entities.itervalues():
            for ent in ed.itervalues():
                ent.set_related()
        for ed in self.entities.itervalues():
            for ent in ed.itervalues():
                ent.check()
                ent.add_links()
        return

    def score(self):
        s = 0
        max = 0
        for ed in self.entities.itervalues():
            for ent in ed.itervalues():
                (es, emax) = ent.score()
                s += es
                max += emax
        return (s, max)

    def _read_pubmed(self):

        """get the pubmed entry

        raises PublicationNotFoundError if the pubmed record is not found
        """

        conn = httplib.HTTPSConnection('www.ncbi.nlm.nih.gov')
        params = {'term': self.pmid, 'report': 'medline', 'format': 'text'}
        url = '/pubmed/?%s' % urllib.urlencode(params)
        conn.request('GET', url)
        response = conn.getresponse()
        if response.status != 200:
            msg = 'PubMed Central response status %d' % response.status
            raise PubMedError(msg)
        data = response.read()
        conn.close()

        field = None
        value = None
        for line in data.split('\n'):
            if not line.startswith(' ') and '-' in line:
                if value:
                    if field == 'TI':
                        self.title = value
                    if field == 'PMC':
                        self.pmc_id = value
                (field, value) = [ el.strip() for el in line.split('-', 1) ]
            elif field:
                value = '%s %s' % (value, line.strip())
        if value:
            if field == 'TI':
                self.title = value
            if field == 'PMC':
                self.pmc_id = value
        if not self.title or not self.pmc_id:
            raise PublicationNotFoundError(self.pmid)
        return

    def _read_annotations(self):

        """reads annotations from a PubMed Central manuscript

        returns a dictionary d such that:

            d[entity type][entity id] = list of (annotation ID, name, value) 
                                        tuples

        generates errors for:

            missing or unknown entity types

            missing entity IDs

            duplicate entity IDs

            unknown entity +IDs

            bad "name: value" lines
        """

        url_fmt = 'http://www.ncbi.nlm.nih.gov/pmc/articles/%s'
        url = url_fmt % self.pmc_id

        conn = httplib.HTTPSConnection('hypothes.is')
        url = '/api/search?%s' % urllib.urlencode({'uri': url})
        conn.request('GET', url, '', {'Accept': 'application/json'})
        response = conn.getresponse()
        if response.status != 200:
            msg = 'hypothes.is response status %d' % response.status
            raise HypothesisError(msg)
        data = response.read()
        obj = json.loads(data)
        conn.close()

        # first pass: through the annotations to generate a dictionary d0 
        # where d0[entity type] = list of (annotation ID, list of lines) tuples

        # generates missing or unknown entity type errors

        d0 = {}

        for annot in obj['rows']:
            if 'CANDISharePub' not in annot['tags']:
                continue
            for et in entities:
                if et in annot['tags']:
                    entity_type = et
                    break
            else:
                self.errors.append(MissingOrUnknownTypeError(annot['id']))
                continue
            block_lines = []
            for line in annot['text'].split('\n'):
                line = line.strip()
                if line:
                    if line not in ('<pre>', '</pre>'):
                        block_lines.append(line)
                else:
                    if block_lines:
                        d0.setdefault(entity_type, [])
                        d0[entity_type].append((annot['id'], block_lines))
                        block_lines = []
            if block_lines:
                d0.setdefault(entity_type, [])
                d0[entity_type].append((annot['id'], block_lines))

        # second pass: through the annotation blocks to generate two 
        # dictionaries, d_base and d_plus, where 
        # d_*[entity type][entity id] = list of (annotation ID, name, value) 
        # tuples

        # generates: missing ID errors
        #            duplicate ID errors
        #            bad "name: value" line

        d_base = {}
        d_plus = {}

        for entity_type in d0:
            for (annot_id, block) in d0[entity_type]:
                id = None
                plus_id = None
                fields = []
                for line in block:
                    try:
                        (name, value) = line.split(':', 1)
                    except ValueError:
                        err = BadFieldDefinitionError(annot_id)
                        self.errors.append(err)
                        continue
                    name = name.strip().lower()
                    value = value.strip()
                    if name == 'id':
                        id = value
                    elif name == '+id':
                        plus_id = value
                    else:
                        fields.append((annot_id, name, value))
                if id:
                    d_base.setdefault(entity_type, {})
                    if id in d_base[entity_type]:
                        err = DuplicateIDError(id, annot_id)
                        self.errors.append(err)
                    else:
                        d_base[entity_type][id] = fields
                elif plus_id:
                    d_plus.setdefault(entity_type, {})
                    d_plus[entity_type][plus_id] = fields
                else:
                    self.errors.append(MissingIDError(annot_id))

        # third pass: move d_plus entires into d_base

        # generates: unknown ID errors

        for entity_type in d_plus:
            for entity_id in d_plus[entity_type]:
                try:
                    base = d_base[entity_type][entity_id]
                except KeyError:
                    annot_id = d_plus[entity_type][entity_id][0][0]
                    err = UnknownIDError(entity_id, annot_id)
                    self.errors.append(err, annot_id)
                else:
                    base.extend(d_plus[entity_type][entity_id])

        # now create entity objects from the definition blocks

        for entity_type in d_base:
            for entity_id in d_base[entity_type]:
                cls = entities[entity_type]
                ent = cls(self, entity_id, d_base[entity_type][entity_id])
                self.entities[entity_type][ent.id] = ent

        return

# eof
