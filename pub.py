import json
import httplib
import urllib
import cgi

class MarkupError:

    """exception for parse or markup errors"""

    def __init__(self, msg):
        self.msg = msg
        return

    def __str__(self):
        return 'Markup error: %s' % self.msg

class Entity:

    """base class for entities"""

    multi_attrs = ()

    def __init__(self, fields, ident):
        self.errors = []
        if 'id' not in fields:
            self.errors.append(MarkupError('no ID given %s' % ident))
            self.id = None
        else:
            self.id = fields['id'][0]
        return

    def init2(self, fields):
        for (an, key, _) in self.attributes:
            if key in fields:
                if an in self.multi_attrs:
                    setattr(self, an, fields[key])
                else:
                    setattr(self, an, fields[key][0])
                del fields[key]
            else:
                setattr(self, an, None)
        return

    def _check_fields(self, fields, ident):
        """check remaining fields after all known ones have been recorded"""
        for key in fields:
            if key not in ('id', 'hypothesisid', 'csentity'):
                err = MarkupError('unknown field %s %s' % (key, ident))
                self.errors.append(err)
        return

    def render(self):
        output = ''
        output += '<p>%s</p>\n' % self.id
        if not self.errors:
            output += '<p>No errors.</p>\n'
        else:
            output += '<p>Errors:</p>\n'
            for error in self.errors:
                output += '<p>%s</p>\n' % cgi.escape(str(error))
        output += '<ul>\n'
        output += '<li>ID: %s</li>\n' % cgi.escape(self.id)
        for (an, _, display) in self.attributes:
            val = getattr(self, an)
            if val is None:
                disp_val = ''
            elif isinstance(val, list):
                parts = [ cgi.escape(el) for el in val ]
                disp_val = ', '.join(parts)
            else:
                disp_val = cgi.escape(str(val))
            output += '<li>%s: %s</li>\n' % (display, disp_val)
        output += '</ul>\n'
        return output

class SubjectGroup(Entity):

    prefix = 'sg'

    # attribute, key, display
    attributes = (('diagnosis', 'diagnosis', 'Diagnosis'), 
                  ('n_subjects', 'nsubjects', 'Subjects'), 
                  ('age_mean', 'agemean', 'Age mean'), 
                  ('age_sd', 'agesd', 'Age SD'))

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        self.init2(fields)
        self._check_fields(fields, ident)
        return

class AcquisitionInstrument(Entity):

    prefix = 'ai'

    attributes = (('type', 'type', 'Type'), 
                  ('location', 'location', 'Location'), 
                  ('field', 'field', 'Field'), 
                  ('manufacturer', 'manufacturer', 'Manufacturer'), 
                  ('model', 'model', 'Model'))

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        self.init2(fields)
        self._check_fields(fields, ident)
        return

class Acquisition(Entity):

    prefix = 'a'

    attributes = (('type', 'type', 'type'), 
                  ('acquisitioninstrument', 'acquisitioninstrument', 'Acquisition Instrument'))

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        self.init2(fields)
        self._check_fields(fields, ident)
        return

class Data(Entity):

    prefix = 'd'

    attributes = (('url', 'url', 'url'), 
                  ('doi', 'doi', 'doi'), 
                  ('acquisition', 'acquisition', 'acquisition'), 
                  ('subjectgroup', 'subjectgroup', 'subjectgroup'))

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        self.init2(fields)
        self._check_fields(fields, ident)
        return

class AnalysisWorkflow(Entity):

    prefix = 'aw'

    attributes = (('method', 'method', 'Method'), 
                  ('methodurl', 'methodurl', 'Method URL'), 
                  ('software', 'software', 'Software'))

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        self.init2(fields)
        self._check_fields(fields, ident)
        return

class Observation(Entity):

    prefix = 'o'

    attributes = (('data', 'data', 'Data'), 
                  ('analysisworkflow', 'analysisworkflow', 'Analysis Workflow'), 
                  ('measure', 'measure', 'Measure'))

    multi_attrs = ('data', )

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        self.init2(fields)
        self._check_fields(fields, ident)
        return

class Model(Entity):

    prefix = 'm'

    attributes = (('variables', 'variable', 'Variables'), )

    mutli_attrs = ('variable', )

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        self.init2(fields)
        self._check_fields(fields, ident)
        return

class ModelApplication(Entity):

    prefix = 'ma'

    attributes = (('observation', 'observation', 'Observation'), 
                  ('model', 'model', 'Model'), 
                  ('url', 'url', 'URL'), 
                  ('software', 'software', 'Software'))

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        self.init2(fields)
        self._check_fields(fields, ident)
        return

class Result(Entity):

    prefix = 'r'

    attributes = (('modelapplication', 'modelapplication', 'Model Application'), 
                  ('value', 'value', 'Value'), 
                  ('interactionvariable', 'interactionvariable', 'Interaction variables'), 
                  ('f', 'f', 'f'), 
                  ('p', 'p', 'p'), 
                  ('interpretation', 'interpretation', 'Interpretation'))

    multi_attrs = ('interactinovariable', )

    def __init__(self, fields, ident):
        Entity.__init__(self, fields, ident)
        self.init2(fields)
        self._check_fields(fields, ident)
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
