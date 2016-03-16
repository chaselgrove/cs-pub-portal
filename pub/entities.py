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

    fields = OrderedDict((('diagnosis', Field('Diagnosis')), 
                          ('nsubjects', Field('Subjects')), 
                          ('agemean', Field('Age mean')), 
                          ('agesd', Field('Age SD'))))

    def check(self):
        self.points.append((5, 'Just for being'))
        # check for missing fields
        for (name, field) in self.fields.iteritems():
            if not field.value:
                self.points.append((-1, 'Missing %s' % name))
        return

class AcquisitionInstrument(Entity):

    fields = OrderedDict((('type', Field('Type')), 
                          ('location', Field('Location')), 
                          ('field', Field('Field')), 
                          ('manufacturer', Field('Manufacturer')), 
                          ('model', Field('Model'))))

    def check(self):
        self.points.append((7, 'Just for being'))
        # check for missing fields
        for (name, field) in self.fields.iteritems():
            if not field.value:
                if name == 'field':
                    self.points.append((-2, 'Missing %s' % name))
                else:
                    self.points.append((-1, 'Missing %s' % name))
        return

class Acquisition(Entity):

    fields = OrderedDict((('type', Field('Type')), 
                          ('acquisitioninstrument', 
                           Field('Acquisition Instrument'))))

    def check(self):
        self.points.append((3, 'Just for being'))
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

    fields = OrderedDict((('url', URLField('URL')), 
                          ('doi', DOIField('DOI')), 
                          ('acquisition', Field('Acquisition')), 
                          ('subjectgroup', Field('Subject Group'))))

    def check(self):
        self.points.append((10, 'Just for being'))
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

    fields = OrderedDict((('method', Field('Method')), 
                          ('methodurl', URLField('Method URL')), 
                          ('software', Field('Software'))))

    def check(self):
        self.points.append((5, 'Just for being'))
        if not self.method:
            self.points.append((-1, 'Missing method'))
        if not self.methodurl:
            self.points.append((-2, 'Missing method URL'))
        if not self.software:
            self.points.append((-1, 'Missing software'))
        for (name, field) in self.fields.iteritems():
            if not field.value:
                if name == 'methodurl':
                    self.points.append((-2, 'Missing %s' % name))
                else:
                    self.points.append((-1, 'Missing %s' % name))
        return

class Observation(Entity):

    fields = OrderedDict((('data', MultiField('Data')), 
                          ('analysisworkflow', Field('Analysis Workflow')), 
                          ('measure', Field('Measure'))))

    def check(self):
        self.points.append((10, 'Just for being'))
        if not self.fields['measure'].value:
            self.points.append((-5, 'No measure'))
        if not self.fields['data'].value:
            self.points.append((-2, 'Missing data'))
        else:
            for data in self.fields['data'].value:
                if data not in self.pub.entities['Data']:
                    self.errors.append(LinkError('Undefined data %s' % data))
        aw = self.fields['analysisworkflow'].value
        if not aw:
            self.points.append((-2, 'Missing analysis workflow'))
        elif aw not in self.pub.entities['AnalysisWorkflows']:
            self.errors.append(LinkError('Undefined analysis workflow %s' % aw))
        return

class Model(Entity):

    fields = OrderedDict((('variable', MultiField('Variables')),))

    def check(self):
        self.points.append((5, 'Just for being'))
        # check if any variables are defined
        # check for bad interaction variables
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

    fields = OrderedDict((('observation', MultiField('Observations')), 
                          ('model', Field('Model')), 
                          ('url', URLField('URL')), 
                          ('software', Field('Software'))))

    def check(self):
        self.points.append((11, 'Just for being'))
        if not self.fields['url'].value:
            self.points.append((-5, 'No link to analysis'))
        if not self.fields['software'].value:
            self.points.append((-1, 'Software undefined'))
        if not self.fields['model'].value:
            self.points.append((-2, 'Model undefined'))
        else:
            model = self.fields['model'].value
            if model not in self.pub.entities['Model']:
                self.errors.append(LinkError('Undefined model %s' % model))
        if not self.fields['observation'].value:
            self.points.append((-2, 'No observations defined'))
        else:
            for o in self.fields['observation'].value:
                if o not in self.pub.entities['Observation']:
                    err = LinkError('Undefined observation "%s"' % o)
                    self.errors.append(err)
        return

class Result(Entity):

    fields = OrderedDict((('modelapplication', Field('Model Application')), 
                          ('value', Field('Value')), 
                          ('variables', MultiField('Variables')), 
                          ('f', Field('f')), 
                          ('p', Field('p')), 
                          ('interpretation', Field('Interpretation'))))

    def check(self):
        self.points.append((23, 'Just for being'))
        if not self.fields['value'].value:
            self.points.append((-3, 'Value undefined'))
        if not self.fields['f'].value:
            self.points.append((-2, 'F undefined'))
        if not self.fields['p'].value:
            self.points.append((-5, 'P undefined'))
        if not self.fields['interpretation'].value:
            self.points.append((-2, 'Interpretation undefined'))
        ma = self.fields['modelapplication'].value
        if not ma:
            self.points.append((-5, 'No model application given'))
            model_vars = None
        elif ma not in self.pub.entities['ModelApplication']:
            self.errors.append(LinkError('Undefined model application %s' % ma))
            model_vars = None
        else:
            ma_obj = self.pub.entities['ModelApplication'][ma]
            m = ma_obj.fields['model'].value
            if not m:
                model_vars = None
            elif m not in self.pub.entities['Model']:
                model_vars = None
            else:
                model_vars = self.pub.entities['Model'][m]
        if not self.fields['variables'].value:
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
