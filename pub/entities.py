from collections import OrderedDict
from .errors import *
from .utils import annot_url
from .fields import *

class Entity:

    """base class for entities"""

    multi_attrs = ()

    def __init__(self, pub, id, values):
        self.pub = pub
        self.id = id
        self.annotation_ids = set()
        self.errors = []
        self.points = []
        self.links = []
        self.fields = OrderedDict()
        for (key, cls, display_name) in self.field_defs:
            self.fields[key] = cls(display_name)
        for (annotation_id, name, value) in values:
            self.annotation_ids.add(annotation_id)
            if name in self.fields:
                self.fields[name].set(value)
            else:
                self.errors.append(UnknownFieldError(name, annotation_id))
        return

    def __getitem__(self, key):
        return self.fields[key].value

    def set_related(self):
        """set related entities"""
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

    def annotation_links(self):
        for annot_id in self.annotation_ids:
            url = annot_url(annot_id)
            yield '<a href="%s">%s</a>' % (url, annot_id)
        return

class SubjectGroup(Entity):

    field_defs = (('diagnosis', Field, 'Diagnosis'), 
                  ('nsubjects', Field, 'Subjects'), 
                  ('agemean', Field, 'Age mean'), 
                  ('agesd', Field, 'Age SD'))

    def check(self):
        self.points.append((5, 'Existential credit'))
        # check for missing fields
        for (name, field) in self.fields.iteritems():
            if not field.value:
                self.points.append((-1, 'Missing %s' % name))
        return

class AcquisitionInstrument(Entity):

    field_defs = (('type', Field, 'Type'), 
                  ('location', Field, 'Location'), 
                  ('field', Field, 'Field'), 
                  ('manufacturer', Field, 'Manufacturer'), 
                  ('model', Field, 'Model'))

    def check(self):
        self.points.append((7, 'Existential credit'))
        # check for missing fields
        for (name, field) in self.fields.iteritems():
            if not field.value:
                if name == 'field':
                    self.points.append((-2, 'Missing %s' % name))
                else:
                    self.points.append((-1, 'Missing %s' % name))
        return

class Acquisition(Entity):

    field_defs = (('type', Field, 'Type'), 
                  ('acquisitioninstrument', Field, 'Acquisition Instrument'), 
                  ('NSlices', Field, 'N Slices'), 
                  ('prep', Field, 'Prep'), 
                  ('tr', Field, 'TE'), 
                  ('te', Field, 'TR'), 
                  ('ti', Field, 'TI'), 
                  ('flipangle', Field, 'Flip Angle'), 
                  ('fov', Field, 'FOV'), 
                  ('slicethickness', Field, 'Slice Thickness'), 
                  ('matrix', Field, 'Matrix'), 
                  ('nexcitations', Field, 'N Excitations'))

    def set_related(self):
        ai_id = self['acquisitioninstrument']
        if ai_id is None:
            self.acquisition_instrument = None
        elif ai_id not in self.pub.entities['AcquisitionInstrument']:
            self.acquisition_instrument = None
            msg = 'Undefined acquisition instrument "%s"' % ai_id
            self.errors.append(LinkError(msg))
        else:
            ai = self.pub.entities['AcquisitionInstrument'][ai_id]
            self.acquisition_instrument = ai
        return

    def check(self):
        self.points.append((3, 'Existential credit'))
        # check for missing fields
        if not self['type']:
            self.points.append((-1, 'Missing type'))
        if not self.acquisition_instrument:
            self.points.append((-1, 'Missing acquisition instrument'))
        return

class Data(Entity):

    field_defs = (('url', URLField, 'URL'), 
                  ('doi', DOIField, 'DOI'), 
                  ('acquisition', Field, 'Acquisition'), 
                  ('subjectgroup', Field, 'Subject Group'))

    def set_related(self):
        a_id = self['acquisition']
        if a_id is None:
            self.acquisition = None
        elif a_id not in self.pub.entities['Acquisition']:
            self.acquisition = None
            self.errors.append(LinkError('Undefined acquisition "%s"' % a_id))
        else:
            self.acquisition = self.pub.entities['Acquisition'][a_id]
        sg_id = self['subjectgroup']
        if sg_id is None:
            self.subject_group = None
        if sg_id not in self.pub.entities['SubjectGroup']:
            self.subject_group = None
            self.errors.append(LinkError('Undefined subjectgroup "%s"' % sg_id))
        else:
            self.subject_group = self.pub.entities['SubjectGroup'][sg_id]
        return

    def check(self):
        self.points.append((10, 'Existential credit'))
        if not self['url'] and not self['doi']:
            self.points.append((-5, 'No link to data (DOI or URL)'))
        if not self.subject_group:
            self.points.append((-1, 'Missing subject group'))
        if not self.acquisition:
            self.points.append((-1, 'Missing acquisition'))
        return

class AnalysisWorkflow(Entity):

    field_defs = (('method', Field, 'Method'), 
                  ('methodurl', URLField, 'Method URL'), 
                  ('software', Field, 'Software'), 
                  ('softwarenitrcid', NITRCIDField, 'NITRC ID'), 
                  ('softwarerrid', RRIDField, 'Software RRID'), 
                  ('softwareurl', URLField, 'Software URL'))

    def check(self):
        self.points.append((7, 'Existential credit'))
        if not self['method']:
            self.points.append((-1, 'Missing method'))
        if not self['methodurl']:
            self.points.append((-2, 'Missing method URL'))
        if not self['software']:
            self.points.append((-1, 'Missing software'))
        if not self['softwarenitrcid'] \
            and not self['softwarerrid'] \
            and not self['softwareurl']:
                self.points.append((-2, 'Missing software link'))
        return

class Observation(Entity):

    field_defs = (('data', MultiField, 'Data'), 
                  ('analysisworkflow', Field, 'Analysis Workflow'), 
                  ('measure', Field, 'Measure'))

    def set_related(self):
        aw_id = self['analysisworkflow']
        if aw_id is None:
            self.analysis_workflow = None
        elif aw_id not in self.pub.entities['AnalysisWorkflow']:
            self.analysis_workflow = None
            err = LinkError('Undefined analysis workflow "%s"' % aw)
            self.errors.append(err)
        else:
            aw = self.pub.entities['AnalysisWorkflow'][aw_id]
            self.analysis_workflow = aw
        self.data = []
        if self['data']:
            for d_id in self['data']:
                if d_id not in self.pub.entities['Data']:
                    self.errors.append(LinkError('Undefined data "%s"' % d_id))
                else:
                    self.data.append(self.pub.entities['Data'][d_id])
        return

    def check(self):
        self.points.append((10, 'Existential credit'))
        if not self['measure']:
            self.points.append((-5, 'Missing measure'))
        if not self.data:
            self.points.append((-2, 'Missing data'))
        if not self.analysis_workflow:
            self.points.append((-2, 'Missing analysis workflow'))
        return

class Model(Entity):

    field_defs = (('type', Field, 'Type'), 
                  ('variable', MultiField, 'Variables'))

    def check(self):
        self.points.append((10, 'Existential credit'))
        # check if any variables are defined
        # check for bad interaction variables
        if not self['type']:
            self.points.append((-4, 'No model type defined'))
        if not self['variable']:
            self.points.append((-4, 'No variables defined'))
        else:
            simple_vars = []
            int_vars = []
            bad_components = set()
            for var in self['variable']:
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

    field_defs = (('observation', MultiField, 'Observations'), 
                  ('model', Field, 'Model'), 
                  ('url', URLField, 'URL'), 
                  ('software', Field, 'Software'))

    def set_related(self):
        m_id = self['model']
        if m_id is None:
            self.model = None
        elif m_id not in self.pub.entities['Model']:
            self.model = None
            self.errors.append(LinkError('Undefined model "%s"' % m_id))
        else:
            self.model = self.pub.entities['Model'][m_id]
        self.observations = []
        if self['observation']:
            for o_id in self['observation']:
                if o_id not in self.pub.entities['Observation']:
                    err = LinkError('Undefined observation "%s"' % o_id)
                    self.errors.append(err)
                else:
                    obs = self.pub.entities['Observation'][o_id]
                    self.observations.append(obs)
        return

    def check(self):
        self.points.append((11, 'Existential credit'))
        if not self['url']:
            self.points.append((-5, 'No link to analysis'))
        if not self['software']:
            self.points.append((-1, 'Missing software'))
        if not self.model:
            self.points.append((-2, 'Missing model'))
        if not self['observation']:
            self.points.append((-2, 'Missing observation(s)'))
        return

class Result(Entity):

    field_defs = (('modelapplication', Field, 'Model Application'), 
                  ('value', Field, 'Value'), 
                  ('variable', MultiField, 'Variables'), 
                  ('f', Field, 'f'), 
                  ('p', Field, 'p'), 
                  ('interpretation', Field, 'Interpretation'))

    def set_related(self):
        ma_id = self['modelapplication']
        if ma_id is None:
            self.model_application = None
        elif ma_id not in self.pub.entities['ModelApplication']:
            self.model_application = None
            err = LinkError('Undefined model application "%s"' % ma_id)
            self.errors.append(err)
        else:
            ma = self.pub.entities['ModelApplication'][ma_id]
            self.model_application = ma
        return

    def check(self):
        self.points.append((23, 'Existential credit'))
        if not self['value']:
            self.points.append((-3, 'Missing "Value"'))
        if not self['f']:
            self.points.append((-2, 'Missing F'))
        if not self['p']:
            self.points.append((-5, 'Missing P'))
        if not self['interpretation']:
            self.points.append((-2, 'Missing interpretation'))
        model_vars = []
        if not self.model_application:
            self.points.append((-5, 'Missing model application'))
        elif self.model_application.model:
            model_vars = self.model_application.model['variable']
        if not self['variable']:
            self.points.append((-5, 'Missing variable(s)'))
        else:
            bad_vars = set()
            for var in self['variable']:
                if var not in model_vars:
                    bad_vars.add(var)
            if bad_vars:
                fmt = 'Variables not defined in the model: %s'
                msg = fmt % ', '.join(sorted(bad_vars))
                self.points.append((-2, msg))
        return

# entities[markup entity type] = entity class
entities = {'SubjectGroup': SubjectGroup, 
            'AcquisitionInstrument': AcquisitionInstrument, 
            'Acquisition': Acquisition, 
            'Data': Data, 
            'AnalysisWorkflow': AnalysisWorkflow, 
            'Observation': Observation, 
            'Model': Model, 
            'ModelApplication': ModelApplication, 
            'Result': Result}

# eof
