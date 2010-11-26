# -* encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################################

from osv import osv, fields
import netsvc
import random
import datetime
import tools
from tools.translate import _
import time
import os
import pooler
from training.training import training_course_kind_compute

FMT = '%Y-%m-%d %H:%M:%S'


class training_course_type(osv.osv):
    _inherit = 'training.course_type'

    _columns = {
        'exam_product_id' : fields.many2one('product.product', 'Exam'),
    }
training_course_type()

class training_config_contact_function(osv.osv):
    _inherit = 'training.config.contact.function'

    def _get_values_of_kind(self):
        return [('standard', 'Course'),('exam', 'Exam')]

training_config_contact_function()

class training_session(osv.osv):
    _inherit = 'training.session'

    def _create_seance(self, cr, uid, session, context=None):
        if session.kind == 'exam':
            group_proxy = self.pool.get('training.group')
            group_ids = group_proxy.search(cr, uid, [('session_id', '=', session.id)])
            if group_ids:
                group_id = group_ids[0]
            else:
                group_id = group_proxy.create(cr, uid, {'name' : _('Class %d') % (1,), 'session_id': session.id}, context=context)

            seance_proxy = self.pool.get('training.seance')
            seance_id = seance_proxy.create(cr, uid, {
                'name' : _("Exam"),
                'original_session_id' : session.id,
                'min_limit' : 1,
                'max_limit' : 100,
                'user_id' : session.user_id.id,
                'date' : session.date,
                'kind' : 'exam',
                'group_id' : group_id,
                'duration' : 3.0,
            })
            return [seance_id]
        else:
            return super(training_session, self)._create_seance(cr, uid, session, context=context)

training_session()

class training_seance(osv.osv):
    _inherit = 'training.seance'

    _columns = {
        'kind' : fields.selection(
            training_course_kind_compute,
            'Kind',
            required=True,
            select=1,
            ),
    }

    def _create_participation(self, cr, uid, seance, subscription_line, context=None):
        participation = super(training_seance, self)._create_participation(cr, uid, seance, subscription_line, context)

        t_part_proxy = self.pool.get('training.participation')

        if subscription_line.session_id.kind == 'exam':
            # for exam session, we must have a course_id on the subscription line
            if not subscription_line.course_id:
                raise osv.except_osv(_('Warning'),
                                     _('You have selected an exam seance but there is no associated course'))
            t_part_proxy.write(cr, uid, [participation], {'course_questionnaire_id': subscription_line.course_id.id})

        elif seance.kind == 'exam':
            # subscription is not on a exam session, but this seance is an exam
            # so the exam participation with be taken on course from this seance
            t_part_proxy.write(cr, uid, [participation], {'course_questionnaire_id': seance.course_id.id})

#XXX: Code comment as of 20100330, participation now only have
#     course_questionnaire_id affected, questionnaire_id is affected
#     when original exam sheet is printed
#            q_proxy = self.pool.get('training.exam.questionnaire')
#            q_ids = q_proxy.search(cr, uid,
#                                   [('course_id', '=', subscription_line.course_id.id),
#                                    ('state', 'in', ('deprecated', 'validated'))],
#                                    context=context)
#            if not q_ids:
#                raise osv.except_osv(_('Warning'),
#                                     _("There is not an available questionnaire for the following course %s")
#                                        % subscription_line.course_id.name)
#
#            proxy = self.pool.get('training.participation')
#            proxy.write(cr, uid, [participation], {'course_questionnaire_id': random.choice(q_ids)}, context=context)
#XXX: End of code comment as of 20100330
        return participation

    def action_create_procurements(self, cr, uid, ids, context=None):
        if not ids:
            return False

        wf_service = netsvc.LocalService("workflow")

        # For each seance, we will create a procurement for each product
        for seance in self.browse(cr, uid, ids, context=context):
            if seance.kind == 'exam':
                continue
            else:
                super(training_seance, self).action_create_procurements(cr, uid, [seance.id], context=context)

        return True


    def search(self, cr, uid, domain, offset=0, limit=None, order=None, context=None, count=False):
        request_session_id = context and context.get('request_session_id', False) or False

        if request_session_id:
            session = self.pool.get('training.session').browse(cr, uid, request_session_id, context=context)

            if session.kind == 'exam':
                return [seance.id for seance in session.seance_ids]

        return super(training_seance, self).search(cr, uid, domain, offset=offset,
                                                   limit=limit, order=order, context=context, count=count)

    def _get_product(self, cr, uid, ids, context=None):
        assert len(ids) == 1
        seance = self.browse(cr, uid, ids[0], context)

        if seance.kind == 'exam':
            # FIXME: Hard coded !!!
            product_proxy = self.pool.get('product.product')
            product_ids = product_proxy.search(cr, uid, [('default_code', '=', 'R50H')], context=context)
            if not product_ids:
                raise osv.except_osv(_('Error'),
                                     _('There is no product with the code equal to R50H !'))
            return product_proxy.browse(cr, uid, product_ids[0], context=context)
        else:
            return super(training_seance, self)._get_product(cr, uid, ids, context=context)
training_seance()

class exam_questionnaire(osv.osv):
    _name = 'training.exam.questionnaire'

exam_questionnaire()

class training_course(osv.osv):
    _inherit = 'training.course'

    def search(self, cr, uid, domain, offset=0, limit=None, order=None, context=None, count=False):
        # If search is done from the "Add Questions" button on
        # "Questionnaires", filter course add to only display courses
        # added to this questionnaire
        if context \
            and 'quizz_search' in context \
            and 'active_id' in context:

            qc_course_ids = set()
            qc_proxy = self.pool.get('training.exam.questionnaire.course')
            qc_search = [('questionnaire_id','=',context['active_id'])]
            qc_ids = qc_proxy.search(cr, uid, qc_search, context=context)

            for qc in qc_proxy.browse(cr, uid, qc_ids):
                qc_course_ids.add(qc.course_id.id)

            domain.append(('id','in',list(qc_course_ids)))
        return super(training_course, self).search(cr, uid, domain, offset, limit, order, context, count)

    def _has_questionnaire_compute(self, cr, uid, ids, fieldnames, args, context=None):
        q_proxy = self.pool.get('training.exam.questionnaire')
        qc_proxy = self.pool.get('training.exam.questionnaire.course')
        res = dict.fromkeys(ids, False)

        for obj in self.browse(cr, uid, ids, context=context):
            qc_ids = qc_proxy.search(cr, uid, [('course_id', '=', obj.id)], context=context)
            q_ids = [qc.questionnaire_id.id for qc in qc_proxy.browse(cr, uid, qc_ids, context=context)]
            res[obj.id] = len(q_proxy.search(cr, uid, [('id', 'in', q_ids),('state', 'in', ('deprecated', 'validated'))], context=context)) > 0

        return res

    def _get_questionnaires(self, cr, uid, ids, context=None):
        res = set()
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.main_course_id:
                res.add(obj.main_course_id.id)
            for c in obj.course_ids:
                res.add(c.course_id.id)
        return list(res)


    _columns = {
        'questionnaire_ids' : fields.many2many('training.exam.questionnaire',
                                              'training_exam_questionnaire_courses_rel',
                                              'course_id',
                                              'questionnaire_id',
                                              string='Questionnaire'),
        'has_questionnaire' : fields.function(_has_questionnaire_compute,
                                              method=True,
                                              string='Has Questionnaires',
                                              type='boolean',
                                              store= { 'training.exam.questionnaire' : (_get_questionnaires, None, 10) }
                                             ),
    }

training_course()

class training_offer(osv.osv):
    _inherit = 'training.offer'

    _columns = {
        'questionnaire_ids' : fields.many2many('training.course',
                                               'training_questionnaire_offer_rel',
                                               'offer_id',
                                               'questionnaire_id',
                                               'Exams',
                                               domain=[('has_questionnaire', '=', True)]),
    }

training_offer()

class training_exam_question(osv.osv):
    _name = 'training.exam.question'

training_exam_question()

class training_exam_questionnaire_question(osv.osv):
    _name = 'training.exam.questionnaire.question'

    _columns = {
        'sequence' : fields.integer('Sequence'),

        'question_id' : fields.many2one('training.exam.question', 'Question', required=True),
        'question_type' : fields.related('question_id', 'type',
                                         type='selection',
                                         selection=[('qcm', 'QCM'),
                                                    ('qcu', 'QCU'),
                                                    ('plain', 'Plain'),
                                                    ('yesno', 'Yes/No') ],
                                         string='Type',
                                         readonly=True,
                                        ),
        'question_exposition' : fields.related('question_id', 'question',
                                               type='text',
                                               string='Exposition',
                                               readonly=True),

        'questionnaire_id' : fields.many2one('training.exam.questionnaire', 'Questionnaire', required=True, ondelete='cascade'),
    }

    _order = 'sequence asc'

training_exam_questionnaire_question()


class training_question(osv.osv):
    _name = 'training.exam.question'
    _description = 'Training Exam Question'

    def _number_of_good_answer(self, cr, uid, ids, name, args, context=None):
        values = dict.fromkeys(ids, 0)
        for obj in self.browse(cr, uid, ids, context=None):
            if obj.type in ('qcm', 'qcu'):
                if obj.question_answer_ids:
                    values[obj.id] = reduce(lambda prev, curr: prev + int(curr.is_solution == 'yes'), obj.question_answer_ids, 0)
            else:
                values[obj.id] = 1
        return values

    _columns = {
        'name' : fields.char('Name',
                             size=128,
                             required=True,
                             select=1,
                             help='Name of Question'),
        'question' : fields.text('Question',
                                 required=True,
                                 select=1),
        'is_mandatory' : fields.boolean('Mandatory',
                                        help='Question is mandatory or not'),
        'is_eliminatory' : fields.boolean('Eliminatory'),
        'note' : fields.text('Note'),
        'type' : fields.selection(
            [('qcm', 'QCM'),
             ('qcu', 'QCU'),
             ('plain', 'Plain'),
             ('yesno', 'Yes/No') ],
            'Type',
            required=True,
            select=1, help='Question type'),
        'number_of_good_answers' : fields.function(_number_of_good_answer, method=True,
                                                   string='Number of Good Answers',
                                                   type='integer'),
        'response_plain' : fields.text('Solution'),
        'response_yesno' : fields.selection([('yes', 'Yes'),('no', 'No')], 'Solution'),
        'question_answer_ids' : fields.one2many('training.exam.question.answer', 'question_id', 'Solution'),
        'questionnaire_ids': fields.many2many('training.exam.questionnaire',
                                              'training_exam_questionnaire_question',
                                              'question_id',
                                              'questionnaire_id',
                                              'Questionnaire', readonly=True),
        'course_ids' : fields.many2many('training.course',
                                        'training_question_course_rel',
                                        'question_id',
                                        'course_id',
                                        'Courses',
                                        select=1),
        'point' : fields.float('Point', digits=(12,2),
                                 required=True,
                                 help='Point related to question'),
        'duration': fields.float('Duration',
                                 required=True,
                                 help='Time related to question'),
        'image': fields.binary('Image',
                               help='Image to be display next to question text'),
        'image_position': fields.selection(
                        [('before_text', 'Before text'),
                         ('after_text', 'After text')],
                        'Image Position',
                        ),
        # plain question
        'free_lines_count': fields.integer('Free Lines', help='How many free line available to formulate a response to a plain question'),

        # states
        'state': fields.selection([
            ('draft', 'Draft'),
            ('validated', 'Validated'),
            ('deprecated', 'Deprecated'),
        ], 'State', required=True, readonly=True, select=1),
    }

    def mark_related_questionnaires_pending(self, cr, uid, ids, context=None):
#        workflow = netsvc.LocalService('workflow')
        for question in self.browse(cr, uid, ids, context=context):
            for quizz in question.questionnaire_ids:
                if quizz.state == 'validated':
                    quizz.set_pending_status()
#                    print("VALIDATE: %s / %s / %s" % (quizz._name, quizz.id, 'signal_teq_pending'))
#                    r = workflow.trg_validate(uid, quizz._name, quizz.id, 'signal_teq_pending', cr)
#                    return(">>> %s" % (str(r)))

    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'})
        return True

    def action_draft_validate(self, cr, uid, ids, context=None):
        self.mark_related_questionnaires_pending(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'draft'})
        return True

    def action_validate(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'validated'})
        return True

    def action_deprecate(self, cr, uid, ids, context=None):
        self.mark_related_questionnaires_pending(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'deprecated'})
        return True

    def write(self, cr, uid, ids, vals, context=None):
        do_vals_validation = False
        for q in self.browse(cr, uid, ids, context=context):
            if q.state == 'validated':
                do_vals_validation = True
                break
        # let workflow work correctly
        if len(vals.keys()) == 1 and 'state' in vals:
            do_vals_validation = False

        if do_vals_validation:
            authz_fields = set(['name','question','question_answer_ids'])
            for k in vals.iterkeys():
                if k not in authz_fields:
                    raise osv.except_osv(_('Error'), _('Cannot modify important field of a question which is validated'))
            answers = []
            for a in vals.get('question_answer_ids',[]):
                if len(a) == 3 and a[0] == 1:
                    del a[2]['is_solution']
                    answers.append(a)
            vals['question_answer_ids'] = answers

        return super(training_question, self).write(cr, uid, ids, vals, context=context)

    def _name_default(self, cr, uid, ids, context=None):
        return self.pool.get('ir.sequence').get(cr, uid, 'training.exam.questionnaire')

    _defaults = {
        'name' : _name_default,
        'is_mandatory' : lambda *a: 0,
        'is_eliminatory' : lambda *a: 0,
        'type' : lambda *a: 'plain',
        'response_yesno' : lambda *a: 0,
        'point' : lambda *a: 0,
        'duration':lambda *a: 1.0,
        'free_lines_count': lambda *a: 10,
        'state': lambda *a: 'draft',
    }

    def _check_point(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        return obj.point > 0

    def _check_answer(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)

        if obj.type == 'qcm' and obj.number_of_good_answers:
            return  obj.number_of_good_answers >=1

        elif obj.type =='qcu':
            return  obj.number_of_good_answers == 1

        return  True

    _constraints = [
        (_check_point, "Can you check the point of your question ?", ['point']),
        (_check_answer, "Can you check your type and the solution", ['number_of_good_answers']),
    ]

    def search(self, cr, uid, domain, offset=0, limit=None, order=None, context=None, count=False):
        course_id = context and context.get('course_id', False) or False
        kind = context and context.get('kind', False) or False
        without_course = context and context.get('course', False) or False

        if without_course:
            cr.execute("SELECT id "
                       "FROM training_exam_question "
                       "WHERE id NOT IN ( SELECT question_id FROM training_question_course_rel)")

            return [x[0] for x in cr.fetchall()]

        # Used by the Generator of Questionnaire
        if course_id and kind:
            values = ['qcm', 'qcu', 'yesno']

            if kind == 'manual':
                values.append('plain')

            cr.execute(
                "SELECT tqcr.question_id "
                "FROM training_question_course_rel tqcr, training_exam_question tq "
                "WHERE tq.id = tqcr.question_id "
                "  AND tqcr.course_id = %s "
                "  AND tq.type in (" + ",".join(['%s'] * len(values)) + ")",
                [course_id] + values,
            )

            return [x[0] for x in cr.fetchall()]

        questionnaire_id = context and context.get('questionnaire_id', False) or False
        if questionnaire_id:
            course_id = self.pool.get('training.exam.questionnaire').browse(cr, uid, questionnaire_id).course_id.id

        if course_id:
            cr.execute("SELECT question_id FROM training_question_course_rel WHERE course_id = %s",
                       (course_id,))

            domain.append(('id','in',[ x[0] for x in cr.fetchall() ]))

        return super(training_question, self).search(cr,
                                                     uid,
                                                     domain,
                                                     offset=offset,
                                                     limit=limit,
                                                     order=order,
                                                     context=context,
                                                     count=count)

training_question()

class training_question_answer(osv.osv):
    _name = 'training.exam.question.answer'
    _description = 'Training Question Answer'
    _columns = {
        'name' : fields.text('Solution', required=True, select=1),
        'is_solution' : fields.selection([('yes', 'Yes'),('no', 'No')], 'Acceptable Solution', required=True),
        'question_id' : fields.many2one('training.exam.question',
                                        'Question',
                                        select=True,
                                        required=True,
                                        ondelete="cascade"),
    }

training_question_answer()

class training_exam_questionnaire_course(osv.osv):
    _name = 'training.exam.questionnaire.course'
    _description = 'Training Exam Questionnaire Course'
    _rec_name = 'course_id'

    def f_total_point(self, cr, uid, ids, fn, args, context=None):
        quizz_proxy = self.pool.get('training.exam.questionnaire')
        res = dict.fromkeys(ids, 0.0)

        course_ids = {} # course_ids -> ids
        quizz_ids = set() # list of quizz to question from
        for obj in self.browse(cr, uid, ids, context=context):
            quizz_ids.add(obj.questionnaire_id.id)
            course_ids[obj.course_id.id] = obj.id
        quizz_ids = list(quizz_ids)

        for quizz in quizz_proxy.browse(cr, uid, quizz_ids, context=context):
            tools.debug(quizz.question_ids)
            if not len(quizz.question_ids):
                # quizz has no question on it
                continue
            for q in quizz.question_ids:
                courses = q.question_id.course_ids
                for c in courses:
                    try:
                        obj_id = course_ids[c.id]
                    except KeyError:
                        # course is not related to this quizz
                        continue
                    res[obj_id] += q.question_id.point
        return res or 0.0

    _columns = {
        'course_id': fields.many2one('training.course',
                                     'Course',
                                     required=True,
                                     ondelete="cascade"),
        'questionnaire_id': fields.many2one('training.exam.questionnaire',
                                    'Questionnaire',
                                    required=True,
                                    ondelete='cascade'),
        'category_id': fields.related('course_id', 'category_id',
                                    type='many2one',
                                    relation='training.course_category',
                                    string='Category of Course',
                                    readonly=True),
        'kind': fields.related('course_id', 'kind',
                                type='selection',
                                selection=training_course_kind_compute,
                                string='Kind',
                                readonly=True),
        'passing_score': fields.float('Passing Score',
                                      required=True,
                                      help='Passing score of  related to Exam'),
        'total_point': fields.function(f_total_point,
                                    method=True,
                                    type='float',
                                    string='Total Point'),
    }

    _defaults = {
        'passing_score': lambda *a: 50.0,
    }

    def on_change_course(self, cr, uid, ids, course_id, context=None):
        if not course_id:
            return {'value' : {'category_id':''}}
        course = self.pool.get('training.course').browse(cr,uid,course_id)
        result = self.pool.get('training.course_category').search(cr, uid, [('analytic_account_id','=',course.parent_id.id)], context=context)
        return {'value' : {'category_id' :  result[0]}}

training_exam_questionnaire_course()

class exam_questionnaire(osv.osv):
    _name = 'training.exam.questionnaire'
    _description = 'Training Exam Questionnaire'

    def copy_data(self, cr, uid, object_id, values=None, context=None):
        if not context:
            context = {}
        if not values:
            values = {}
        # don't copy course as they are automatically updated
        if 'course_ids' not in values:
            values['course_ids'] = []
        return super(exam_questionnaire, self).copy_data(cr, uid, object_id, values, context=context)

    def _func_get_type(self, cr, uid, ids, name, args, context=None):
        r = {}
        for quizz in self.browse(cr, uid, ids):
            type = 'automatic'
            for q in quizz.question_ids:
                if q.question_type == 'plain':
                    type = 'manual'
                    break
            r[quizz.id] = type
        return r

    def _get_quizz_from_quizz_lines(self, cr, uid, ids, context=None):
        if not ids:
            return []
        quizzes = set()
        for quizz_line in self.read(cr, uid, ids, ['questionnaire_id']):
            quizzes.add(quizz_line['questionnaire_id'][0])
        return quizzes

    def _get_quizz_from_questions(self, cr, uid, ids, context=None):
        if not ids:
            return []
        pool_quizz_q = self.pool.get('training.exam.questionnaire.question')
        quizz_lines = set()
        quizzes = set()
        quizz_lines = pool_quizz_q.search(cr, uid, [('question_id','in',ids)])
        for quizz_line in pool_quizz_q.read(cr, uid, quizz_lines, ['questionnaire_id']):
            quizzes.add(quizz_line['questionnaire_id'][0])
        return quizzes

    def _len_question_ids(self, cr, uid, ids, field_name, value, context=None):
        return dict([(obj.id, len(obj.question_ids)) for obj in self.browse(cr, uid, ids, context=context)])

    #compute the time of questionnaire
    def point_compute(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, '')
        for questionnaire in self.browse(cr,uid,ids,context=context):
            res[questionnaire.id] = reduce(lambda acc,question: acc + question.question_id.point, questionnaire.question_ids, 0.0)
        return res or 0.0

    def duration_compute(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, '')
        for questionnaire in self.browse(cr,uid,ids,context=context):
            res[questionnaire.id] = reduce(lambda acc,question: acc + question.question_id.duration, questionnaire.question_ids, 0.0)
        return res or 0.0

    def course_category(self, cr, uid, ids, name, args, context=None):
        coursecat_proxy = self.pool.get('training.course_category')
        res = dict.fromkeys(ids, '')
        for obj in self.browse(cr,uid,ids,context=context):
            results = []
            for course in obj.course_ids:
                result = coursecat_proxy.search(cr, uid, [('analytic_account_id','=',course.course_id.parent_id.id)], context=context)
                results.append(result[0])
            # only keep the first reference (exam quizz should only have
            # one course attached, for other don't specify product line
            # to avoid errors
            if len(results) == 1:
                res[obj.id] = results[0]
            else:
                res[obj.id] = []
        return res

    def f_passing_score(self, cr, uid, ids, fn, args, context=None):
        """Quizz Global Passing Score
        The global passing score is the sum of all passing score by
        courses
        """
        res = dict.fromkeys(ids, '')
        for obj in self.browse(cr, uid, ids, context=context):
            if not obj.course_ids:
                res[obj.id] = 50.0
            else:
                res[obj.id] = reduce(lambda acc, c: acc + c.passing_score,
                                      obj.course_ids, 0.0)
        return res or 0.0

    _columns = {
        'name' : fields.char( 'Name', size=128, required=True, select=1, help='Name of questionnaire'),
        'state' : fields.selection([('draft', 'Draft'),
                                    ('validated', 'Validated'),
                                    ('pending', 'Pending'),
                                    ('inprogress', 'In Progress'),
                                    ('deprecated', 'Deprecated')
                                   ],
                                   'State',
                                   required=True,
                                   readonly=True,
                                   select=1,
                                   help='The state of the Questionnaire'),
        'kind': fields.function(_func_get_type, method=True,
                                 type='selection',
                                 string='Mode',
                                 selection=[('automatic','Automatic'),
                                            ('manual','Manual')],
                                 store={
                                     'training.exam.questionnaire.question': (_get_quizz_from_quizz_lines, [], 0),
                                     'training.exam.question': (_get_quizz_from_questions, ['type'], 0),
                                 },
                                 select=1,
                                 help='How this questionnaire could be corrected'),
        'type': fields.selection([('examen', 'Examen')],
                                'Type',
                                required=True,
                                select=2),
        'objective' : fields.text('Objective'),
        'description' : fields.text('Description'),
        'remark_firstpage': fields.text('Remark First Page'),

        'main_course_id' : fields.many2one('training.course',
                                      'Main Course',
                                      required=True,
                                      select=1,
                                      domain="[('state_course', 'in', ('draft', 'validated', 'pending'))]"),

#        'course_ids' : fields.many2many('training.course',
#                                        'training_exam_questionnaire_courses_rel',
#                                        'questionnaire_id',
#                                        'course_id',
#                                        domain="[('state_course', 'in', ('draft', 'validated', 'pending')]",
#                                        required=True),
        'course_ids': fields.one2many('training.exam.questionnaire.course',
                                    'questionnaire_id',
                                    string='Courses'),

        'total_point' : fields.function(point_compute,method=True,
                                        type='float',
                                        string='Total Point',
                                        help='Total point for the questionnaire'),
        'duration' : fields.function(duration_compute,method=True,
                                             type='float',
                                             string='Duration',
                                  help='Duration for the exam'),
        'question_ids' : fields.one2many('training.exam.questionnaire.question', 'questionnaire_id', 'Questions'),
        'len_question_ids' : fields.function(_len_question_ids,
                                             method=True,
                                             type='integer',
                                             string='Number of Questions',
                                             help='Total number of questions'),
        'passing_score': fields.function(f_passing_score,
                                        method=True,
                                        type='float',
                                        string='Global Passing Score',
                                        help='The global passing score of the questionnaire'),

        'category' : fields.function(course_category,
                                     method=True,
                                     type='many2one',
                                     relation='training.course_category',
                                     string='Category of  Course',
                                     select=1,
                                    ),
        'attachment_ids': fields.one2many('training.exam.questionnaire.attachment', 'questionnaire_id', 'Attachments',),
    }

    def _name_default(self, cr, uid, ids, context=None):
        return self.pool.get('ir.sequence').get(cr, uid, 'training.exam.questionnaire')

    _defaults = {
        'name' : _name_default,
        'state' : lambda *a: 'draft',
        'kind' : lambda *a: 'manual',
        'duration' : lambda *a: 2.0,
        'passing_score' : lambda *a: 1.0,
        'type': lambda *a: 'examen',
    }

    def _check_course_limit(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=None)
        if obj.type == 'examen' and len(obj.course_ids) > 1:
            return False
        return True


    def _check_score(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        return 0.0 <= obj.passing_score <= 100.0

    _constraints = [
        (_check_course_limit, "Only one course allowed for questionnaire with type 'Examen'", ['course_ids']),
        (_check_score, "Can you check the passing score  ?", ['passing_score']),
    ]

    def set_pending_status(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')

        for oid in ids:
            workflow.trg_create(uid, self._name, oid, cr)
            workflow.trg_validate(uid, self._name, oid, 'signal_teq_pending', cr)

        return self.write(cr, uid, ids, {'state' : 'pending'}, context=context)

    def reset_to_draft_cb(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')

        for oid in ids:
            workflow.trg_create(uid, self._name, oid, cr)

        return self.write(cr, uid, ids, {'state' : 'draft'}, context=context)

exam_questionnaire()

class exam_questionnaire_wizard(osv.osv_memory):
    _name = 'training.exam.questionnaire.wizard'
    _description = 'Questionnaire Wizard'

    _columns = {
        'name' : fields.char('Name', size=64, required=True),
        'course_id' : fields.many2one('training.course', 'Course',
                                      required=True,
                                      domain="[('state_course', '=', 'validated')]"),
        'number_of_question' : fields.integer('Number of Questions'),
        'kind' : fields.selection(
            [
                ('automatic', 'Automatic'),
                ('manual', 'At Least one open-ended question')
            ],
            'Type'),
    }

    _defaults = {
        'kind' : lambda *a: 'automatic',
        'number_of_question' : lambda *a: 20,
    }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close'}

    def action_generate_questionnaire(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids, context=context)[0]

        question_proxy = self.pool.get('training.exam.question')

        all_question_ids = question_proxy.search(cr, uid, [], context=context)

        mandatory_question_ids = []
        question_ids = []

        for question in question_proxy.browse(cr, uid, all_question_ids, context=context):
            if this.course_id in question.course_ids:
                if question.is_mandatory:
                    mandatory_question_ids.append(question.id)
                else:
                    question_ids.append(question.id)

        mqids = []
        qids = []

        import random

        number_of_mandatory_questions = random.randint(0, 3)
        number_of_questions = min(max(20, this.number_of_question) - number_of_mandatory_questions,len(question_ids))

        while number_of_mandatory_questions:
            try:
                idx = random.randint(0, len(mandatory_question_ids))
                mqids.append(mandatory_question_ids[idx])
                del mandatory_question_ids[idx]
            except:
                pass
            number_of_mandatory_questions -= 1

        while number_of_questions:
            try:
                idx = random.randint(0, len(question_ids))
                qids.append(question_ids[idx])
                del question_ids[idx]
                number_of_questions -= 1
            except:
                pass

        return {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'training.exam.questionnaire',
            'view_id':self.pool.get('ir.ui.view').search(cr,uid,[('name','=','training.exam.questionnaire.form')]),
            'type': 'ir.actions.act_window',
            'target':'current',
            'context' : {
                'default_name' : this.name,
                'default_course_id' : this.course_id.id,
                'default_question_ids' : mqids + qids,
                'default_kind' : this.kind,
            }
        }

exam_questionnaire_wizard()

class training_question_wizard(osv.osv_memory):
    _name = 'training.exam.question.wizard'
    _description = 'Question Wizard'

    _columns = {
        'course_id' : fields.many2one('training.course', 'Course', required=True,
                                      domain="[('state_course', '=', 'validated')]"),
    }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close'}

    def find_question_with_course(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids, context=context)[0]

        context2 = context.copy()
        context2.update({'course_id':this.course_id.id})

        return {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'training.exam.question',
            'view_id':self.pool.get('ir.ui.view').search(cr,uid,[('name','=','training.exam.question.tree')]),
            'type': 'ir.actions.act_window',
            'target':'current',
            'context': context2,
        }

training_question_wizard()

class training_subscription(osv.osv):
    _inherit = 'training.subscription'

    def action_subscription_line_compute(self, cr, uid, ids, context=None):
        if not len(ids):
            return False

        sl_proxy = self.pool.get('training.subscription.line')
        session_proxy = self.pool.get('training.session')
        questionnaire_proxy = self.pool.get('training.exam.questionnaire')

        for subscription in self.browse(cr, uid, ids, context=context):
            for sl in subscription.subscription_line_ids:
                if (not sl.computed) and sl.exam_session_id:
                    # Rechercher tous les cours provenant de l'offre associée à la session
                    # Rechercher les questionnaires appartenant à ces cours
                    course_ids = set()

                    for course in sl.session_id.offer_id.course_ids:
                        course_ids.add(course.course_id.id)

                    for course_id in course_ids:
                        course = self.pool.get('training.course').browse(cr, uid, course_id, context=context)
                        if not course.course_type_id.product_id:
                            raise osv.except_osv(_('Warning'),
                                                 _("Can you check the product on the course type of the course ?"))

                        price = self.pool.get('product.pricelist').price_get(cr, uid,
                                                                                 [sl.price_list_id.id],
                                                                                 course.course_type_id.exam_product_id.id,
                                                                                 subscription.partner_id.id,
                                                                                 1.0)[sl.price_list_id.id]
                        values = {
                                'job_id' : sl.job_id.id,
                                'job_email' : sl.job_id.email or '',
                                'subscription_id' : sl.subscription_id.id,
                                'session_id' : sl.exam_session_id.id,
                                'parent_id' : sl.id,
                                'course_id' : course.id,
                                'price_list_id' : sl.price_list_id.id,
                                'price' : price,
                        }
                        sl_proxy.create(cr, uid, values, context=context)
                        sl.write({'computed' : 1})

        return True


training_subscription()

class training_subscription_line(osv.osv):
    _inherit = 'training.subscription.line'
    _columns = {
        'exam_session_id' : fields.many2one('training.session', 'Exam Session', domain=[('kind', '=', 'exam')]),
        'course_id' : fields.many2one('training.course', 'Exam',
                                      domain=[('state_course', 'in', ['validated', 'pending'])]),
        'parent_id' : fields.many2one('training.subscription.line', 'Parent', ondelete='set null'),
        'computed' : fields.boolean('Computed'),
    }

    _defaults = {
        'computed' : lambda *a: 0,
    }

    def _check_subscription(self, cr, uid, ids, context=None):
        # FIXME check also the overlaps for exam sessions...
        ids = [line.id for line in self.browse(cr, 1, ids, context=context) if line.session_id.kind != 'exam']
        return super(training_subscription_line, self)._check_subscription(cr, uid, ids, context)

    def on_change_session(self, cr, uid, ids, session_id, price_list_id, partner_id, context=None):
        if not session_id:
            return False
        session = self.pool.get('training.session').browse(cr, uid, session_id, context=context)
        if session.kind == 'exam':
            price_list = self._get_price_list_from_product_line(session, partner_id, price_list_id)
            return {'value': {'kind': 'exam', 'price_list_id': price_list}} #, 'course_id': False}}

        res = super(training_subscription_line, self).on_change_session(cr, uid, ids, session_id,
                                                                        price_list_id, partner_id,
                                                                        context=None)
        if res and 'kind' in res['value']:
            res['value']['course_id'] = 0

        return res

    def on_change_exam(self, cr, uid, ids, session_id, price_list_id, course_id, partner_id, context=None):
        # If exam course is from a product line with special members,
        # we must apply this pricelist if current partner is one of those
        ocv = {'value':{}}
        if course_id:
            course = self.pool.get('training.course').browse(cr, uid, course_id)
            if course.category_id and course.category_id.price_list_id:
                if any(partner.id == partner_id for partner in course.category_id.partner_ids):
                    price_list_id = course.category_id.price_list_id.id
                    ocv['value']['price_list_id'] = price_list_id
            else:
                # get partner default pricelist
                p = self.pool.get('res.partner').browse(cr, uid, partner_id)
                pl = p.property_product_pricelist and p.property_product_pricelist.id or False
                ocv['value']['price_list_id'] = pl

        ocv_p = self.on_change_price_list(cr, uid, ids, session_id, ocv['value'].get('price_list_id',price_list_id), course_id, context)
        if ocv_p:
            ocv['value'].update(ocv_p['value'])
        return ocv

    def on_change_price_list(self, cr, uid, ids, session_id, price_list_id, course_id, context=None):
        if not session_id or not price_list_id:
            return False
        session = self.pool.get('training.session').browse(cr, uid, session_id, context=context)
        if session.kind != 'exam':
            return super(training_subscription_line, self).on_change_price_list(cr, uid, ids, session_id, price_list_id, context=context)

        if not course_id:
            return False
        course = self.pool.get('training.course').browse(cr, uid, course_id, context=context)

        pricelist_proxy = self.pool.get('product.pricelist')

        if not course.course_type_id.exam_product_id:
            raise osv.except_osv(_('Warning'),
                                 _("Can you check the product on the course type of the course %s") % course.name)

        return {
            'value' : {
                'price' : pricelist_proxy.price_get(cr, uid, [price_list_id], course.course_type_id.exam_product_id.id, 1.0)[price_list_id]
            }
        }

    def _get_values_from_wizard(self, cr, uid, subscription_id, job, subscription_mass_line, context=None):
        subscription = self.pool.get('training.subscription').browse(cr, uid, subscription_id, context=context)
        session = subscription_mass_line.session_id

        def_pricelist_id = job.name.property_product_pricelist.id

        values = {
            'subscription_id' : subscription_id,
            'job_id' : job.id,
            'job_email': job.email,
            'session_id' : session.id,
        }
        ocv = self.on_change_session(cr, uid, [], session.id, def_pricelist_id, job.name.id, context=context)
        if ocv and 'value' in ocv:
            values.update(ocv['value'])

        ocv = super(training_subscription_line, self).on_change_price_list(cr, uid, [], values['session_id'], values.get('price_list_id', False), context=context)
        course_id = subscription_mass_line.course_id and subscription_mass_line.course_id.id
        ocv = self.on_change_exam(cr, uid, [], values['session_id'], values.get('price_list_id', False), course_id, job.name.id, context=context)
        if ocv and 'value' in ocv:
            values.update(ocv['value'])

        values.update({
            'exam_session_id' : getattr(subscription_mass_line.exam_session_id, 'id'),
            'course_id' : course_id,
        })
        return values

    def _get_courses(self, cr, uid, ids, context=None):
        res = dict.fromkeys(ids, [])

        standard_ids = []

        for sl in self.browse(cr, uid, ids, context=context):
            if sl.kind == 'exam':
                res[sl.id] = [sl.course_id]
            else:
                standard_ids.append(sl.id)

        values = super(training_subscription_line, self)._get_courses(cr, uid, standard_ids, context=context)
        res.update(values)

        return res

    # training.subscription.line
    def _get_invoice_line_data(self, cr, uid, name, invoice_id, partner, session, subline, context=None):
        values = super(training_subscription_line, self)._get_invoice_line_data(cr, uid, name, invoice_id, partner, session, subline, context=context)
        if not values:
            values = {}
        if subline.kind == 'exam' and subline.course_id:
            name = "%s %s" % (subline.contact_id.first_name, subline.contact_id.name,)
            values['name'] = "%s: %s (%s)" % (_('Exam'), subline.course_id.name, name)
        return values

    # training.subscription.line
    def _get_invoice_line_taxes(self, cr, uid, subline, fiscal_position, partner, session, context=None):
        if subline.kind == 'exam':
            _slc = subline.course_id
            if _slc:
                _slcp = subline.course_id.course_type_id.exam_product_id
                if _slcp.taxes_id:
                    taxes = _slcp.taxes_id
                    tax_id = self.pool.get('account.fiscal.position').map_tax(cr, uid, fiscal_position, taxes)
                    return [(6, 0, [t for t in tax_id])]
            return []
        # else
        return super(training_subscription_line, self)._get_invoice_line_taxes(cr, uid, subline, fiscal_position, partner, session, context=context)

    # training.subscription.line
    def action_create_invoice(self, cr, uid, ids, context=None):
        # Creation des factures
        account_id = self.pool.get('account.account').search(cr, uid, [('code', '=', '70828')])[0]
        # Get journal
        journal_proxy = self.pool.get('account.journal')
        journal_sales_srch = journal_proxy.search(cr, uid, [('type','=','sale'),('refund_journal','=',False)])
        journal_sales = journal_proxy.browse(cr, uid, journal_sales_srch)[0]

        proxy_seance = self.pool.get('training.seance')
        proxy_invoice = self.pool.get('account.invoice')
        proxy_invoice_line = self.pool.get('account.invoice.line')
        proxy_adist = self.pool.get('account.analytic.plan.instance')
        proxy_adistline = self.pool.get('account.analytic.plan.instance.line')
        workflow = netsvc.LocalService('workflow')

        if not context:
            context = {}

        exam_sl_ids = []
        other_sl_ids = []

        partners = {}
        for sl in self.browse(cr, uid, ids, context=context):
            if sl.invoice_line_id:
                continue
            if sl.kind == 'exam':
                exam_sl_ids.append(sl.id)
            else:
                other_sl_ids.append(sl.id)


        invoice_ids = []
        if other_sl_ids:
            invoice_ids.extend(super(training_subscription_line, self).action_create_invoice(cr, uid, other_sl_ids, context=context))

        for sl in self.browse(cr, uid, exam_sl_ids, context=context):
            if -0.00001 < sl.price < 0.00001:
                continue
            key = (sl.subscription_id.partner_id, sl.session_id, sl.subscription_id.payment_term_id.id, sl.course_id,)
            partners.setdefault(key, []).append(sl)

        for (partner, session, payment_term, course), subscription_lines in partners.items():
            name = "%s - %s" % (session.name, course.name)
            if context.get('cancellation', False) is True:
                name += ' - ' + _('Cancellation')

            invoice_values = {
                'name' : name,
                'origin' : "%s - %s" % (session.name, course.name),
                'type' : 'out_invoice',
                'reference' : "%s - %s - %s" % (partner.name, session.name, course.name),
                'partner_id' : partner.id,
                'address_contact_id' : partner.notif_contact_id and partner.notif_contact_id.address_id.id,
                'address_invoice_id' : subscription_lines[0].subscription_id.address_id.id,
                'journal_id': journal_sales.id,
                'account_id' : partner.property_account_receivable.id,
                'fiscal_position' : partner.property_account_position.id,
                'date_invoice' : time.strftime('%Y-%m-%d'),
                'payment_term' : payment_term,
            }
            invoice_values.update(self._get_invoice_data(cr, uid, name, partner, session, subscription_lines, context=context))

            invoice_id = proxy_invoice.create(cr, uid, invoice_values)

            fpos_proxy = self.pool.get('account.fiscal.position')
            fpos = invoice_values['fiscal_position'] and fpos_proxy.browse(cr, uid, [invoice_values['fiscal_position']])[0] or False

            global_courses = self._get_courses(cr, uid, [sl.id for sl in subscription_lines], context=context)
            for sl in subscription_lines:
                session = sl.session_id
                name = "%s %s" % (sl.contact_id.first_name, sl.contact_id.name,)
                courses = global_courses[sl.id]

                values = {
                    'invoice_id' : invoice_id,
                    'product_id' : session.offer_id.product_id.id,
                    'quantity' : 1,
                    'name' : session.name + u' ' + name,
                    'account_id' : session.offer_id.product_id.property_account_income and session.offer_id.product_id.property_account_income.id or account_id,
                    'origin' : sl.name,
                    'price_unit' : sl.price,
                    'discount' : context and context.get('discount', 0.0) or 0.0,
                    'invoice_line_tax_id': self._get_invoice_line_taxes(cr, uid, sl, fpos, partner, session, context=context),
                    'account_analytic_id': '',
                    'analytics_id': '',  # Analytic Distribution
                }
                values.update(self._get_invoice_line_data(cr, uid, name, invoice_id, partner, session, sl, context=None))

                self._invoice_min_max(cr, uid, values, context)

                total_duration = 0.0
                for c in courses:
                    if c.duration == 0.0:
                        raise osv.except_osv(_('Error'),
                                             _("The following course has not a valid duration '%s' (%d)") % (c.name, c.id))
                    total_duration += c.duration

                # Create 'analytic distribution instance'
                adist_id = proxy_adist.create(cr, uid, {
                    'journal_id': journal_sales.analytic_journal_id.id,
                })

                aaid = course.analytic_account_id
                if not isinstance(aaid, (int, long, bool)):
                    aaid = aaid.id

                proxy_adistline.create(cr, uid, {
                    'plan_id': adist_id,
                    'analytic_account_id': aaid,
                    'rate': course.duration * 100.0 / total_duration
                })

                values['analytics_id'] = adist_id
                invoice_line_id = proxy_invoice_line.create(cr, uid, values, context=context)
                sl.write({'invoice_line_id' : invoice_line_id})

            proxy_invoice.button_compute(cr, uid, [invoice_id])
            invoice_ids.append(invoice_id)

        return invoice_ids

training_subscription_line()

class training_participation_exam(osv.osv):
    _inherit = 'training.participation'

    def copy_data(self, cr, uid, object_id, values=None, context=None):
        if not values:
            values = {}
        if 'participation_line_ids' not in values:
            values['participation_line_ids'] = []
        return super(training_participation_exam, self).copy_data(cr, uid, object_id, values, context)

    def after_exam_sheet_generation(self, cr, uid, participation_id, context=None):
        pool = pooler.get_pool(cr.dbname)
        # Need to register questions printed on PDF into corresponding training.participation record
        qn = 1 # question number
        qset = set() # question id set

        tpline = pool.get('training.participation.line')
        tpline_current_ids = tpline.search(cr, uid, [('participation_id','=',participation_id)])
        if len(tpline_current_ids) != 0:
            raise Exception("Can't generate exam sheet on participation which already have participation line")

        for page_num, page in enumerate(context['checkboxes_context']):
            if not len(page):
                continue
            for qanswer in page:
                qid, aid = qanswer.split('-')
                if qid not in qset:
                    qset.add(qid)
                    new_qn = qn
                    qn += 1
                    new_tpline = {
                        'sequence': new_qn,
                        'page_num': page_num,
                        'participation_id': participation_id,
                        'question_id': qid,
                        'graded': False
                    }
                    tpline.create(cr, uid, new_tpline)

    def _result_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0.0)
        for p in self.browse(cr, uid, ids, context=context):
            if p.forced_result >= -0.001 and p.forced_result <= 0.001:
                # Result not forced
                if p.participation_line_ids:
                    res[p.id] = reduce(lambda acc,x: acc + x.point, p.participation_line_ids, 0.0)
            else:
                # Result is forced, return that value
                res[p.id] = p.forced_result
        return res

    def _result_pourcentage_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0.0)
        for p in self.read(cr, uid, ids, ['result','total_points'], context=context):
            if p['total_points'] <= 0.0:
                res[p['id']] = 100.0
            else:
                res[p['id']] = p['result'] * 100 / p['total_points']
        return res

    def _total_points_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0.0)
        quizz_cache = {}
        quizz_proxy = self.pool.get('training.exam.questionnaire')
        for p in self.read(cr, uid, ids, ['questionnaire_id'], context=context):
            quizz_id = p['questionnaire_id'] and p['questionnaire_id'][0] or None
            if quizz_id:
                if quizz_id in quizz_cache:
                    res[p['id']] = quizz_cache[quizz_id]
                else:
                    q = quizz_proxy.read(cr, uid, [quizz_id], ['total_point'])
                    totpoints = q[0]['total_point']
                    if totpoints <= 0.0:
                        totpoints = 100.0 # if no question defined on questionnaire, use 100% as default
                    res[p['id']] = totpoints
            else:
                # no quizz defined, force it to 100.0 so it's easy for percentage calculation
                res[p['id']] = 100.0
        return res

    def _succeeded(self, cr, uid, ids, fn, args, context=None):
        res = dict.fromkeys(ids, 'n/a')
        for p in self.browse(cr, uid, ids, context=context):
            # if passing_score == 0, that means it's not set!
            if p.passing_score >= 0.0001:
                res[p.id] = ['no', 'yes'][(p.result >= p.passing_score)]
        return res

    def _certif_printed(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, 0)
        q = """
            SELECT  res_id, count(1)
            FROM    ir_attachment
            WHERE   res_id in (%s)
              AND   res_model = 'training.participation'
              AND   name like 'CERTIF%%'
            GROUP
                BY  res_id
            """ % (','.join(map(str, map(int, ids))))
        cr.execute(q)
        res.update(dict([(x[0], bool(x[1])) for x in cr.fetchall()]))
        return res

    def _checkstore_update_certif(self, cr, uid, ids, context=None):
        proxy = self.pool.get('ir.attachment')
        attach_ids = proxy.search(cr, uid, [('id', 'in', ids),('res_model', '=', 'training.participation'),('name', 'like', 'CERTIF%')], context=context)
        res = set()
        for attach in proxy.browse(cr, uid, attach_ids, context=context):
            res.add(attach.res_id)
        return list(res)

    def _check_self_particip(self, cr, uid, ids, context=None):
        return ids

    def on_change_forced_result(self, cr, uid, ids, result, context=None):
        if not len(ids):
            return {'value':{}}
        ret_val = result > 0.0 and True or False
        return {'value': {'result_received': ret_val }}

    def on_change_questionnaire(self, cr, uid, ids, questionnaire_id, context=None):
        if not questionnaire_id:
            return {'value': {'passing_score': 0.0}}

        quizz_proxy = self.pool.get('training.exam.questionnaire')
        quizz = quizz_proxy.browse(cr, uid, questionnaire_id)
        return {'value': {'passing_score': quizz.passing_score}}

    def random_questionnaire_get_domain(self, cr, uid, participation):
        return [('type','=','examen'),('state','in',['validated']),('main_course_id','=',participation.course_questionnaire_id.id)]

    def random_questionnaire_assign(self, cr, uid, ids):
        t_quizz = self.pool.get('training.exam.questionnaire')

        for p in self.browse(cr, uid, ids):
            if p.questionnaire_id:
                # questionnaire already assigned, nothing more to do
                continue
            course = p.course_questionnaire_id
            if not course:
                raise osv.except_osv(_('Error'),
                                     _("Can't assign questionnaire to participation %s because there is not exam defined on this participation") % (p.id))

            # combinate quizz relate to "course", and standard filter
            domain = self.random_questionnaire_get_domain(cr, uid, p)

            # search for quizz matching the computated domain
            quizz_ids = t_quizz.search(cr, uid, domain)
            if not quizz_ids:
                raise osv.except_osv(_('Error'),
                                    _("Can't find validated questionnaire for course '%s'") % (course.name))

            # make random choice of quizz
            final_quizz_id = random.choice(quizz_ids)
            self.write(cr, uid, [p.id], {'questionnaire_id': final_quizz_id})

    _columns = {
        'exam_id': fields.related('subscription_line_id', 'course_id', type='many2one', relation='training.course', readonly=True, string="Exam"),
        'questionnaire_id' : fields.many2one('training.exam.questionnaire', 'Questionnaire',
                                             help='Select the Questionnaire for participant'),
#        'course_questionnaire_id' : fields.related('questionnaire_id', 'course_id', type='many2one', relation='training.course', string='Exam', readonly=True, store=True, select=1),
        'course_questionnaire_id': fields.many2one('training.course', string='Exam', select=1),
        'duration_questionnaire_id' : fields.related('questionnaire_id',
                                                     'duration',
                                                     type='float',
                                                     string='Duration',
                                                     store=True,
                                                     readonly=True, help='Duration of selected  Questionnaire'),
        'participation_line_ids' : fields.one2many('training.participation.line',
                                                   'participation_id',
                                                   'Participation Lines'),
        'result_received': fields.boolean('Result received', select="2"),
        'forced_result': fields.float('Forced Result', digits=(12,2),
                                help='If not zero, this is the score that will be forced'),
        'forced_noresult': fields.boolean('Forced No Result', help='Check if this participation won\'t have any result, and that is normal. This particaption will not be taken anymore in account for correction request, exam certificate'),
        'result' : fields.function(_result_compute, method=True, string='Result', type='float',
                                   store={
                                        'training.participation': (
                                            _check_self_particip,
                                            ['forced_result','result_received','questionnaire_id','course_questionnaire_id','participation_line_ids','passing_score'],
                                            1,
                                        )
                                    },
                                   help='Exam Result of participate'),
        'total_points': fields.function(_total_points_compute, method=True, string='Total Points', type='float',
                                        store = {
                                            'training.participation': (
                                                _check_self_particip,
                                                ['id', 'course_questionnaire_id', 'participation_line_ids', 'questionnaire_id'],
                                                1,
                                            ),
                                        },
                                        help='Total Point on Questionnaire',
                                        ),
        'result_pourcentage': fields.function(_result_pourcentage_compute, method=True, string='Result (%)', type='float',
                                            help="Exam Result of Participate in Pourcetage"),
        'passing_score': fields.float('Passing Score',
                                    help='The minimum score needed to succueed to this exam, assigned when questionnaire is affected to the participation (on "Exam Sheet" generation) and not updated after'),

        'kind' : fields.related('seance_id', 'kind', type='selection', selection=[('standard', 'Course'),('exam', 'Exam')], string='Kind', select=1),
        'succeeded': fields.function(_succeeded,
                                     method=True,
                                     type='selection',
                                     selection=[('n/a', 'N/A'),
                                                ('no', 'No'),
                                                ('yes', 'Yes')],
                                     select=2,
                                     string='Succeeded'),

        'certif_printed' : fields.function(_certif_printed,
                                        method=True,
                                        type="boolean",
                                        store={
                                            'ir.attachment' : (_checkstore_update_certif, None, 10),
                                        },
                                        select=2,
                                        string="Certificate Printed"),

    }

    _defaults = {
        'result_received': lambda *a: False,
        'forced_result': lambda *a: 0.0,
        'passing_score': lambda *a: 0.0,
    }

training_participation_exam()

class training_participation_line(osv.osv):
    _name = 'training.participation.line'

    _columns = {
        'sequence': fields.integer('Question N°'),
        'page_num': fields.integer('Page N°'),
        'participation_id' : fields.many2one('training.participation', 'Participation',
                                             required=True,
                                             ondelete="cascade"),
        'question_id' : fields.many2one('training.exam.question', 'Question', ondelete='restrict'),
        'point_question_id' : fields.related('question_id', 'point', type='integer', string='Max Point', readonly=True, help='Point of question'),
        'type_question_id' : fields.related('question_id', 'type',
                                            type='selection',
                                            selection = [('qcm', 'QCM'),
                                                         ('qcu', 'QCU'),
                                                         ('plain', 'Plain'),
                                                         ('yesno', 'Yes/No') ],
                                            string='Type', readonly=True),
        'yesno_question_id' : fields.related('question_id', 'response_yesno', type='char',
                                             string='Solution YesNo', readonly=True, help='Question type'),
        'plain_question_id' : fields.related('question_id', 'response_plain', type='text',
                                             string='Solution Plain', readonly=True),
        'qcm_question_id' : fields.related('question_id', 'question_answer_ids', type='one2many',
                                           relation='training.exam.question.answer', readonly=True,
                                           string='Solution QCM'),
        'graded': fields.boolean('Is Graded'),

        # Response from the user
        'response_qcm_ids' : fields.many2many('training.exam.question.answer', 'training_result_line_answer_rel',
                                        'exam_line_id', 'question_answer_id', 'Solutions', domain="[('question_id', '=', question_id)]"),
        'response_plain' : fields.text('Solution'),
        'response_yesno' : fields.selection([('yes', 'Yes'),('no', 'No')], 'Solution'),

        'point' : fields.float('Point', digits=(12,2),
                                help='Number of point get from question'),

        'note' : fields.text('Note'),

    }

    _defaults = {
        'sequence': lambda *a: 0,
        'page_num': lambda *a: 0,
    }

    def _check_score(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        question = self.pool.get('training.exam.question').browse(cr, uid, obj.question_id.id)
        return obj.point <=question.point or 0.0
    def on_change_question(self, cr, uid, ids, question_id, context=None):
        if not question_id:
            return False

        question = self.pool.get('training.exam.question').browse(cr, uid, question_id)

        return {
            'value': {
                'point_question_id': question.point,
                'type_question_id' : question.type,
            }
        }
    _constraints = [
        (_check_score, "Can you check the give point  ?", ['point']),
    ]
training_participation_line()

class mass_subscription_line(osv.osv_memory):
    _inherit = 'training.subscription.mass.line'

    _columns = {
        'date_session' : fields.related('session_id', 'date', type='datetime', string='Date', readonly=True),
        'exam_session_id' : fields.many2one('training.session', 'Exam Session'),
        'course_id' : fields.many2one('training.course', 'Exam',
                                      domain="[('state_course', '=', 'validated')]"),
    }

    def on_change_session(self, cr, uid, ids, session_id, context=None):
        if not session_id:
            return False

        session = self.pool.get('training.session').browse(cr, uid, session_id)
        dates = [seance.date for seance in session.seance_ids]

        return {
            'value' : {
                'kind' : session.kind,
                'date_session' : session.date,
            },
            'domain' : {
                'exam_session_id' :
                [('state', 'in', ('opened_confirmed', 'opened', 'closed_confirmed')),
                 ('kind', '=', 'exam'),
                 ('date', '>', len(dates) and max(dates) or session.date),
                 ('id', '!=', session.id)],
            },
        }

mass_subscription_line()

class training_participation_stakeholder(osv.osv):
    _inherit = 'training.participation.stakeholder'
    _columns = {
        'kind' : fields.related('seance_id', 'kind',
                                type='selection',
                                selection=[ ('standard', 'Course'), ('exam', 'Exam')],
                                string='Kind',
                                readonly=True,
                                select=1)
    }

    def _check_disponibility(self, cr, uid, ids, context=None):
        # FIXME check also the overlaps for exam sessions at different places...
        ids = [sh.id for sh in self.browse(cr, uid, ids, context=context) if sh.kind != 'exam']
        return super(training_participation_stakeholder, self)._check_disponibility(cr, uid, ids, context)

    def _default_price_compute(self, cr, uid, job, seance, product_id=None, context=None):
        if not job or not seance:
            return False
        if isinstance(seance, (int, long)):
            seance = self.pool.get('training.seance').browse(cr, uid, seance, context=context)

        if seance.kind != 'exam':
            return super(training_participation_stakeholder, self)._default_price_compute(cr, uid, job, seance, product_id=product_id, context=None)
        if product_id and isinstance(product_id, (int,long)):
            product = self.pool.get('product.product').browse(cr, uid, product_id)
        else:
            product = seance._get_product()
        if not product:
            raise osv.except_osv(_('Error'),
                                 _("The type of the course (%s) of this seance has no product defined") % course.name)
        return product.standard_price * seance.duration

training_participation_stakeholder()

class training_subscription_line_second(osv.osv):
    _inherit = 'training.subscription.line.second'

    _columns = {
        'exam_session_id' : fields.many2one('training.session', 'Exam Session'),
        'course_id' : fields.many2one('training.course', 'Exam',
                                      domain="[('state_course', '=', 'validated')]"),
    }

    def _create_from_wizard(self, cr, uid, the_wizard, job, subscription_line_mass, context=None):
        proxy = self.pool.get('training.subscription.line.second')
        return proxy.create(cr, uid,
                            {
                                'job_id' : job.id,
                                'session_id' : subscription_line_mass.session_id.id,
                                'exam_session_id' : subscription_line_mass.exam_session_id.id,
                                'course_id' : subscription_line_mass.course_id and subscription_line_mass.course_id.id,
                            },
                            context=context)

training_subscription_line_second()

class training_participation(osv.osv):
    _inherit = 'training.participation'

training_participation()


class training_email(osv.osv):
    _inherit = 'training.email'

    def _get_lang(self, session, seance, **objects):
        DEFAULT_LANG = 'fr_FR'
        lng = None
        subline = objects.get('subline', None)
        if (session and session.kind == 'exam') or (seance and seance.kind == 'exam'):
            if not subline:
                return DEFAULT_LANG
            return subline.course_id.lang_id.code
        return super(training_email, self)._get_lang(session, seance, **objects)
training_email()

class training_seance_generate_pdf_wizard(osv.osv_memory):
    _inherit = 'training.seance.generate.zip.wizard'

    _columns = {
        'exams_report' : fields.boolean('Exams',
                                        help="If you select this option, you will print the exams. The filename format is Exam_DATE_PARTICIPATIONID.pdf"),
    }

    _defaults = {
        'exams_report' : lambda *a: False,
    }

    def add_selections(self, cr, uid, ids, directory, context=None):
        active_id = context and context.get('active_id')
        seance = self.pool.get('training.seance').browse(cr, uid, active_id, context=context)
        ts = time.strptime(seance.date, '%Y-%m-%d %H:%M:%S')
        date = time.strftime('%Y%m%d', ts)

        exam_directory = os.path.join(directory, 'Exams')
        os.mkdir(exam_directory)

        res = []
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.exams_report:
                for part in seance.participant_ids:
                    if part.questionnaire_id:
                        res = self._get_report(cr, uid, part.id, 'report.training.participation.report', context=context)

                        filename = os.path.join(exam_directory, 'Exam_%s_%06d.pdf' % (date, part.id))
                        fp = file(filename, 'w')
                        fp.write(res)
                        fp.close()

        super(training_seance_generate_pdf_wizard, self).add_selections(cr, uid, ids, directory, context=context)

training_seance_generate_pdf_wizard()

class exam_wizard_helper(osv.osv_memory):
    _name = 'training.exam.wizard.helper'

    _columns = {
        'questionnaire_id' : fields.many2one('training.exam.questionnaire', 'Questionnaire', required=True, select=1),
        'question_ids' : fields.many2many('training.exam.question', 'training_exam_wizard_helper_rel', 'helper_id', 'question_id', 'Questions', ),
        'course_id' : fields.many2one('training.course', 'Course', context={'quizz_search': 1}),
        'kind' : fields.char('Kind', size=32),
    }

    def _default_questionnaire_id(self, cr, uid, context=None):
        return context and context.get('active_id', False) or False

    def _default_course_id(self, cr, uid, context=None):
        active_id = context and context.get('active_id', False) or False

        questionnaire = self.pool.get('training.exam.questionnaire').browse(cr, uid, active_id, context=context)
        if questionnaire.type == 'examen':
            r = questionnaire.main_course_id.id
        else:
            r = len(questionnaire.course_ids) and questionnaire.course_ids[0].course_id.id or None
        return r

    _defaults = {
        'questionnaire_id' : _default_questionnaire_id,
        'course_id' : _default_course_id,
    }

    def cancel_cb(self, cr, uid, ids, context=None):
        return {'type' : 'ir.actions.act_window_close'}

    def add_questions_cb(self, cr, uid, ids, context=None):

        this = self.browse(cr, uid, ids[0], context=context)

        proxy = self.pool.get('training.exam.questionnaire.question')

        for question in this.question_ids:
            proxy.create(cr, uid,
                         {
                             'question_id' : question.id,
                             'questionnaire_id' : this.questionnaire_id.id,
                         }, context=context)

        return {'type' : 'ir.actions.act_window_close'}

exam_wizard_helper()

class training_exam_questionnaire_attachment(osv.osv):
    _name = 'training.exam.questionnaire.attachment'
    _description = 'training.exam.questionnaire.attachment'
    _order = 'position DESC, sequence ASC'

    _columns = {
        'questionnaire_id': fields.many2one('training.exam.questionnaire', 'Questionnaire', required=True,),
        'attachment_id': fields.many2one('ir.attachment', 'Attachment', required=True,),
        'position': fields.selection([('before','Before'),('after','After')], 'Position', required=True,),
        'sequence': fields.integer('Sequence', ),
        'store_in_dms': fields.boolean('Store In DMS', help='Indicate if generated document will be store is the document management system or discared on scan'),
    }

    _defaults = {
        'position': lambda *a: 'after',
        'sequence': lambda *a: 0,
        'store_in_dms': lambda *a: False,
    }

training_exam_questionnaire_attachment()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
