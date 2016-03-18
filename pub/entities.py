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

    def check(self):
        self.points.append((3, 'Existential credit'))
        # check for missing fields
        if not self.fields['type'].value:
            self.points.append((-1, 'Missing type'))
        ai = self.fields['acquisitioninstrument'].value
        if not ai:
            self.points.append((-1, 'Missing acquisition instrument'))
        elif ai not in self.pub.entities['AcquisitionInstrument']:
            msg = 'Undefined acquisition instrument "%s"' % ai
            self.errors.append(LinkError(msg))
        return

class Data(Entity):

    field_defs = (('url', URLField, 'URL'), 
                  ('doi', DOIField, 'DOI'), 
                  ('acquisition', Field, 'Acquisition'), 
                  ('subjectgroup', Field, 'Subject Group'))

    def check(self):
        self.points.append((10, 'Existential credit'))
        if not self.fields['url'].value and not self.fields['doi'].value:
            self.points.append((-5, 'No link to data (DOI or URL)'))
        sg = self.fields['subjectgroup'].value
        if not sg:
            self.points.append((-1, 'Missing subject group'))
        elif sg not in self.pub.entities['SubjectGroup']:
            msg = 'Undefined subjectgroup "%s"' % sg
            self.errors.append(LinkError('Undefined subjectgroup "%s"' % sg))
        a = self.fields['acquisition'].value
        if not a:
            self.points.append((-1, 'Missing acquisition'))
        elif a not in self.pub.entities['Acquisition']:
            self.errors.append(LinkError('Undefined acquisition "%s"' % a))
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
        if not self.fields['method'].value:
            self.points.append((-1, 'Missing method'))
        if not self.fields['methodurl'].value:
            self.points.append((-2, 'Missing method URL'))
        if not self.fields['software'].value:
            self.points.append((-1, 'Missing software'))
        if not self.fields['softwarenitrcid'].value \
            and not self.fields['softwarerrid'].value \
            and not self.fields['softwareurl'].value:
                self.points.append((-2, 'Missing software link'))
        return

class Observation(Entity):

    field_defs = (('data', MultiField, 'Data'), 
                  ('analysisworkflow', Field, 'Analysis Workflow'), 
                  ('measure', Field, 'Measure'))

    def check(self):
        self.points.append((10, 'Existential credit'))
        if not self.fields['measure'].value:
            self.points.append((-5, 'Missing measure'))
        if not self.fields['data'].value:
            self.points.append((-2, 'Missing data'))
        else:
            for data in self.fields['data'].value:
                if data not in self.pub.entities['Data']:
                    self.errors.append(LinkError('Undefined data "%s"' % data))
        aw = self.fields['analysisworkflow'].value
        if not aw:
            self.points.append((-2, 'Missing analysis workflow'))
        elif aw not in self.pub.entities['AnalysisWorkflow']:
            err = LinkError('Undefined analysis workflow "%s"' % aw)
            self.errors.append(err)
        return

class Model(Entity):

    field_defs = (('type', Field, 'Type'), 
                  ('variable', MultiField, 'Variables'))

    def check(self):
        self.points.append((10, 'Existential credit'))
        # check if any variables are defined
        # check for bad interaction variables
        if not self.fields['type'].value:
            self.points.append((-4, 'No model type defined'))
        if not self.fields['variable'].value:
            self.points.append((-4, 'No variables defined'))
        else:
            simple_vars = []
            int_vars = []
            bad_components = set()
            for var in self.fields['variable'].value:
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

    def check(self):
        self.points.append((11, 'Existential credit'))
        if not self.fields['url'].value:
            self.points.append((-5, 'No link to analysis'))
        if not self.fields['software'].value:
            self.points.append((-1, 'Missing software'))
        if not self.fields['model'].value:
            self.points.append((-2, 'Missing model'))
        else:
            model = self.fields['model'].value
            if model not in self.pub.entities['Model']:
                self.errors.append(LinkError('Undefined model "%s"' % model))
        if not self.fields['observation'].value:
            self.points.append((-2, 'Missing observation(s)'))
        else:
            for o in self.fields['observation'].value:
                if o not in self.pub.entities['Observation']:
                    err = LinkError('Undefined observation "%s"' % o)
                    self.errors.append(err)
        return

class Result(Entity):

    field_defs = (('modelapplication', Field, 'Model Application'), 
                  ('value', Field, 'Value'), 
                  ('variable', MultiField, 'Variables'), 
                  ('f', Field, 'f'), 
                  ('p', Field, 'p'), 
                  ('interpretation', Field, 'Interpretation'))

    def check(self):
        self.points.append((23, 'Existential credit'))
        if not self.fields['value'].value:
            self.points.append((-3, 'Missing "Value"'))
        if not self.fields['f'].value:
            self.points.append((-2, 'Missing F'))
        if not self.fields['p'].value:
            self.points.append((-5, 'Missing P'))
        if not self.fields['interpretation'].value:
            self.points.append((-2, 'Missing interpretation'))
        ma = self.fields['modelapplication'].value
        if not ma:
            self.points.append((-5, 'Missing model application'))
            model_vars = None
        elif ma not in self.pub.entities['ModelApplication']:
            err = LinkError('Undefined model application "%s"' % ma)
            self.errors.append(err)
            model_vars = None
        else:
            ma_obj = self.pub.entities['ModelApplication'][ma]
            model_id = ma_obj.fields['model'].value
            if not model_id:
                model_vars = None
            elif model_id not in self.pub.entities['Model']:
                model_vars = None
            else:
                model = self.pub.entities['Model'][model_id]
                model_vars = model.fields['variable'].value
        if not self.fields['variable'].value:
            self.points.append((-5, 'Missing variable(s)'))
        else:
            if not model_vars:
                self.points.append((-2, 'No model variables to check against'))
            else:
                bad_vars = set()
                for var in self.fields['variable'].value:
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
