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
        fmt = '<a href="%s">%s</a>'
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
        return 'Missing field "%s"' % cgi.escape(self.field)

class Entity:

    """base class for entities"""

    multi_attrs = ()

    def __init__(self, pub, id, fields):
        self.pub = pub
        self.id = id
        self.annotation_ids = set()
        self.errors = []
        self.warnings = []
        self.points = []
        field_dict = {}
        for (annotation_id, name, value) in fields:
            field_dict.setdefault(name, [])
            field_dict[name].append((annotation_id, value))
            self.annotation_ids.add(annotation_id)
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
                self.warnings.append(MissingFieldWarning(name))
        for name in field_dict:
            annot_id = field_dict[name][0][0]
            err = MarkupError('Unknown field "%s"' % name, annot_id)
            self.errors.append(err)
        return

    def score(self):
        """obj.score() -> (score, maximum possible score)"""
        s = 0
        max = 0
        for (val, _) in self.points:
            if val > 0:
                max += val
            s += val
        return (s, max)

    def __getitem__(self, key):
        for (an, _, _) in self.attributes:
            if key == an:
                break
        else:
            raise KeyError(key)
        return getattr(self, key)

    def display_value(self, key):
        value = self[key]
        if value is None:
            return ''
        if isinstance(value, list):
            return ', '.join(value)
        return value

    def annotation_links(self):
        for annot_id in self.annotation_ids:
            url = annot_url(annot_id)
            yield '<a href="%s">%s</a>' % (url, annot_id)
        return

class SubjectGroup(Entity):

    # attribute, key, display
    attributes = (('diagnosis', 'diagnosis', 'Diagnosis'), 
                  ('n_subjects', 'nsubjects', 'Subjects'), 
                  ('age_mean', 'agemean', 'Age mean'), 
                  ('age_sd', 'agesd', 'Age SD'))

    def check(self):
        self.points.append((5, 'Just for being'))
        # check for missing fields
        for (an, name, _) in self.attributes:
            if not getattr(self, an):
                self.points.append((-1, 'Missing %s' % name))
        return

class AcquisitionInstrument(Entity):

    attributes = (('type', 'type', 'Type'), 
                  ('location', 'location', 'Location'), 
                  ('field', 'field', 'Field'), 
                  ('manufacturer', 'manufacturer', 'Manufacturer'), 
                  ('model', 'model', 'Model'))

    def check(self):
        self.points.append((7, 'Just for being'))
        # check for missing fields
        for (an, name, _) in self.attributes:
            if not getattr(self, an):
                if an == 'field':
                    self.points.append((-2, 'Missing %s' % name))
                else:
                    self.points.append((-1, 'Missing %s' % name))
        return

class Acquisition(Entity):

    attributes = (('type', 'type', 'type'), 
                  ('acquisitioninstrument', 'acquisitioninstrument', 'Acquisition Instrument'))

    def check(self):
        self.points.append((3, 'Just for being'))
        # check for missing fields
        if not self.type:
            self.points.append((-1, 'Missing type'))
        if not self.acquisitioninstrument:
            self.points.append((-1, 'Missing acquisition instrument'))
        elif self.acquisitioninstrument not in self.pub.acquisitioninstruments:
            fmt = 'Undefined acquisition instrument "%s"'
            msg = fmt % self.acquisitioninstrument
            self.errors.append(LinkError(msg))
        return

class Data(Entity):

    attributes = (('url', 'url', 'URL'), 
                  ('doi', 'doi', 'DOI'), 
                  ('acquisition', 'acquisition', 'acquisition'), 
                  ('subjectgroup', 'subjectgroup', 'subjectgroup'))

    def check(self):
        self.points.append((10, 'Just for being'))
        if not self.url and not self.doi:
            self.points.append((-5, 'No link to data (DOI or URL)'))
        if not self.subjectgroup:
            self.points.append((-1, 'Missing subject group'))
        elif self.subjectgroup not in self.pub.subjectgroups:
            msg = 'Undefined subjectgroup "%s"' % self.subjectgroup
            self.errors.append(LinkError(msg))
        if not self.acquisition:
            self.points.append((-1, 'Missing acquisition'))
        elif self.acquisition not in self.pub.acquisitions:
            msg = 'Undefined acquisition "%s"' % self.acquisition
            self.errors.append(LinkError(msg))
        return

class AnalysisWorkflow(Entity):

    attributes = (('method', 'method', 'Method'), 
                  ('methodurl', 'methodurl', 'Method URL'), 
                  ('software', 'software', 'Software'))

    def check(self):
        self.points.append((5, 'Just for being'))
        if not self.method:
            self.points.append((-1, 'Missing method'))
        if not self.methodurl:
            self.points.append((-2, 'Missing method URL'))
        if not self.software:
            self.points.append((-1, 'Missing software'))
        return

class Observation(Entity):

    attributes = (('data', 'data', 'Data'), 
                  ('analysisworkflow', 'analysisworkflow', 'Analysis Workflow'), 
                  ('measure', 'measure', 'Measure'))

    multi_attrs = ('data', )

    def check(self):
        self.points.append((10, 'Just for being'))
        if not self.measure:
            self.points.append((-5, 'No measure'))
        if not self.data:
            self.points.append((-2, 'Missing data'))
        else:
            for data in self.data:
                if data not in self.pub.data:
                    self.errors.append(LinkError('Undefined data %s' % data))
        if not self.analysisworkflow:
            self.points.append((-2, 'Missing analysis workflow'))
        elif self.analysisworkflow not in self.pub.analysisworkflows:
            msg = 'Undefined analysis workflow %s' % self.analysisworkflow
            self.errors.append(LinkError(msg))
        return

class Model(Entity):

    attributes = (('variables', 'variable', 'Variables'), )

    multi_attrs = ('variables', )

    def check(self):
        self.points.append((5, 'Just for being'))
        # check if any variables are defined
        # check for bad interaction variables
        if not self.variables:
            self.points.append((-4, 'No variables defined'))
        else:
            simple_vars = []
            int_vars = []
            bad_components = set()
            for var in self.variables:
                if '+' in var:
                    int_vars.append(var)
                else:
                    simple_vars.append(var)
            for int_var in int_vars:
                for int_component in int_var.split('+'):
                    if int_component not in simple_vars:
                        bad_components.add(int_component)
            if bad_components:
                vars = ', '.join(sorted(bad_components))
                msg = 'Variables only in interaction terms: %s' % vars
                self.points.append((-2, msg))
        return

class ModelApplication(Entity):

    attributes = (('observations', 'observation', 'Observations'), 
                  ('model', 'model', 'Model'), 
                  ('url', 'url', 'URL'), 
                  ('software', 'software', 'Software'))

    multi_attrs = ('observations', )

    def check(self):
        self.points.append((11, 'Just for being'))
        if not self.url:
            self.points.append((-5, 'No link to analysis'))
        if not self.software:
            self.points.append((-1, 'Software undefined'))
        if not self.model:
            self.points.append((-2, 'Model undefined'))
        elif self.model not in self.pub.models:
            self.errors.append(LinkError('Undefined model %s' % self.model))
        if not self.observations:
            self.points.append((-2, 'No observations defined'))
        else:
            for o in self.observations:
                if o not in self.pub.observations:
                    err = LinkError('Undefined observation %s' % o)
                    self.errors.append(err)
        return

class Result(Entity):

    attributes = (('modelapplication', 'modelapplication', 'Model Application'), 
                  ('value', 'value', 'Value'), 
                  ('variables', 'variable', 'Variables'), 
                  ('f', 'f', 'f'), 
                  ('p', 'p', 'p'), 
                  ('interpretation', 'interpretation', 'Interpretation'))

    multi_attrs = ('interactinovariables', )

    def check(self):
        self.points.append((23, 'Just for being'))
        if not self.value:
            self.points.append((-3, 'Value undefined'))
        if not self.f:
            self.points.append((-2, 'F undefined'))
        if not self.p:
            self.points.append((-5, 'P undefined'))
        if not self.interpretation:
            self.points.append((-2, 'Interpretation undefined'))
        if not self.modelapplication:
            self.points.append((-5, 'No model application given'))
            model_vars = None
        elif self.modelapplication not in self.pub.modelapplications:
            msg = 'Undefined model application %s' % self.modelapplication
            self.errors.append(LinkError(msg))
            model_vars = None
        else:
            ma = self.pub.modelapplications[self.modelapplication]
            if not ma.model:
                model_vars = None
            elif ma.model not in self.pub.models:
                model_vars = None
            else:
                model_vars = self.pub.models[ma.model]
        if not self.variables:
            self.points.append((-5, 'No variables defined'))
        else:
            if not model_vars:
                self.points.append((-2, 'No model variables to check against'))
            else:
                bad_vars = set()
                for var in self.variables:
                    if var not in model_vars:
                        bad_vars.add(var)
                if bad_vars:
                    fmt = 'Variables not defined in the model: %s'
                    msg = fmt % ', '.join(sorted(bad_vars))
                    self.points.append((-2, msg))
        return

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
        for sg in self.subjectgroups.itervalues():
            sg.check()
        for ai in self.acquisitioninstruments.itervalues():
            ai.check()
        for a in self.acquisitions.itervalues():
            a.check()
        for d in self.data.itervalues():
            d.check()
        for aw in self.analysisworkflows.itervalues():
            aw.check()
        for o in self.observations.itervalues():
            o.check()
        for m in self.models.itervalues():
            m.check()
        for ma in self.modelapplications.itervalues():
            ma.check()
        for r in self.results.itervalues():
            r.check()
        return

    def score(self):
        s = 0
        max = 0
        for sg in self.subjectgroups.itervalues():
            (es, emax) = sg.score()
            s += es
            max += emax
        for ai in self.acquisitioninstruments.itervalues():
            (es, emax) = ai.score()
            s += es
            max += emax
        for a in self.acquisitions.itervalues():
            (es, emax) = a.score()
            s += es
            max += emax
        for d in self.data.itervalues():
            (es, emax) = d.score()
            s += es
            max += emax
        for aw in self.analysisworkflows.itervalues():
            (es, emax) = aw.score()
            s += es
            max += emax
        for o in self.observations.itervalues():
            (es, emax) = o.score()
            s += es
            max += emax
        for m in self.models.itervalues():
            (es, emax) = m.score()
            s += es
            max += emax
        for ma in self.modelapplications.itervalues():
            (es, emax) = ma.score()
            s += es
            max += emax
        for r in self.results.itervalues():
            (es, emax) = r.score()
            s += es
            max += emax
        return (s, max)

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
                    err = MarkupError('Unknown ID %s' % entity_id)
                    self.errors.append(err, annot_id)
                else:
                    base.extend(d_plus[entity_type][entity_id])

        return d_base

    def _create_entities(self, e_dict):
        for entity_type in e_dict:
            for entity_id in e_dict[entity_type]:
                (cls, an) = entities[entity_type]
                ent = cls(self, entity_id, e_dict[entity_type][entity_id])
                d = getattr(self, an)
                d[ent.id] = ent
        return

def annot_url(annot_id):
    """annot_url(annot_id) -> url

    generate the URL for a hypothes.is annotation
    """
    return 'http://hypothes.is/a/%s' % annot_id

# eof
