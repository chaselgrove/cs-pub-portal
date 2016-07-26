from collections import OrderedDict
from . import errors
from .utils import annot_url
from .fields import *

class Entity(object):

    """base class for entities"""

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
                err = errors.UnknownFieldError(name)
                self.errors.append(err)
        return

    def __getitem__(self, key):
        return self.fields[key].value

    @classmethod
    def _clear_pmid(cls, pmid, cursor):
        query = "DELETE FROM %s WHERE publication = %%s" % cls.table
        cursor.execute(query, (pmid, ))
        return

    def _insert_errors(self, cursor):
        query = """INSERT INTO entity_error (publication, 
                                             entity_type, 
                                             entity_id, 
                                             error_type, 
                                             data) 
                     VALUES (%s, %s, %s, %s, %s)"""
        for error in self.errors:
            params = (self.pub.pmid, 
                      self.table, 
                      self.id, 
                      error.__class__.__name__, 
                      error.data)
            cursor.execute(query, params)
        return

    def set_related(self):
        """set related entities"""
        return

    def get_scores(self):
        """obj.get_scores() -> (score, maximum possible score)"""
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

    table = 'subject_group'

    def _insert(self, cursor):
        query = """INSERT INTO subject_group (publication, 
                                              id, 
                                              diagnosis, 
                                              n_subjects, 
                                              age_mean, 
                                              age_sd)
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        params = (self.pub.pmid, 
                  self.id, 
                  self['diagnosis'], 
                  self['nsubjects'], 
                  self['agemean'], 
                  self['agesd'])
        cursor.execute(query, params)
        self._insert_errors(cursor)
        return



    def score(self):
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

    table = 'acquisition_instrument'

    def _insert(self, cursor):
        query = """INSERT INTO acquisition_instrument (publication, 
                                                       id, 
                                                       type, 
                                                       location, 
                                                       field, 
                                                       manufacturer, 
                                                       model)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        params = (self.pub.pmid, 
                  self.id, 
                  self['type'], 
                  self['location'], 
                  self['field'], 
                  self['manufacturer'], 
                  self['model'])
        cursor.execute(query, params)
        self._insert_errors(cursor)
        return

    def score(self):
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
                  ('nslices', Field, 'N Slices'), 
                  ('prep', Field, 'Prep'), 
                  ('tr', Field, 'TE'), 
                  ('te', Field, 'TR'), 
                  ('ti', Field, 'TI'), 
                  ('flipangle', Field, 'Flip Angle'), 
                  ('fov', Field, 'FOV'), 
                  ('slicethickness', Field, 'Slice Thickness'), 
                  ('matrix', Field, 'Matrix'), 
                  ('nexcitations', Field, 'N Excitations'))

    table = 'acquisition'

    def _insert(self, cursor):
        query = """INSERT INTO acquisition (publication, 
                                            id, 
                                            acquisition_instrument, 
                                            type, 
                                            n_slice, 
                                            prep, 
                                            tr, 
                                            te, 
                                            ti, 
                                            flip_angle, 
                                            fov, 
                                            slice_thickness, 
                                            matrix, 
                                            n_excitations)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 
                           %s, %s, %s, %s, %s, %s, %s)"""
        params = (self.pub.pmid, 
                  self.id, 
                  self['acquisitioninstrument'], 
                  self['type'], 
                  self['nslices'], 
                  self['prep'], 
                  self['tr'], 
                  self['te'], 
                  self['ti'], 
                  self['flipangle'], 
                  self['fov'], 
                  self['slicethickness'], 
                  self['matrix'], 
                  self['nexcitations'])
        cursor.execute(query, params)
        self._insert_errors(cursor)
        return

    def set_related(self):
        ai_id = self['acquisitioninstrument']
        if ai_id is None:
            self.acquisition_instrument = None
        elif ai_id not in self.pub.entities['AcquisitionInstrument']:
            self.acquisition_instrument = None
            msg = 'Undefined acquisition instrument "%s"' % ai_id
            self.errors.append(errors.LinkError(msg))
        else:
            ai = self.pub.entities['AcquisitionInstrument'][ai_id]
            self.acquisition_instrument = ai
        return

    def score(self):
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

    table = 'data'

    def __init__(self, pub, id, values):
        Entity.__init__(self, pub, id, values)
        # set in Observation.set_related()
        self.observations = []
        return

    @classmethod
    def _clear_pmid(cls, pmid, cursor):
        query = "DELETE FROM dataXobservation WHERE publication = %s"
        cursor.execute(query, (pmid, ))
        super(Data, cls)._clear_pmid(pmid, cursor)
        return

    def _insert(self, cursor):
        query = """INSERT INTO data (publication, 
                                     id, 
                                     acquisition, 
                                     subject_group, 
                                     url, 
                                     doi)
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        params = (self.pub.pmid, 
                  self.id, 
                  self.acquisition.id, 
                  self.subject_group.id, 
                  self['url'], 
                  self['doi'])
        cursor.execute(query, params)
        self._insert_errors(cursor)
        return

    def set_related(self):
        a_id = self['acquisition']
        if a_id is None:
            self.acquisition = None
        elif a_id not in self.pub.entities['Acquisition']:
            self.acquisition = None
            err = errors.LinkError('Undefined acquisition "%s"' % a_id)
            self.errors.append(err)
        else:
            self.acquisition = self.pub.entities['Acquisition'][a_id]
        sg_id = self['subjectgroup']
        if sg_id is None:
            self.subject_group = None
        if sg_id not in self.pub.entities['SubjectGroup']:
            self.subject_group = None
            err = LinkError('Undefined subjectgroup "%s"' % sg_id)
            self.errors.append(err)
        else:
            self.subject_group = self.pub.entities['SubjectGroup'][sg_id]
        return

    def score(self):
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

    table = 'analysis_workflow'

    def _insert(self, cursor):
        query = """INSERT INTO analysis_workflow (publication, 
                                                  id, 
                                                  method, 
                                                  methodurl, 
                                                  software, 
                                                  software_nitrc_id, 
                                                  software_rrid, 
                                                  software_url)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        params = (self.pub.pmid, 
                  self.id, 
                  self['method'], 
                  self['methodurl'], 
                  self['software'], 
                  self['softwarenitrcid'], 
                  self['softwarerrid'], 
                  self['softwareurl'])
        cursor.execute(query, params)
        self._insert_errors(cursor)
        return

    def score(self):
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

    table = 'observation'

    def __init__(self, pub, id, values):
        Entity.__init__(self, pub, id, values)
        # set in ModelApplication.set_related()
        self.model_applications = []
        return

    def _insert(self, cursor):
        query = """INSERT INTO observation (publication, 
                                            id, 
                                            analysis_workflow, 
                                            measure) 
                   VALUES (%s, %s, %s, %s)"""
        params = (self.pub.pmid, 
                  self.id, 
                  self['analysisworkflow'], 
                  self['measure'])
        cursor.execute(query, params)
        query = """INSERT INTO dataXobservation (publication, 
                                                 data, 
                                                 observation) 
                   VALUES (%s, %s, %s)"""
        for data in self.data:
            params = (self.pub.pmid, data.id, self.id)
            cursor.execute(query, params)
        self._insert_errors(cursor)
        return

    @classmethod
    def _clear_pmid(cls, pmid, cursor):
        query = "DELETE FROM dataXobservation WHERE publication = %s"
        cursor.execute(query, (pmid, ))
        query = """DELETE FROM observationXmodel_application 
                    WHERE publication = %s"""
        cursor.execute(query, (pmid, ))
        super(Observation, cls)._clear_pmid(pmid, cursor)
        return

    def set_related(self):
        aw_id = self['analysisworkflow']
        if aw_id is None:
            self.analysis_workflow = None
        elif aw_id not in self.pub.entities['AnalysisWorkflow']:
            self.analysis_workflow = None
            err = errors.LinkError('Undefined analysis workflow "%s"' % aw)
            self.errors.append(err)
        else:
            aw = self.pub.entities['AnalysisWorkflow'][aw_id]
            self.analysis_workflow = aw
        self.data = []
        if self['data']:
            for d_id in self['data']:
                if d_id not in self.pub.entities['Data']:
                    err = errors.LinkError('Undefined data "%s"' % d_id)
                    self.errors.append(err)
                else:
                    d = self.pub.entities['Data'][d_id]
                    self.data.append(d)
                    d.observations.append(self)
        return

    def score(self):
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

    table = 'model'

    @classmethod
    def _clear_pmid(cls, pmid, cursor):
        query = "DELETE FROM model_variable WHERE publication = %s"
        cursor.execute(query, (pmid, ))
        super(Model, cls)._clear_pmid(pmid, cursor)
        return

    def _insert(self, cursor):
        query = "INSERT INTO model (publication, id, type) VALUES (%s, %s, %s)"
        params = (self.pub.pmid, self.id, self['type'])
        cursor.execute(query, params)
        if self['variable'] is not None:
            query = """INSERT INTO model_variable (publication, 
                                                   model, 
                                                   variable) 
                       VALUES (%s, %s, %s)"""
            for val in self['variable']:
                params = (self.pub.pmid, self.id, val)
                cursor.execute(query, params)
        self._insert_errors(cursor)
        return

    def score(self):
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

    table = 'model_application'

    @classmethod
    def _clear_pmid(cls, pmid, cursor):
        query = """DELETE FROM observationXmodel_application 
                    WHERE publication = %s"""
        cursor.execute(query, (pmid, ))
        super(ModelApplication, cls)._clear_pmid(pmid, cursor)
        return

    def _insert(self, cursor):
        query = """INSERT INTO model_application (publication, 
                                                  id, 
                                                  url, 
                                                  software)
                   VALUES (%s, %s, %s, %s)"""
        params = (self.pub.pmid, 
                  self.id, 
                  self['url'], 
                  self['software'])
        cursor.execute(query, params)
        query = """INSERT INTO observationXmodel_application 
                               (publication, observation, model_application) 
                   VALUES (%s, %s, %s)"""
        for obs in self.observations:
            params = (self.pub.pmid, obs.id, self.id)
            cursor.execute(query, params)
        self._insert_errors(cursor)
        return

    def set_related(self):
        m_id = self['model']
        if m_id is None:
            self.model = None
        elif m_id not in self.pub.entities['Model']:
            self.model = None
            self.errors.append(errors.LinkError('Undefined model "%s"' % m_id))
        else:
            self.model = self.pub.entities['Model'][m_id]
        self.observations = []
        if self['observation']:
            for o_id in self['observation']:
                if o_id not in self.pub.entities['Observation']:
                    err = errors.LinkError('Undefined observation "%s"' % o_id)
                    self.errors.append(err)
                else:
                    obs = self.pub.entities['Observation'][o_id]
                    self.observations.append(obs)
                    obs.model_applications.append(self)
        return

    def score(self):
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

    table = 'result'

    @classmethod
    def _clear_pmid(cls, pmid, cursor):
        query = "DELETE FROM result_variable WHERE publication = %s"
        cursor.execute(query, (pmid, ))
        super(Result, cls)._clear_pmid(pmid, cursor)
        return

    def _insert(self, cursor):
        query = """INSERT INTO result (publication, 
                                       id, 
                                       model_application, 
                                       value, 
                                       f, 
                                       p, 
                                       interpretation) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        params = (self.pub.pmid, 
                  self.id, 
                  self['modelapplication'], 
                  self['value'], 
                  self['f'], 
                  self['p'], 
                  self['interpretation'])
        cursor.execute(query, params)
        if self['variable'] is not None:
            query = """INSERT INTO result_variable (publication, 
                                                    result, 
                                                    variable) 
                       VALUES (%s, %s, %s)"""
            for val in self['variable']:
                params = (self.pub.pmid, self.id, val)
                cursor.execute(query, params)
        self._insert_errors(cursor)
        return

    def set_related(self):
        ma_id = self['modelapplication']
        if ma_id is None:
            self.model_application = None
        elif ma_id not in self.pub.entities['ModelApplication']:
            self.model_application = None
            err = errors.LinkError('Undefined model application "%s"' % ma_id)
            self.errors.append(err)
        else:
            ma = self.pub.entities['ModelApplication'][ma_id]
            self.model_application = ma
        return

    def score(self):
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
# this order propagates to Publication.entities, whose order is used to put 
# the entities in the database
entities = OrderedDict()
entities['SubjectGroup'] = SubjectGroup
entities['AcquisitionInstrument'] = AcquisitionInstrument
entities['Acquisition'] = Acquisition
entities['Data'] = Data
entities['AnalysisWorkflow'] = AnalysisWorkflow
entities['Observation'] = Observation
entities['Model'] = Model
entities['ModelApplication'] = ModelApplication
entities['Result'] = Result

# eof
