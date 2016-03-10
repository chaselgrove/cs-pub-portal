import json
import httplib
import urllib

class MarkupError:

    """exception for parse or markup errors"""

    def __init__(self, msg):
        self.msg = msg
        return

    def __str__(self):
        return 'Markup error: %s' % self.msg

class Entity:

    """base class for entities"""

    def __init__(self, fields, ident):
        self.errors = []
        if 'id' not in fields:
            self.errors.append(MarkupError('no ID given %s' % ident))
            self.id = None
        else:
            self.id = fields['id'][0]
        return

class SubjectGroup(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'diagnosis' in fields:
            self.diagnosis = fields['diagnosis'][0]
        else:
            self.diagnosis = None
        if 'nsubjects' in fields:
            self.n_subjects = fields['nsubjects'][0]
        else:
            self.n_subjects = None
        if 'agemean' in fields:
            self.age_mean = fields['agemean'][0]
        else:
            self.age_mean = None
        if 'agesd' in fields:
            self.age_sd = fields['agesd'][0]
        else:
            self.age_sd = None
        return

class AcquisitionInstrument(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'type' in fields:
            self.type = fields['type'][0]
        else:
            self.type = None
        if 'location' in fields:
            self.location = fields['location'][0]
        else:
            self.location = None
        if 'field' in fields:
            self.field = fields['field'][0]
        else:
            self.field = None
        if 'manufacturer' in fields:
            self.manufacturer = fields['manufacturer'][0]
        else:
            self.manufacturer = None
        if 'model' in fields:
            self.model = fields['model'][0]
        else:
            self.model = None
        return

class Acquisition(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'type' in fields:
            self.type = fields['type'][0]
        else:
            self.type = None
        if 'acquisitioninstrument' in fields:
            self.acquisitioninstrument = fields['acquisitioninstrument'][0]
        else:
            self.acquisitioninstrument = None
        return

class Data(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'url' in fields:
            self.url = fields['url'][0]
        else:
            self.url = None
        if 'doi' in fields:
            self.doi = fields['doi'][0]
        else:
            self.doi = None
        if 'acquisition' in fields:
            self.acquisition = fields['acquisition'][0]
        else:
            self.acquisition = None
        if 'subjectgroup' in fields:
            self.subjectgroup = fields['subjectgroup'][0]
        else:
            self.subjectgroup = None
        return

class AnalysisWorkflow(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'method' in fields:
            self.method = fields['method']
        else:
            self.method = None
        if 'methodurl' in fields:
            self.methodurl = fields['methodurl']
        else:
            self.methodurl = None
        if 'software' in fields:
            self.software = fields['software']
        else:
            self.software = None
        return

class Observation(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'data' in fields:
            self.data = fields['data']
        else:
            self.data = None
        if 'analysisworkflow' in fields:
            self.analysisworkflow = fields['analysisworkflow'][0]
        else:
            self.analysisworkflow = None
        if 'meausure' in fields:
            self.meausure = fields['meausure'][0]
        else:
            self.meausure = None
        return

class Model(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'Variable' in fields:
            self.variables = fields['Variable']
        else:
            self.variables = None
        return

class ModelApplication(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'observation' in fields:
            self.observation = fields['observation'][0]
        else:
            self.observation = None
        if 'model' in fields:
            self.model = fields['model'][0]
        else:
            self.model = None
        if 'url' in fields:
            self.url = fields['url'][0]
        else:
            self.url = None
        if 'software' in fields:
            self.software = fields['software'][0]
        else:
            self.software = None
        return

class Result(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'modelapplication' in fields:
            self.modelapplication = fields['modelapplication'][0]
        else:
            self.modelapplication = None
        if 'value' in fields:
            self.value = fields['value'][0]
        else:
            self.value = None
        if 'interactionvariable' in fields:
            self.interactionvariables = fields['interactionvariable']
        else:
            self.interactionvariable = None
        if 'f' in fields:
            self.f = fields['f'][0]
        else:
            self.f = None
        if 'p' in fields:
            self.p = fields['p'][0]
        else:
            self.p = None
        if 'interpretation' in fields:
            self.interpretation = fields['interpretation'][0]
        else:
            self.interpretation = None
        return

entities = {'SubjectGroup': SubjectGroup, 
            'AcquisitionInstrument': AcquisitionInstrument, 
            'Acquisition': Acquisition, 
            'Data': Data, 
            'AnalysisWorkflow': AnalysisWorkflow, 
            'Observation': Observation, 
            'Model': Model, 
            'ModelApplication': ModelApplication, 
            'Result': Result}

class PubError(Exception):

    """base class for exceptions"""

class HypothesisError(PubError):

    """error in hpyothes.is call"""

class Publication:

    def __init__(self, data):
        self.errors = []
        self._parse_data(data)
        self.pmc_id = None
        return

    def _parse_data(self, data):
        self.subjectgroups = {}
        self.acquisitioninstruments = {}
        self.acquisitions = {}
        self.data = {}
        self.analysisworkflows = {}
        self.observations = {}
        self.models = {}
        self.modelapplications = {}
        self.results = {}
        fields = {}
        first_line = None
        line_no = 0
        for line in data.split('\n'):
            line_no += 1
            if line:
                try:
                    (name, value) = [ el.strip() for el in line.split(':', 1) ]
                except ValueError:
                    MarkupError('error in line: %s' % line)
                else:
                    name = name.lower()
                    fields.setdefault(name, []).append(value)
                    if not first_line:
                        first_line = line_no
            else:
                if fields:
                    try:
                        self._create_entity(first_line, fields)
                    except MarkupError, data:
                        self.errors.append(data)
                fields = {}
                first_line = None
        if fields:
            try:
                self._create_entity(first_line, fields)
            except MarkupError, data:
                self.errors.append(data)
        return

    def _create_entity(self, first_line, fields):
        if 'hypothesisid' in fields:
            ident = 'in annotation ID %s' % fields['hypothesisid'][0]
        else:
            ident = 'in block starting at line %d' % first_line
        if 'csentity' not in fields:
            raise MarkupError('no entity type given %s' % ident)
        entity_type = fields['csentity'][0]
        if entity_type not in entities:
            raise MarkupError('bad entity type given %s' % ident)
        ent = entities[entity_type](fields, ident)
        if not ent.id:
            return
        if entity_type == 'SubjectGroup':
            d = self.subjectgroups
        if entity_type == 'AcquisitionInstrument':
            d = self.acquisitioninstruments
        if entity_type == 'Acquisition':
            d = self.acquisitions
        if entity_type == 'Data':
            d = self.data
        if entity_type == 'AnalysisWorkflow':
            d = self.analysisworkflows
        if entity_type == 'Observation':
            d = self.observations
        if entity_type == 'Model':
            d = self.models
        if entity_type == 'ModelApplication':
            d = self.modelapplications
        if entity_type == 'Result':
            d = self.results
        if ent.id in d:
            raise MarkupError('duplicate ID %s %s' % (ent.id, ident))
        else:
            d[ent.id] = ent
        return

    @staticmethod
    def pub_from_pmc_id(pmc_id):

        """gets annotations from to a PubMed Central manuscript, put in in a 
        flat text form, and use that to create a publication object"""

        url = 'http://www.ncbi.nlm.nih.gov/pmc/articles/%s' % pmc_id

        conn = httplib.HTTPSConnection('hypothes.is')
        url = '/api/search?%s' % urllib.urlencode({'uri': url})
        conn.request('GET', url, '', {'Accept': 'application/json'})
        response = conn.getresponse()
        if response.status != 200:
            raise HypothesisError()
        data = response.read()
        obj = json.loads(data)
        conn.close()

        # all lines, to be joined later and passed to the publication 
        # constructor
        lines = []

        # lines in a block, that will need a Hypothesis ID and entity 
        # type prepended
        # these are flushed to the list "lines" at each blank line (double 
        # newline) or after each annotation
        block_lines = []

        for annot in obj['rows']:
            if 'CANDISharePub' not in annot['tags']:
                continue
            for et in entities:
                if et in annot['tags']:
                    entity_type = et
                    break
                else:
                    entity_type = None
            for line in annot['text'].split('\n'):
                line = line.strip()
                if line:
                    if line not in ('<pre>', '</pre>'):
                        block_lines.append(line)
                else:
                    if block_lines:
                        lines.append('HypothesisID: %s' % annot['id'])
                        if entity_type:
                            lines.append('CSEntity: %s' % entity_type)
                        lines.extend(block_lines)
                        lines.append('')
                        block_lines = []
            if block_lines:
                lines.append('HypothesisID: %s' % annot['id'])
                if entity_type:
                    lines.append('CSEntity: %s' % entity_type)
                lines.extend(block_lines)
                lines.append('')
                block_lines = []

        pub = Publication('\n'.join(lines))
        pub.pmc_id = pmc_id

        return pub

# eof
