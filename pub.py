import json
import httplib
import urllib
import cgi

class PubError:

    """base class for publication errors

    these are not derived from Exception because they are not errors to be 
    caught in code
    """

class MarkupError(PubError):

    """parse or markup error

    instances belong to Pub instances and have associated annotations
    """

    def __init__(self, msg, annotation_id):
        self.msg = msg
        self.annotation_id = annotation_id
        return

    def render(self):
        fmt = '<a href="%s">%s in annotation</a>'
        return fmt % (annot_url(self.annotation_id), cgi.escape(self.msg))

class LinkError(PubError):

    """missing link error

    instances belong to entities
    """

    def __init__(self, msg):
        self.msg = msg
        return

    def render(self):
        return cgi.escape(self.msg)

class PubWarning:

    """base class for publication warnings"""

class MissingFieldWarning(PubWarning):

    """missing field"""

    def __init__(self, field):
        self.field = field
        return

    def render(self):
        return 'Missing field %s' % cgi.escape(self.field)

class Entity:

    """base class for entities"""

    multi_attrs = ()

    def __init__(self, id, fields):
        self.errors = []
        self.id = id
        field_dict = {}
        for (annotation_id, name, value) in fields:
            field_dict.setdefault(name, [])
            field_dict[name].append((annotation_id, value))
        for (an, name, _) in self.attributes:
            if name in field_dict:
                vals = [ el[1] for el in field_dict[name] ]
                if an in self.multi_attrs:
                    setattr(self, an, vals)
                else:
                    setattr(self, an, vals[0])
                del field_dict[name]
            else:
                setattr(self, an, None)
        for name in field_dict:
            annot_id = field_dict[name][0][0]
            err = MarkupError('Unknown field "%s"' % name, annot_id)
            self.errors.append(err)
        return

    def render(self):
        output = '<div class="entity">'
        output += '<div class="eid">%s</div>\n' % self.id
        for error in self.errors:
            output += '<div class="error">%s</div>\n' % error.render()
        output += '<ul class="fields">\n'
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
        output += '</div>\n'
        return output

class SubjectGroup(Entity):

    prefix = 'sg'

    # attribute, key, display
    attributes = (('diagnosis', 'diagnosis', 'Diagnosis'), 
                  ('n_subjects', 'nsubjects', 'Subjects'), 
                  ('age_mean', 'agemean', 'Age mean'), 
                  ('age_sd', 'agesd', 'Age SD'))

class AcquisitionInstrument(Entity):

    prefix = 'ai'

    attributes = (('type', 'type', 'Type'), 
                  ('location', 'location', 'Location'), 
                  ('field', 'field', 'Field'), 
                  ('manufacturer', 'manufacturer', 'Manufacturer'), 
                  ('model', 'model', 'Model'))

class Acquisition(Entity):

    prefix = 'a'

    attributes = (('type', 'type', 'type'), 
                  ('acquisitioninstrument', 'acquisitioninstrument', 'Acquisition Instrument'))

class Data(Entity):

    prefix = 'd'

    attributes = (('url', 'url', 'url'), 
                  ('doi', 'doi', 'doi'), 
                  ('acquisition', 'acquisition', 'acquisition'), 
                  ('subjectgroup', 'subjectgroup', 'subjectgroup'))

class AnalysisWorkflow(Entity):

    prefix = 'aw'

    attributes = (('method', 'method', 'Method'), 
                  ('methodurl', 'methodurl', 'Method URL'), 
                  ('software', 'software', 'Software'))

class Observation(Entity):

    prefix = 'o'

    attributes = (('data', 'data', 'Data'), 
                  ('analysisworkflow', 'analysisworkflow', 'Analysis Workflow'), 
                  ('measure', 'measure', 'Measure'))

    multi_attrs = ('data', )

class Model(Entity):

    prefix = 'm'

    attributes = (('variables', 'variable', 'Variables'), )

    mutli_attrs = ('variable', )

class ModelApplication(Entity):

    prefix = 'ma'

    attributes = (('observation', 'observation', 'Observation'), 
                  ('model', 'model', 'Model'), 
                  ('url', 'url', 'URL'), 
                  ('software', 'software', 'Software'))

class Result(Entity):

    prefix = 'r'

    attributes = (('modelapplication', 'modelapplication', 'Model Application'), 
                  ('value', 'value', 'Value'), 
                  ('interactionvariable', 'interactionvariable', 'Interaction variables'), 
                  ('f', 'f', 'f'), 
                  ('p', 'p', 'p'), 
                  ('interpretation', 'interpretation', 'Interpretation'))

    multi_attrs = ('interactinovariable', )

# entities[entity type] = (entity class, pub attribute name)
entities = {'SubjectGroup': (SubjectGroup, 
                             'subjectgroups'), 
            'AcquisitionInstrument': (AcquisitionInstrument, 
                                      'acquisitioninstruments'), 
            'Acquisition': (Acquisition, 
                            'acquisitions'), 
            'Data': (Data, 
                     'data'), 
            'AnalysisWorkflow': (AnalysisWorkflow, 
                                 'analysisworkflows'), 
            'Observation': (Observation, 
                            'observations'), 
            'Model': (Model, 
                      'models'), 
            'ModelApplication': (ModelApplication, 
                                 'modelapplications'), 
            'Result': (Result, 
                       'results')}

class PubError(Exception):

    """base class for exceptions"""

class HypothesisError(PubError):

    """error in hpyothes.is call"""

class Publication:

    def __init__(self, pmc_id):
        self.pmc_id = pmc_id
        self.errors = []
        self.warnings = []
        self.subjectgroups = {}
        self.acquisitioninstruments = {}
        self.acquisitions = {}
        self.data = {}
        self.analysisworkflows = {}
        self.observations = {}
        self.models = {}
        self.modelapplications = {}
        self.results = {}
        self._read_annotations()
        self._check_links()
        return

    def _read_annotations(self):
        e_dict = self._get_annotations()
        self._create_entities(e_dict)
        return

    def _get_annotations(self):

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

        url = 'http://www.ncbi.nlm.nih.gov/pmc/articles/%s' % self.pmc_id

        conn = httplib.HTTPSConnection('hypothes.is')
        url = '/api/search?%s' % urllib.urlencode({'uri': url})
        conn.request('GET', url, '', {'Accept': 'application/json'})
        response = conn.getresponse()
        if response.status != 200:
            raise HypothesisError()
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
                msg = 'Missing or unknown entity type'
                self.errors.append(MarkupError(msg, annot['id']))
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
                        msg = 'Bad field definition "%s"' % line
                        self.errors.append(MarkupError(msg, annot_id))
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
                        err = MarkupError('Duplicate ID "%s"' % id, annot_id)
                        self.errors.append(err)
                    else:
                        d_base[entity_type][id] = fields
                elif plus_id:
                    d_plus.setdefault(entity_type, {})
                    d_plus[entity_type][plus_id] = fields
                else:
                    self.errors.append(MarkupError('No ID given', annot_id))

        # third pass: move d_plus entires into d_base

        # generates: unknown ID errors

        for entity_type in d_plus:
            for entity_id in d_plus[entity_type]:
                try:
                    base = d_base[entity_type][entity_id]
                except KeyError:
                    annot_id = d_plus[entity_type][entity_id][0][0]
                    self.errors.append('unknown ID %s' % entity_id, annot_id)
                else:
                    base.extend(d_plus[entity_type][entity_id])

        return d_base

    def _create_entities(self, e_dict):
        for entity_type in e_dict:
            for entity_id in e_dict[entity_type]:
                (cls, an) = entities[entity_type]
                ent = cls(entity_id, e_dict[entity_type][entity_id])
                d = getattr(self, an)
                d[ent.id] = ent
        return

    def _check_fields(self):
        """check for undefined fields"""

    def _check_links(self):
        """check inter-entity links"""
        for ai in self.acquisitions.itervalues():
            if not ai.acquisitioninstrument:
                ai.errors.append(LinkError('No acquisition instrument given'))
            elif ai.acquisitioninstrument not in self.acquisitioninstruments:
                fmt = 'Undefined acquisition instrument "%s"'
                err = LinkError(fmt % ai.acquisitioninstrument)
                ai.errors.append(err)
        for d in self.data.itervalues():
            if not d.subjectgroup:
                d.errors.append(LinkError('No subject group given'))
            elif d.subjectgroup not in self.subjectgroups:
                err = LinkError('undefined subject group "%s"' % d.subjectgroup)
                d.errors.append(err)
            if not d.acquisition:
                d.errors.append(LinkError('No acquisition given'))
            elif d.acquisition not in self.data:
                err = LinkError('Undefined acquisition "%s"' % d.acquisition)
                d.errors.append(err)
        for o in self.observations.itervalues():
            if not o.analysisworkflow:
                o.errors.append(LinkError('No analysis workflow given'))
            elif o.analysisworkflow not in self.analysisworkflows:
                fmt = 'Undefined analysis workflow "%s"'
                err = LinkError(fmt % o.analysisworkflow)
                o.errors.append(err)
            if not o.data:
                o.errors.append(LinkError('No data given'))
            for data in o.data:
                if data not in self.data:
                    err = LinkError('Undefined data "%s"' % o.data)
                    o.errors.append(err)
        for ma in self.modelapplications.itervalues():
            if not ma.model:
                ma.errors.append(LinkError('No model given'))
            elif ma.model not in self.models:
                ma.errors.append(LinkError('Undefined model "%s"' % ma.model))
            if not ma.observation:
                ma.errors.append(LinkError('No observation given'))
            elif ma.observation not in self.observations:
                err = LinkError('Undefined observation "%s"' % ma.observation)
                ma.errors.append(err)
        for r in self.results.itervalues():
            if not r.modelapplication:
                r.errors.append(LinkError('No model application given'))
            elif r.modelapplication not in self.modelapplications:
                fmt = 'Undefined model application "%s"'
                err = LinkError(fmt % r.modelapplication)
                r.errors.append(err)
        return

def annot_url(annot_id):
    """annot_url(annot_id) -> url

    generate the URL for a hypothes.is annotation
    """
    return 'http://hypothes.is/a/%s' % annot_id

# eof
