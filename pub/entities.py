from collections import OrderedDict
from . import errors
from .utils import annot_url
from .fields import *

class Entity(object):

    """base class for entities"""

    @classmethod
    def _get_from_def(cls, pub, id, values):
        obj = cls(pub, id)
        for (annotation_id, name, value) in values:
            obj.annotation_ids.add(annotation_id)
            if name in obj.fields:
                obj.fields[name].set(value)
            else:
                err = errors.UnknownFieldError(name)
                obj.errors.append(err)
        return obj

    @classmethod
    def _clear_pmid(cls, pmid, cursor):
        query = "DELETE FROM %s WHERE publication = %%s" % cls.table
        cursor.execute(query, (pmid, ))
        return

    def __init__(self, pub, id):
        self.pub = pub
        self.id = id
        self.annotation_ids = set()
        self.errors = []
        self.points = []
        self.links = []
        self.fields = OrderedDict()
        for (key, cls, display_name) in self.field_defs:
            self.fields[key] = cls(display_name)
        return

    def __getitem__(self, key):
        return self.fields[key].value

    def _insert_annotations(self, cursor):
        query = """INSERT INTO entity_annotation (publication, 
                                                  entity_type, 
                                                  entity_id, 
                                                  annotation_id) 
                   VALUES (%s, %s, %s, %s)"""
        for annotation_id in self.annotation_ids:
            params = (self.pub.pmid, 
                      self.table, 
                      self.id, 
                      annotation_id)
            cursor.execute(query, params)
        return

    def _insert_errors(self, cursor):
        query = """INSERT INTO entity_error (publication, 
                                             entity_type, 
                                             entity_id, 
                                             error_type, 
                                             data) 
                     VALUES (%s, %s, %s, %s, %s)"""
        for error in self.errors:
            if not error.db_error:
                continue
            params = (self.pub.pmid, 
                      self.table, 
                      self.id, 
                      error.__class__.__name__, 
                      error.data)
            cursor.execute(query, params)
        return

    @classmethod
    def _get_annotation_ids_from_db(cls, pub, d, cursor):
        query = """SELECT entity_id, annotation_id 
                     FROM entity_annotation 
                    WHERE publication = %s 
                      AND entity_type = %s"""
        cursor.execute(query, (pub.pmid, cls.table))
        for (entity_id, annotation_id) in cursor:
            d[entity_id].annotation_ids.add(annotation_id)
        return

    @classmethod
    def _get_errors_from_db(cls, pub, d, cursor):
        query = """SELECT entity_id, error_type, data 
                     FROM entity_error 
                    WHERE publication = %s 
                      AND entity_type = %s"""
        cursor.execute(query, (pub.pmid, cls.table))
        for (entity_id, error_type, data) in cursor:
            cls = getattr(errors, error_type)
            err = cls(data)
            d[entity_id].errors.append(err)
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

    @classmethod
    def _get_from_db(cls, pub, cursor):
        d = {}
        query = """SELECT * 
                     FROM subject_group 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        cols = [ el[0] for el in cursor.description ]
        for row in cursor:
            row_dict = dict(zip(cols, row))
            obj = SubjectGroup(pub, row_dict['id'])
            obj.fields['diagnosis'].set(row_dict['diagnosis'])
            obj.fields['nsubjects'].set(row_dict['n_subjects'])
            obj.fields['agemean'].set(row_dict['age_mean'])
            obj.fields['agesd'].set(row_dict['age_sd'])
            d[row_dict['id']] = obj
        SubjectGroup._get_annotation_ids_from_db(pub, d, cursor)
        SubjectGroup._get_errors_from_db(pub, d, cursor)
        return d

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
        self._insert_annotations(cursor)
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

    @classmethod
    def _get_from_db(cls, pub, cursor):
        d = {}
        query = """SELECT * 
                     FROM acquisition_instrument 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        cols = [ el[0] for el in cursor.description ]
        for row in cursor:
            row_dict = dict(zip(cols, row))
            obj = AcquisitionInstrument(pub, row_dict['id'])
            obj.fields['type'].set(row_dict['type'])
            obj.fields['location'].set(row_dict['location'])
            obj.fields['field'].set(row_dict['field'])
            obj.fields['manufacturer'].set(row_dict['manufacturer'])
            obj.fields['model'].set(row_dict['model'])
            d[row_dict['id']] = obj
        AcquisitionInstrument._get_annotation_ids_from_db(pub, d, cursor)
        AcquisitionInstrument._get_errors_from_db(pub, d, cursor)
        return d

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
        self._insert_annotations(cursor)
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

    @classmethod
    def _get_from_db(cls, pub, cursor):
        d = {}
        query = """SELECT * 
                     FROM acquisition 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        cols = [ el[0] for el in cursor.description ]
        for row in cursor:
            row_dict = dict(zip(cols, row))
            obj = Acquisition(pub, row_dict['id'])
            val = row_dict['acquisition_instrument']
            obj.fields['acquisitioninstrument'].set(val)
            obj.fields['type'].set(row_dict['type'])
            obj.fields['nslices'].set(row_dict['n_slice'])
            obj.fields['prep'].set(row_dict['prep'])
            obj.fields['tr'].set(row_dict['tr'])
            obj.fields['te'].set(row_dict['te'])
            obj.fields['ti'].set(row_dict['ti'])
            obj.fields['flipangle'].set(row_dict['flip_angle'])
            obj.fields['fov'].set(row_dict['fov'])
            obj.fields['slicethickness'].set(row_dict['slice_thickness'])
            obj.fields['matrix'].set(row_dict['matrix'])
            obj.fields['nexcitations'].set(row_dict['n_excitations'])
            d[row_dict['id']] = obj
        Acquisition._get_annotation_ids_from_db(pub, d, cursor)
        Acquisition._get_errors_from_db(pub, d, cursor)
        return d

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
        if self.acquisition_instrument:
            ai = self.acquisition_instrument.id
        else:
            ai = None
        params = (self.pub.pmid, 
                  self.id, 
                  ai, 
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
        self._insert_annotations(cursor)
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

    @classmethod
    def _get_from_db(cls, pub, cursor):
        d = {}
        query = """SELECT * 
                     FROM data 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        cols = [ el[0] for el in cursor.description ]
        for row in cursor:
            row_dict = dict(zip(cols, row))
            obj = Data(pub, row_dict['id'])
            obj.fields['url'].set(row_dict['url'])
            obj.fields['doi'].set(row_dict['doi'])
            obj.fields['acquisition'].set(row_dict['acquisition'])
            obj.fields['subjectgroup'].set(row_dict['subject_group'])
            d[row_dict['id']] = obj
        Data._get_annotation_ids_from_db(pub, d, cursor)
        Data._get_errors_from_db(pub, d, cursor)
        return d

    @classmethod
    def _clear_pmid(cls, pmid, cursor):
        query = "DELETE FROM dataXobservation WHERE publication = %s"
        cursor.execute(query, (pmid, ))
        super(Data, cls)._clear_pmid(pmid, cursor)
        return

    def __init__(self, pub, id):
        super(Data, self).__init__(pub, id)
        # set in Observation.set_related()
        self.observations = []
        return

    def _insert(self, cursor):
        query = """INSERT INTO data (publication, 
                                     id, 
                                     acquisition, 
                                     subject_group, 
                                     url, 
                                     doi)
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        if self.acquisition:
            aquisition = self.acquisition.id
        else:
            aquisition = None
        params = (self.pub.pmid, 
                  self.id, 
                  aquisition, 
                  self.subject_group.id, 
                  self['url'], 
                  self['doi'])
        cursor.execute(query, params)
        self._insert_annotations(cursor)
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

    @classmethod
    def _get_from_db(cls, pub, cursor):
        d = {}
        query = """SELECT * 
                     FROM analysis_workflow 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        cols = [ el[0] for el in cursor.description ]
        for row in cursor:
            row_dict = dict(zip(cols, row))
            obj = AnalysisWorkflow(pub, row_dict['id'])
            obj.fields['method'].set(row_dict['method'])
            obj.fields['methodurl'].set(row_dict['methodurl'])
            obj.fields['software'].set(row_dict['software'])
            obj.fields['softwarenitrcid'].set(row_dict['software_nitrc_id'])
            obj.fields['softwarerrid'].set(row_dict['software_rrid'])
            obj.fields['softwareurl'].set(row_dict['software_url'])
            d[row_dict['id']] = obj
        AnalysisWorkflow._get_annotation_ids_from_db(pub, d, cursor)
        AnalysisWorkflow._get_errors_from_db(pub, d, cursor)
        return d

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
        self._insert_annotations(cursor)
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

    @classmethod
    def _get_from_db(cls, pub, cursor):
        d = {}
        query = """SELECT * 
                     FROM observation 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        cols = [ el[0] for el in cursor.description ]
        for row in cursor:
            row_dict = dict(zip(cols, row))
            obj = Observation(pub, row_dict['id'])
            obj.fields['analysisworkflow'].set(row_dict['analysis_workflow'])
            obj.fields['measure'].set(row_dict['measure'])
            d[row_dict['id']] = obj
        query = """SELECT observation, data 
                     FROM dataXobservation 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        for (observation_id, data_id) in cursor:
            d[observation_id].fields['data'].set(data_id)
        Observation._get_annotation_ids_from_db(pub, d, cursor)
        Observation._get_errors_from_db(pub, d, cursor)
        return d

    @classmethod
    def _clear_pmid(cls, pmid, cursor):
        query = "DELETE FROM dataXobservation WHERE publication = %s"
        cursor.execute(query, (pmid, ))
        query = """DELETE FROM observationXmodel_application 
                    WHERE publication = %s"""
        cursor.execute(query, (pmid, ))
        super(Observation, cls)._clear_pmid(pmid, cursor)
        return

    def __init__(self, pub, id):
        super(Observation, self).__init__(pub, id)
        # set in ModelApplication.set_related()
        self.model_applications = []
        return

    def _insert(self, cursor):
        query = """INSERT INTO observation (publication, 
                                            id, 
                                            analysis_workflow, 
                                            measure) 
                   VALUES (%s, %s, %s, %s)"""
        if self.analysis_workflow:
            aw = self.analysis_workflow.id
        else:
            aw = None
        params = (self.pub.pmid, 
                  self.id, 
                  aw, 
                  self['measure'])
        cursor.execute(query, params)
        query = """INSERT INTO dataXobservation (publication, 
                                                 data, 
                                                 observation) 
                   VALUES (%s, %s, %s)"""
        for data in self.data:
            params = (self.pub.pmid, data.id, self.id)
            cursor.execute(query, params)
        self._insert_annotations(cursor)
        self._insert_errors(cursor)
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
    def _get_from_db(cls, pub, cursor):
        d = {}
        query = """SELECT * 
                     FROM model 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        cols = [ el[0] for el in cursor.description ]
        for row in cursor:
            row_dict = dict(zip(cols, row))
            obj = Model(pub, row_dict['id'])
            obj.fields['type'].set(row_dict['type'])
            d[row_dict['id']] = obj
        query = """SELECT model, variable 
                     FROM model_variable 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        for (model_id, variable) in cursor:
            d[model_id].fields['variable'].set(variable)
        Model._get_annotation_ids_from_db(pub, d, cursor)
        Model._get_errors_from_db(pub, d, cursor)
        return d

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
        self._insert_annotations(cursor)
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
    def _get_from_db(cls, pub, cursor):
        d = {}
        query = """SELECT * 
                     FROM model_application 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        cols = [ el[0] for el in cursor.description ]
        for row in cursor:
            row_dict = dict(zip(cols, row))
            obj = ModelApplication(pub, row_dict['id'])
            obj.fields['model'].set(row_dict['model'])
            obj.fields['url'].set(row_dict['url'])
            obj.fields['software'].set(row_dict['software'])
            d[row_dict['id']] = obj
        query = """SELECT observation, model_application 
                     FROM observationXmodel_application 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        for (observation_id, model_application_id) in cursor:
            d[model_application_id].fields['observation'].set(observation_id)
        ModelApplication._get_annotation_ids_from_db(pub, d, cursor)
        ModelApplication._get_errors_from_db(pub, d, cursor)
        return d

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
                                                  model, 
                                                  url, 
                                                  software)
                   VALUES (%s, %s, %s, %s, %s)"""
        if self.model:
            model = self.model.id
        else:
            model = None
        params = (self.pub.pmid, 
                  self.id, 
                  model, 
                  self['url'], 
                  self['software'])
        cursor.execute(query, params)
        query = """INSERT INTO observationXmodel_application 
                               (publication, observation, model_application) 
                   VALUES (%s, %s, %s)"""
        print '=', self.id
        for obs in self.observations:
            print obs.id
            params = (self.pub.pmid, obs.id, self.id)
            cursor.execute(query, params)
        self._insert_annotations(cursor)
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
    def _get_from_db(cls, pub, cursor):
        d = {}
        query = """SELECT * 
                     FROM result 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        cols = [ el[0] for el in cursor.description ]
        for row in cursor:
            row_dict = dict(zip(cols, row))
            obj = Result(pub, row_dict['id'])
            obj.fields['modelapplication'].set(row_dict['model_application'])
            obj.fields['value'].set(row_dict['value'])
            obj.fields['f'].set(row_dict['f'])
            obj.fields['p'].set(row_dict['p'])
            obj.fields['interpretation'].set(row_dict['interpretation'])
            d[row_dict['id']] = obj
        query = """SELECT result, variable 
                     FROM result_variable 
                    WHERE publication = %s"""
        cursor.execute(query, (pub.pmid, ))
        for (result_id, variable) in cursor:
            d[result_id].fields['variable'].set(variable)
        Result._get_annotation_ids_from_db(pub, d, cursor)
        Result._get_errors_from_db(pub, d, cursor)
        return d

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
        if self.model_application:
            ma = self.model_application.id
        else:
            ma = None
        params = (self.pub.pmid, 
                  self.id, 
                  ma, 
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
        self._insert_annotations(cursor)
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
