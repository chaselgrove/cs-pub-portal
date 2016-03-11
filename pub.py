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

    def _check_fields(self, fields, ident):
        """check remaining fields after all known ones have been recorded"""
        for key in fields:
            if key not in ('id', 'hypothesisid', 'csentity'):
                err = MarkupError('unknown field %s %s' % (key, ident))
                self.errors.append(err)
        return

class SubjectGroup(Entity):

    # attribute, key, display
    fields = (('diagnosis', 'diagnosis', 'Diagnosis'), 
              ('n_subjects', 'nsubjects', 'Subjects'), 
              ('age_mean', 'agemean', 'Age mean'), 
              ('age_sd', 'agesd', 'Age SD'))

    prefix = 'sg'

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        for (an, key, _) in self.fields:
            if key in fields:
                setattr(self, an, fields[key][0])
                del fields[key]
            else:
                setattr(self, an, None)
        return

    def render(self):
        output = ''
        output += '<a name="%s_%s"></a>\n' % (self.prefix, self.id)
        output += '<p>%s</p>\n' % self.id
        if not self.errors:
            output += '<p>No errors.</p>\n'
        else:
            output += '<p>Errors:</p>\n'
            for error in self.errors:
                output += '<p>%s</p>\n' % str(error)
        output += '<ul>\n'
        output += '<li>ID: %s</li>\n' % self.id
        for (an, _, display) in self.fields:
            output += '<li>%s: %s</li>\n' % (display, getattr(self, an))
        output += '</ul>\n'
        return output

class AcquisitionInstrument(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'type' in fields:
            self.type = fields['type'][0]
            del fields['type']
        else:
            self.type = None
        if 'location' in fields:
            self.location = fields['location'][0]
            del fields['location']
        else:
            self.location = None
        if 'field' in fields:
            self.field = fields['field'][0]
            del fields['field']
        else:
            self.field = None
        if 'manufacturer' in fields:
            self.manufacturer = fields['manufacturer'][0]
            del fields['manufacturer']
        else:
            self.manufacturer = None
        if 'model' in fields:
            self.model = fields['model'][0]
            del fields['model']
        else:
            self.model = None
        return

class Acquisition(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'type' in fields:
            self.type = fields['type'][0]
            del fields['type']
        else:
            self.type = None
        if 'acquisitioninstrument' in fields:
            self.acquisitioninstrument = fields['acquisitioninstrument'][0]
            del fields['acquisitioninstrument']
        else:
            self.acquisitioninstrument = None
        self._check_fields(fields, ident)
        return

class Data(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'url' in fields:
            self.url = fields['url'][0]
            del fields['url']
        else:
            self.url = None
        if 'doi' in fields:
            self.doi = fields['doi'][0]
            del fields['doi']
        else:
            self.doi = None
        if 'acquisition' in fields:
            self.acquisition = fields['acquisition'][0]
            del fields['acquisition']
        else:
            self.acquisition = None
        if 'subjectgroup' in fields:
            self.subjectgroup = fields['subjectgroup'][0]
            del fields['subjectgroup']
        else:
            self.subjectgroup = None
        return

class AnalysisWorkflow(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'method' in fields:
            self.method = fields['method'][0]
            del fields['method']
        else:
            self.method = None
        if 'methodurl' in fields:
            self.methodurl = fields['methodurl'][0]
            del fields['methodurl']
        else:
            self.methodurl = None
        if 'software' in fields:
            self.software = fields['software'][0]
            del fields['software']
        else:
            self.software = None
        return

class Observation(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'data' in fields:
            self.data = fields['data']
            del fields['data']
        else:
            self.data = None
        if 'analysisworkflow' in fields:
            self.analysisworkflow = fields['analysisworkflow'][0]
            del fields['analysisworkflow']
        else:
            self.analysisworkflow = None
        if 'meausure' in fields:
            self.meausure = fields['meausure'][0]
            del fields['meausure']
        else:
            self.meausure = None
        return

class Model(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'Variable' in fields:
            self.variables = fields['Variable']
            del fields['Variable']
        else:
            self.variables = None
        return

class ModelApplication(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'observation' in fields:
            self.observation = fields['observation'][0]
            del fields['observation']
        else:
            self.observation = None
        if 'model' in fields:
            self.model = fields['model'][0]
            del fields['model']
        else:
            self.model = None
        if 'url' in fields:
            self.url = fields['url'][0]
            del fields['url']
        else:
            self.url = None
        if 'software' in fields:
            self.software = fields['software'][0]
            del fields['software']
        else:
            self.software = None
        return

class Result(Entity):

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        if 'modelapplication' in fields:
            self.modelapplication = fields['modelapplication'][0]
            del fields['modelapplication']
        else:
            self.modelapplication = None
        if 'value' in fields:
            self.value = fields['value'][0]
            del fields['value']
        else:
            self.value = None
        if 'interactionvariable' in fields:
            self.interactionvariables = fields['interactionvariable']
            del fields['interactionvariable']
        else:
            self.interactionvariable = None
        if 'f' in fields:
            self.f = fields['f'][0]
            del fields['f']
        else:
            self.f = None
        if 'p' in fields:
            self.p = fields['p'][0]
            del fields['p']
        else:
            self.p = None
        if 'interpretation' in fields:
            self.interpretation = fields['interpretation'][0]
            del fields['interpretation']
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
        self._check_links()
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

    def _check_links(self):
        """check inter-entity links"""
        for ai in self.acquisitions.itervalues():
            if not ai.acquisitioninstrument:
                ai.errors.append(MarkupError('no acquisition instrument given'))
            elif ai.acquisitioninstrument not in self.acquisitioninstruments:
                fmt = 'undefined acquisition instrument %s'
                err = MarkupError(fmt % ai.acquisitioninstrument)
                ai.errors.append(err)
        for d in self.data.itervalues():
            if not d.subjectgroup:
                d.errors.append(MarkupError('no subject group given'))
            elif d.subjectgroup not in self.subjectgroups:
                err = MarkupError('undefined subject group %s' % d.subjectgroup)
                d.errors.append(err)
            if not d.acquisition:
                d.errors.append(MarkupError('no acquisition given'))
            elif d.acquisition not in self.data:
                err = MarkupError('undefined acquisition %s' % d.acquisition)
                d.errors.append(err)
        for o in self.observations.itervalues():
            if not o.analysisworkflow:
                o.errors.append(MarkupError('no analysis workflow given'))
            elif o.analysisworkflow not in self.analysisworkflows:
                fmt = 'undefined analysis workflow %s'
                err = MarkupError(fmt % o.analysisworkflow)
                o.errors.append(err)
            if not o.data:
                o.errors.append(MarkupError('no data given'))
            for data in o.data:
                if data not in self.data:
                    err = MarkupError('undefined data %s' % o.data)
                    o.errors.append(err)
        for ma in self.modelapplications.itervalues():
            if not ma.model:
                ma.errors.append(MarkupError('no model given'))
            elif ma.model not in self.models:
                ma.errors.append(MarkupError('undefined model %s' % ma.model))
            if not ma.observation:
                ma.errors.append(MarkupError('no observation given'))
            elif ma.observation not in self.observations:
                err = MarkupError('undefined observation %s' % ma.observation)
                ma.errors.append(err)
        for r in self.results.itervalues():
            if not r.modelapplication:
                r.errors.append(MarkupError('no model application given'))
            elif r.modelapplication not in self.modelapplications:
                fmt = 'undefined model application %s'
                err = MarkupError(fmt % r.modelapplication)
                r.errors.append(err)
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
