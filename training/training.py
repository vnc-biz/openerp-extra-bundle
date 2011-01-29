# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu>). All Rights Reserved
#    Copyright (C) 2010 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
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

from cStringIO import StringIO
from osv import osv, fields
import decimal_precision as dp
from tools import config
from tools.translate import _
from zipfile import PyZipFile, ZIP_DEFLATED
import base64
import mx.DateTime
import netsvc
import os
import re
import time
import datetime
import tools
import re
import mx


WRITABLE_ONLY_IN_DRAFT = dict(readonly=True, states={'draft': [('readonly', False)]})

def _partner_from_uid(obj, cr, uid, context=None):
    user = obj.pool.get('res.users').browse(cr, uid, uid, context)
    if user and user.partner_id:
        return user.partner_id.id
    return False

class training_course_pending(osv.osv):
    _name = 'training.course.pending'

training_course_pending()

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'

    _columns = {
        'name' : fields.char('Account Name', size=64, required=True),
    }

account_analytic_account()

class training_config_contact_function(osv.osv):
    _name = 'training.config.contact.function'

    def _get_values_of_kind(self):
        return [('standard', 'Course')]

    _rec_name = 'kind'

    _columns = {
        'kind' : fields.selection(lambda obj, cr, uid, context=None: obj._get_values_of_kind(), 'Kind', required=True, select=1),
        'function' : fields.char('Function', size=64, required=True, select=1),
    }

    _sql_constraints = [
        ('uniq_kind_function', 'unique(kind, function)', 'You can not define twice the same relation !'),
    ]

training_config_contact_function()

class training_course_category(osv.osv):
    _name = 'training.course_category'
    _description = 'The category of a course'
    _inherits = {
        'account.analytic.account' : 'analytic_account_id',
    }

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
        'complete_name': fields.function(_name_get_fnc, method=True, type="char", string='Full Name'),
        'analytic_account_id' : fields.many2one('account.analytic.account', 'Analytic Account', ondelete='cascade'),

        'partner_ids' : fields.many2many('res.partner',
                                         'training_purchase_line_partner_rel',
                                         'purchase_line_id',
                                         'partner_id',
                                         'Partners'),
        'price_list_id' : fields.many2one('product.pricelist', 'Pricelist', domain="[('type', '=', 'sale')]"),
    }

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

training_course_category()

class training_course_type(osv.osv):
    _name = 'training.course_type'
    _description = "The Course's Type"

    _columns = {
        'name' : fields.char('Course Type', size=32, required=True, select=1, help="The course type's name"),
        'objective' : fields.text('Objective',
                                  help="Allows to the user to write the objectives of the course type",
                                  translate=True,
                                 ),
        'description' : fields.text('Description',
                                    translate=True,
                                    help="Allows to the user to write the description of the course type"),
        'min_limit' : fields.integer('Minimum Threshold',
                                     required=True,
                                     select=2,
                                     help="The minimum threshold is the minimum for this type of course"),
        'max_limit' : fields.integer('Maximum Threshold',
                                     required=True,
                                     select=2,
                                     help="The maximum threshold is the maximum for this type of course"),
        'product_id' : fields.many2one('product.product', 'Lecturer'),
    }

    def _check_limits(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids)[0]
        return obj.min_limit <= obj.max_limit

    _constraints = [
        (_check_limits,
         'The minimum limit is greater than the maximum limit',
         ['min_limit', 'max_limit']),
    ]

training_course_type()

class training_course(osv.osv):
    _name = 'training.course'

training_course()

class training_course_purchase_line(osv.osv):
    _name = 'training.course.purchase_line'
    _rec_name = 'course_id'
    _columns = {
        'course_id' : fields.many2one('training.course', 'Course', required=True,
                                      help="The course attached to this purchase line",
                                      domain="[('state_course', '=', 'validated')]",
                                      ondelete='cascade'),
        'product_id' : fields.many2one('product.product', 'Product', required=True,
                                       help="The product for this purchase line"),
        'product_qty' : fields.integer('Quantity', required=True,
                                       help="The quantity of this product"),
        'product_uom' : fields.many2one('product.uom', 'Product UoM', required=True,
                                        help="The unit of mesure for this product"),
        'product_price' : fields.related('product_id', 'standard_price', type='float', digits_compute=dp.get_precision('Account'), string='Cost Price'),
        'attachment_id' : fields.many2one('ir.attachment', 'Attachment'),
        'attachment_price' : fields.related('attachment_id', 'price', type='float', digits_compute=dp.get_precision('Account'), string='Attachment Price', readonly=True),
    }

    _defaults = {
        'product_qty' : lambda *a: 1,
    }

    def on_change_product(self, cr, uid, ids, product_id, context=None):
        if not product_id:
            return {'value' : {'product_uom' : 0, 'product_price' : 0.0}}

        product = self.pool.get('product.product').browse(cr, uid, product_id)

        return {
            'value' : {
                'product_uom' : product.uom_id.id,
                'product_price' : product.standard_price,
            }
        }

    def on_change_attachment(self, cr, uid, ids, attachment_id):
        if not attachment_id:
            return {'value' : {'attachment_price' : 0.0}}

        attachment = self.pool.get('ir.attachment').browse(cr, uid, attachment_id)

        return {
            'value' : {
                'attachment_price' : attachment.price,
            }
        }

training_course_purchase_line()

class training_offer(osv.osv):
    _name = 'training.offer'

training_offer()

class training_course_theme(osv.osv):
    _name ='training.course.theme'
    _description = "Course Theme"

    _columns = {
        'name' : fields.char('Name', size=64, required=True, select=1),
        'active' : fields.boolean('Active'),
        'parent_id': fields.many2one('training.course.theme', 'Parent', select=1),
        'priority': fields.integer('Priority'),
        'description' : fields.text('Description',
                                    help="Allows to write the description of the theme"),
    }

    _defaults = {
        'active' : lambda *a: 1,
        'priority': lambda *a: 0,
    }

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

training_course_theme()

class training_course_kind(osv.osv):
    _name = 'training.course.kind'

    _columns = {
        'code' : fields.char('Code', size=16, required=True),
        'name' : fields.char('Name', size=32, translate=True, required=True),
    }

    _sql_constraints = [
        ('uniq_code', 'unique(code)', "The code of this kind must be unique"),
    ]
training_course_kind()

def training_course_kind_compute(obj, cr, uid, context=None):
    proxy = obj.pool.get('training.course.kind')
    return [(kind.code, kind.name) for kind in proxy.browse(cr, uid, proxy.search(cr, uid, []))] or []

class training_course_offer_rel(osv.osv):
    _name = 'training.course.offer.rel'

    _columns = {
        'sequence' : fields.integer('Sequence'),
        'course_id' : fields.many2one('training.course', 'Course', required=True, select=1, ondelete='cascade'),
        'offer_id' : fields.many2one('training.offer', 'Offer', required=True, select=1, ondelete='cascade'),
        'category_id' : fields.related('course_id', 'category_id', type='many2one', relation='training.course_category',  string='Product Line', readonly=True),
        'course_type_id' : fields.related('course_id', 'course_type_id', type='many2one', relation='training.course_type', string='Course Type', readonly=True),
        'lang_id' : fields.related('course_id', 'lang_id', type='many2one', relation='res.lang', string='Language', readonly=True),
        'kind': fields.related('course_id','kind', type='selection', selection=training_course_kind_compute, string='Course Kind', readonly=True),
        'duration' : fields.related('course_id', 'duration', type='float', string='Duration', readonly=True),
    }

    _sql_constraints = [
        ('uniq_course_offer', 'unique(course_id, offer_id)', "You cannot have twice courses in this offer"),
    ]

    def on_change_course(self, cr, uid, ids, course_id, context=None):
        if not course_id:
            return False

        course = self.pool.get('training.course').browse(cr, uid, course_id, context=context)

        return {
            'value' : {
                'category_id' : course.category_id.id,
                'course_type_id' : course.course_type_id.id,
                'lang_id' : course.lang_id.id,
                'duration' : course.duration,
            }
        }

    _order = 'sequence asc'

training_course_offer_rel()

class training_course(osv.osv):
    _name = 'training.course'
    _description = 'Course'
    _inherits = {
        'account.analytic.account' : 'analytic_account_id'
    }

    def _total_duration_compute(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, 0.0)

        if 'offer_id' in context:
            context = context.copy()
            del context['offer_id']

        for course in self.browse(cr, uid, ids, context=context):
            res[course.id] = reduce(lambda acc, child: acc + child.duration, course.course_ids, 0.0)

        return res

    def _has_support(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, 0)
        cr.execute("SELECT res_id, count(1) "
                   "FROM ir_attachment "
                   "WHERE res_id in ("+ ",".join(['%s'] * len(ids)) + ")"
                   "AND res_model = 'training.course' "
                   "AND is_support = %s "
                   "GROUP BY res_id",
                   ids + [True],
        )
        res.update(dict([(x[0], bool(x[1])) for x in cr.fetchall()]))

        return res

    def action_workflow_pending(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state_course' : 'pending'}, context=context)

    def test_course_for_validation(self, cr, uid, ids, context=None):
        return True

    def _duration_compute(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, 0.0)

        if 'offer_id' in context:
            context=context.copy()
            del context['offer_id']

        for course in self.browse(cr, uid, ids, context=context):
            res[course.id] = len(course.course_ids) and course.duration_with_children or course.duration_without_children

        return res

    def _with_children_compute(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, 0.0)

        if 'offer_id' in context:
            context = context.copy()
            del context['offer_id']

        for course in self.browse(cr, uid, ids, context=context):
            res[course.id] = bool(len(course.course_ids))

        return res

    def _price_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0.0)

        proxy = self.pool.get('ir.attachment')

        for course in self.browse(cr, uid, ids, context=context):
            support_ids = proxy.search(cr, uid,
                                       [('res_model', '=', self._name),
                                        ('res_id', '=', course.id),
                                        ('is_support', '=', 1)],
                                       context=context)
            price = reduce(lambda acc, support: acc + support.price,
                          proxy.browse(cr, uid, support_ids, context=context),
                           0.0)

            res[course.id] = price

        return res

    def _attachment_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, [])
        proxy = self.pool.get('ir.attachment')
        for course in self.browse(cr, uid, ids, context=context):
            res[course.id] = proxy.search(cr, uid,
                                          [('res_model', '=', self._name),
                                           ('res_id', '=', course.id),
                                           ('is_support', '=', 1)],
                                          context=context
                                         )

        return res

    def _get_support(self, cr, uid, ids, context=None):
        proxy = self.pool.get('ir.attachment')
        attach_ids = proxy.search(cr, uid, [('id', 'in', ids),('res_model', '=', 'training.course'),('is_support', '=', 1)], context=context)
        res = set()
        for attach in proxy.browse(cr, uid, attach_ids, context=context):
            res.add(attach.res_id)

        return list(res)

    _columns = {
        'splitted_by' : fields.selection([('2', '2 Hours'),
                                          ('4', '4 Hours'),
                                          ('8', '8 Hours')
                                         ],
                                         'Splitted By',
                                         required=True),
        'price' : fields.function(_price_compute,
                                  method=True,
                                  string='Price',
                                  type='float',
                                  digits_compute=dp.get_precision('Account'),
                                  #store = {
                                  #    'ir.attachment' : (_get_support, None, 10),
                                  #},
                                  help='The price of the support of the courses'),
        'theme_ids' : fields.many2many('training.course.theme', 'training_course_theme_rel', 'course_id',
                                      'theme_id', 'Theme'),

        'duration' : fields.function(_duration_compute,
                                     method=True,
                                     string='Duration',
                                     type='float',
                                     store=True,
                                     help='The duration of the course'),

        'duration_with_children':fields.function(_total_duration_compute,
                                                 method=True,
                                                 string='Duration',
                                                 type='float',
                                                 store=True,
                                                 help='The duration of the course'),

        'duration_without_children':fields.float('Duration',
                                                 help="The duration of the course"),

        'with_children': fields.function(_with_children_compute,
                                         method=True,
                                         string='With Children',
                                         store=True,
                                         type='boolean',
                                         help='Allows to know if the course contains some subcourses or not'),

        'p_id' : fields.many2one('training.course',
                                 'Parent Course',
                                 help="The parent course",
                                 readonly=True,
                                 domain="[('state_course', '=', 'validated')]"),

        'course_ids' : fields.one2many('training.course',
                                       'p_id',
                                       "Sub Courses",
                                       help="A course can be completed with some subcourses"),

        'sequence' : fields.integer('Sequence',
                                    help="The sequence can help the user to reorganize the order of the courses"),

        'reference_id' : fields.many2one('training.course',
                                         'Master Course',
                                         help="The master course is necessary if the user wants to link certain courses together to easy the managment",
                                        ),
        'child_reference_id' : fields.one2many('training.course', 'reference_id', 'Children'),

        'reference_lang_id' : fields.related('reference_id', 'lang_id', type='many2one', relation='res.lang', string="Master Course's Language", readonly=True),
        'reference_type' : fields.related('reference_id', 'course_type_id', type='many2one', relation='training.course_type', string="Master Course's Type", readonly=True),
        'analytic_account_id' : fields.many2one('account.analytic.account', 'Account'),
        'course_type_id' : fields.many2one('training.course_type', 'Type', select=1),
        'category_id': fields.many2one('training.course_category', 'Product Line', select=1),

        'lecturer_ids' : fields.many2many('res.partner.job', 'training_course_job_rel', 'course_id', 'job_id', 'Lecturers',
                                          select=1,
                                          help="The lecturers who give the course"),

        'internal_note' : fields.text('Note',
                                      translate=True,
                                      help="The user can write some internal note for this course"),

        'lang_id' : fields.many2one('res.lang',
                                    'Language',
                                    required=True,
                                    select=1,
                                    domain=[('active', '=', True), ('translatable', '=', True)],
                                    help="The language of the course"),
        'kind': fields.selection(training_course_kind_compute,
                                 'Kind',
                                 required=True,
                                 select=2,
                                 help="The kind of course"),

        'state_course' : fields.selection([('draft', 'Draft'),
                                           ('pending', 'Ask Review'),
                                           ('deprecated', 'Deprecated'),
                                           ('validated', 'Validated'),
                                          ],
                                          'State',
                                          required=True,
                                          readonly=True,
                                          select=1,
                                          help="The state of the course"
                                         ),

        'purchase_line_ids' : fields.one2many('training.course.purchase_line', 'course_id',
                                              'Supplier Commands',
                                              help="The purchase line helps to create a purchase order for the seance"),


        'has_support' : fields.function(_has_support,
                                        method=True,
                                        type="boolean",
                                        store={
                                            'ir.attachment' : (_get_support, None, 10),
                                        },
                                        select=2,
                                        string="Has Support"),

        'long_name' : fields.char('Long Name',
                                     size=256,
                                     select=1,
                                     help='Allows to show the long name of the course for the external view'),

        'attachment_ids' : fields.function(_attachment_compute,
                                           method=True,
                                           string='Supports of Course',
                                           type='one2many',
                                           relation='ir.attachment'),
        'pending_ids' : fields.one2many('training.course.pending', 'course_id', 'Pendings'),

    }

    _defaults = {
        'state_course' : lambda *a: 'draft',
        'duration' : lambda *a: 1.0,
        'duration_without_children' : lambda *a: 1.0,
        'splitted_by' : lambda *a: '8',
        'kind': lambda *a: 'standard',
    }

    def _check_duration(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)
        #return (this.duration > 0.0 or this.duration_without_children > 0.0 or this.duration_with_children > 0.0)
        return this.duration_without_children > 0.0

    _constraints = [
        (_check_duration, "Please, Can you check the duration ?", ['duration']),
    ]

    def create(self, cr, uid, values, context=None):
        if 'category_id' in values:
            proxy = self.pool.get('training.course_category')
            values['parent_id'] = proxy.browse(cr, uid, values['category_id'], context).analytic_account_id.id
        return super(training_course, self).create(cr, uid, values, context)

    def write(self, cr, uid, ids, values, context=None):
        if 'category_id' in values:
            proxy = self.pool.get('training.course_category')
            values['parent_id'] = proxy.browse(cr, uid, values['category_id'], context).analytic_account_id.id
        return super(training_course, self).write(cr, uid, ids, values, context)

    def on_change_reference(self, cr, uid, ids, reference_id, context=None):
        if not reference_id:
            return False

        values = {
            'duration' : 0.0,
            'course_type_id' : 0,
            'category_id' : 0,
        }

        if reference_id:
            course = self.browse(cr, uid, reference_id, context=context)
            new_val = {
                'theme_ids' : [ x.id for x in course.theme_ids],
                'course_type_id' : course.course_type_id.id,
                'category_id' : course.category_id.id,
            }

            values.update(new_val)

        return {'value' : values}

    def search(self, cr, uid, domain, offset=0, limit=None, order=None, context=None, count=False):
        link_id = context and context.get('link_id', False) or False
        has_master_course = context and ('master_course' in context) or False

        if link_id:

            course = self.browse(cr, uid, link_id, context=context)

            reference_id = course.reference_id and course.reference_id.id or course.id

            res = super(training_course, self).search(cr, uid, [('reference_id', '=', reference_id)], context=context)
            if course.reference_id:
                res += [course.reference_id.id]

            return list(set(res))

        if has_master_course:
            return list(set(super(training_course, self).search(cr, uid, [('reference_id', '!=', False)], context=context)))

        offer_id = context and context.get('offer_id', False) or False

        if offer_id:
            proxy = self.pool.get('training.course.offer.rel')
            ids = proxy.search(cr, uid, [('offer_id', '=', offer_id)], context=context)
            return [rel.course_id.id for rel in proxy.browse(cr, uid, ids, context=context)]

        return super(training_course, self).search(cr, uid, domain, offset=offset,
                                                   limit=limit, order=order, context=context, count=count)

    def action_workflow_validate(self, cr, uid, ids, context=None):
        proxy = self.pool.get('training.course.pending')
        for course_id in ids:
            pending_ids = proxy.search(cr, uid, [('course_id', '=', course_id)], context=context)
            proxy.write(cr, uid, pending_ids, {'todo' : 1}, context=context)

        return self.write(cr, uid, ids, {'state_course' : 'validated'}, context=context)

    def reset_to_draft(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')

        for oid in ids:
            workflow.trg_create(uid, self._name, oid, cr)

        return self.write(cr, uid, ids, {'state' : 'draft'}, context=context)

training_course()

class training_offer_public_target(osv.osv):
    _name = 'training.offer.public.target'
    _columns = {
        'name':fields.char('Name',
                           translate=True,
                           size=256,
                           select=1,
                           help="Allows to the participants to select a course whose can participate"),
        'note' : fields.text('Target Audience', translate=True),
    }

    _sql_constraints = [
        ('target_name', 'unique (name)', 'The name must be unique !')
    ]

training_offer_public_target()

class training_offer_kind(osv.osv):
    _name = 'training.offer.kind'

    _columns = {
        'code' : fields.char('Code', size=16, required=True),
        'name' : fields.char('Name', size=32, translate=True, required=True),
    }

    _sql_constraints = [
        ('uniq_code', 'unique(code)', "The code of this kind must be unique"),
    ]

training_offer_kind()

class training_offer_format(osv.osv):
    _name = 'training.offer.format'
    _description = "The delivery format of the offer or session"

    _columns = {
        'name' : fields.char('Name', size=32, required=True, select=1, help="The format's name of the offer or session"),
        'active' : fields.boolean('Active'),
    }

    _defaults = {
        'active' : lambda *a: 1,
    }

training_offer_format()

class training_offer_purchase_line_update_wizard(osv.osv_memory):
    _name = 'training.offer.purchase.line.update.wizard'
    _columns = {
        'name': fields.char('Summary', size=256),
        'log': fields.text('Log Text'),
        'date': fields.datetime('Date'),
        'state': fields.selection([('confirm','Confirm'),('update','Update')]),
    }

    _defaults = {
        'state': lambda *a: 'confirm',
    }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close' }

    def action_close(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close' }

    def action_confirm(self, cr, uid, ids, context=None):
        offer_proxy = self.pool.get('training.offer')
        offer_id = context.get('active_id', False)
        val = offer_proxy.action_update_seance_procurements(cr, uid, offer_id, context=context)
        if val:
            val['state'] = 'update'
        else:
            val = { 'name': _('FAILED')}
        return self.write(cr, uid, ids, val, context=context)

training_offer_purchase_line_update_wizard()

class training_offer_purchase_line_log(osv.osv):
    _name = 'training.offer.purchase.line.log'
    _columns = {
        'offer_id': fields.many2one('training.offer', 'Offer', required=True),
        'name': fields.char('Summary', size=256, required=True),
        'log': fields.text('Log Text', required=True),
        'date': fields.datetime('Date', required=True),
    }
training_offer_purchase_line_log()

class training_offer_purchase_line(osv.osv):
    _name = 'training.offer.purchase.line'
    _rec_name = 'offer_id'
    _columns = {
        'offer_id' : fields.many2one('training.offer', 'Offer', required=True,
                                      domain="[('state_course', '=', 'validated')]", ondelete='cascade'),
        'product_id' : fields.many2one('product.product', 'Product', required=True,
                                       help="The product for this purchase line"),
        'description' : fields.char('Description', size=128),
        'product_qty' : fields.integer('Quantity', required=True,
                                       help="The quantity of this product"),
        'product_uom' : fields.many2one('product.uom', 'Product UoM', required=True,
                                        help="The unit of mesure for this product"),
        'product_price' : fields.related('product_id', 'standard_price', type='float',
                                         digits_compute=dp.get_precision('Account'),
                                         string='Cost Price'),
        'attachment_id' : fields.many2one('ir.attachment', 'Attachment'),
        'attachment_price' : fields.related('attachment_id', 'price', type='float',
                                            digits_compute=dp.get_precision('Account'),
                                            string='Attachment Price', readonly=True),
        'fix' : fields.selection([('fix', 'Fix'),('by_subscription', 'By Subscription')], 'Invoiced Quantity', required=True),
        'procurement_quantity' : fields.selection([('on_first_seance', 'On First Seance'),
                                                   ('on_all_seances', 'On All Seances'),
                                                   ('on_seance_course', 'Relative to the course'),
                                                   ('on_last_seance', 'On Last Seance'),
                                                  ],
                                                  'Trigger',
                                                  required=True),
        'course_id' : fields.many2one('training.course', 'Course'),
        'auto_update': fields.boolean('Auto. Update'),
    }

    _defaults = {
        'product_qty' : lambda *a: 1,
        'fix' : lambda *a: 'fix',
        'procurement_quantity' : lambda *a: 'on_first_seance',
        'auto_update': lambda *a: True,
    }

    def on_change_product(self, cr, uid, ids, product_id, context=None):
        if not product_id:
            return {'value' : {'product_uom' : 0, 'product_price' : 0.0}}

        product = self.pool.get('product.product').browse(cr, uid, product_id)

        proxy = self.pool.get('training.config.product')
        ids = proxy.search(cr, uid,
                           [('type', 'in', ('support_of_course','voucher')),
                            ('product_id', '=', product.id)
                           ],
                           context=context)
        conf = None
        if ids:
            conf = proxy.browse(cr, uid, ids[0], context)
        fix = ids and 'by_subscription' or 'fix'
        qty = (conf and conf.type == 'voucher') and 'on_all_seances' or 'on_first_seance'
        return {
            'value' : {
                'product_uom' : product.uom_id.id,
                'product_price' : product.standard_price,
                'fix' : fix,
                'procurement_quantity': qty,
                'description' : product.name,
            }
        }

    def on_change_attachment(self, cr, uid, ids, attachment_id):
        if not attachment_id:
            return {'value' : {'attachment_price' : 0.0}}

        attachment = self.pool.get('ir.attachment').browse(cr, uid, attachment_id)

        return {
            'value' : {
                'attachment_price' : attachment.price,
            }
        }

training_offer_purchase_line()


def training_offer_kind_compute(obj, cr, uid, context=None):
    proxy = obj.pool.get('training.offer.kind')
    return [(kind.code, kind.name) for kind in proxy.browse(cr, uid, proxy.search(cr, uid, []))] or []

class training_offer(osv.osv):
    _name = 'training.offer'
    _description = 'Offer'

    def on_change_course_ids(self, cr, uid, ids, course_ids, context=None):
        values = {
            'type_id' : 0,
            'product_line_id' : 0,
        }

        if len(course_ids) == 1:
            course = self.pool.get('training.course').browse(cr, uid, course_ids[0][2]['course_id'])

            values.update({
                'name' : course.name,
                'type_id' : course.course_type_id.id,
                'product_line_id' : course.category_id.id,
            })

        # Creer un bouton 'draft' qui rebalance en draft quand une offre est deja deprecated
        return {'value' : values}

    def _is_standalone_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)
        for offer in self.browse(cr, uid, ids, context=context):
            res[offer.id] = len(offer.course_ids) == 1 and 1 or 0

        return res

    def draft_cb(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')

        for offer_id in ids:
            workflow.trg_create(uid, 'training.offer', offer_id, cr)

        return self.write(cr, uid, ids, {'state' : 'draft'}, context=context)


    def action_load_procurements(self, cr, uid, ids, context=None):
        proxy = self.pool.get('training.offer.purchase.line')
        for offer in self.browse(cr, uid, ids, context=context):
            for course_offer_rel in offer.course_ids:
                for purchase_line in course_offer_rel.course_id.purchase_line_ids:
                    proxy_config = self.pool.get('training.config.product')
                    config_ids = proxy_config.search(cr, uid,
                                              [('type', 'in', ('support_of_course','voucher')),
                                               ('product_id', '=', purchase_line.product_id.id)
                                              ],
                                              context=context)
                    values = {
                        'offer_id' : offer.id,
                        'product_id' : purchase_line.product_id.id,
                        'product_qty' : purchase_line.product_qty,
                        'product_uom' : purchase_line.product_uom.id,
                        'attachment_id' : purchase_line.attachment_id and purchase_line.attachment_id.id,
                        'course_id' : course_offer_rel.course_id.id,
                        'procurement_quantity' : 'on_first_seance',
                        'fix' : config_ids and 'by_subscription' or 'fix'
                    }
                    proxy.create(cr, uid, values, context=context)

        return True

    def action_update_seance_procurements(self, cr, uid, ids, context=None):
        session_proxy = self.pool.get('training.session')
        seance_proxy = self.pool.get('training.seance')
        group_proxy = self.pool.get('training.group')
        offer_pol_proxy = self.pool.get('training.offer.purchase.line')
        seance_pol_proxy = self.pool.get('training.seance.purchase_line')
        offer_id = isinstance(ids, (int,long)) and ids or ids[0]
        today = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')

        log_proxy = self.pool.get('training.offer.purchase.line.log')
        log = []
        log_seance_cnt = 0

        def create_purchase_lines(purchase_line_ids, seance):
            result = []
            proxy = self.pool.get('training.seance.purchase_line')
            for pl in purchase_line_ids:
                # only ambigious case: purchase line per course
                if pl.procurement_quantity == 'on_seance_course':
                    if not (pl.course_id and pl.course_id.id == seance['course_id'][0]):
                        # not course on purchase line, or differ from seance's one
                        continue

                if pl.attachment_id:
                    product_price = pl.attachment_price
                    description = "%s (%s)" % (pl.product_id.name, pl.attachment_id.datas_fname)
                else:
                    product_price = pl.product_price
                    description = pl.description or pl.product_id.name

                if pl.description:
                    description = "%s - %s" % (description, pl.description,)

                values = {
                    'seance_id' : seance['id'],
                    'course_id': pl.course_id.id,
                    'product_id' : pl.product_id.id,
                    'description' : description,
                    'product_qty' : pl.product_qty,
                    'product_uom' : pl.product_uom.id,
                    'product_price' : product_price,
                    'fix' : pl.fix,
                    'attachment_id' : pl.attachment_id and pl.attachment_id.id,
                }
                result.append((0, 0, values))
            return result

        # get offer purchase lines (auto_update = True),
        # and group them by 'procurement_quantity' (aka trigger)
        offer_pol_ids = offer_pol_proxy.search(cr, uid, [('offer_id','=',offer_id)])
        offer_pol = {} # PO lines by trigger
        for pol in offer_pol_proxy.browse(cr, uid, offer_pol_ids):
            if pol.auto_update:
                offer_pol.setdefault(pol.procurement_quantity, []).append(pol)

        futur_sessions_ids = session_proxy.search(cr, uid, [('offer_id','=',offer_id),('date','>=',today)])
        for session in session_proxy.read(cr, uid, futur_sessions_ids, ['name', 'seance_ids'], context=context):
            log.append("SESSION: %s" % (session['name']))

            # group seance by 'group_id'
            seance_by_group = {}
            seance_ids = seance_proxy.search(cr, uid, [('id','in',session['seance_ids']),('state','!=','cancelled')], order='date')
            for seance in seance_proxy.read(cr, uid, seance_ids, ['is_first_seance','state','course_id','purchase_line_ids','group_id','date', 'name']):
                seance_by_group.setdefault(seance['group_id'], []).append(seance)

            for group, seances in seance_by_group.iteritems():
                # get remarquable idx
                first_seance_idx = 0
                last_seance_idx = len(seances) and (len(seances) - 1) or 0

                for idx, seance in enumerate(seances):
                    s_pol_updates = []

                    # get all purchase line in automatic (will be deleted)
                    pol_ids_to_del = seance_pol_proxy.search(cr, uid, [('seance_id','=',seance['id']),('auto_update','=',True)])
                    s_pol_updates.extend([(2, id) for id in pol_ids_to_del])

                    extra_info = ''
                    # compute purchase line depending on trigger
                    if idx == first_seance_idx:
                        extra_info += 'first'
                        s_pol_updates.extend(create_purchase_lines(offer_pol.get('on_first_seance', []), seance))
                    if idx == last_seance_idx:
                        extra_info += 'last'
                        s_pol_updates.extend(create_purchase_lines(offer_pol.get('on_last_seance', []), seance))
                    s_pol_updates.extend(create_purchase_lines(offer_pol.get('on_all_seances', []), seance))
                    s_pol_updates.extend(create_purchase_lines(offer_pol.get('on_seance_course', []), seance))

                    if seance['state'] != 'opened':
                        # opened = draft, after that state, seance purchase order are already existing
                        continue
                    log_seance_cnt += 1
                    log.append("    %s (%s) / %s" % (seance['name'], seance['date'], (seance['group_id'] and seance['group_id'][1] or '')))

                    seance_proxy.write(cr, uid, [seance['id']], {'purchase_line_ids': s_pol_updates})

        log_values = {
            'name': _('%d seance(s) updated') % (log_seance_cnt),
            'date': today,
            'log': u'\n'.join(log),
            'offer_id': offer_id,
        }
        new_log_id = log_proxy.create(cr, uid, log_values)
        if new_log_id:
            retval = log_values.copy()
            del retval['offer_id']
            return retval
        return None

    def _duration_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0.0)

        for offer in self.browse(cr, uid, ids, context=context):
            res[offer.id] = reduce(lambda acc,obj: acc + obj.course_id.duration, offer.course_ids, 0.0)

        return res

    def can_be_planned_search(self, cr, uid, context=None):
        return self.search(cr, uid, [('state', '=', 'validated')], context=context)

    def can_be_planned_compute(self, cr, uid, ids, context=None):
        return dict((obj.id, obj.state == 'validated') for obj in self.browse(cr, uid, ids, context=context))

    def _can_be_planned_search(self, cr, uid, obj, name, args, context=None):
        if not len(args):
            return []

        return [('id', 'in', self.can_be_planned_search(cr, uid, context=context))]

    def _can_be_planned_compute(self, cr, uid, ids, fields, args, context=None):
        return self.can_be_planned_compute(cr, uid, ids, context=context)

    def is_planned_compute(self, cr, uid, ids, fname, args, context=None):
        return dict.fromkeys(ids, True)

    def is_planned_search(self, cr, uid, obj, name, args, context=None):
        if not len(args):
            return []
        cond = " = 0";
        for arg in args:
            if arg[0] == 'is_planned':
                if arg[2] == True:
                    cond = " > 0" # True
                else:
                    cond = " = 0" # False
                break
        cr.execute("""
            SELECT
                toff.id,count(ts.id)
            FROM
                training_offer toff
            LEFT JOIN
                training_session ts ON ts.offer_id = toff.id
            GROUP BY
                toff.id
            HAVING count(ts.id) %s;""" % (cond))
        res = [ x['id'] for x in cr.dictfetchall() ]
        return [('id', 'in', res)]

    _columns = {
        'product_line_id' : fields.many2one('training.course_category', 'Product Line', select=1, required=True),

        'type_id' : fields.many2one('training.course_type', 'Type'),
        'name' : fields.char('Name',
                             size=64,
                             required=True,
                             select=1,
                             help="The name's offer"),
        'product_id' : fields.many2one('product.product',
                                       'Product',
                                       help="An offer can be a product for invoicing",
                                      ),
        'course_ids' : fields.one2many('training.course.offer.rel', 'offer_id', 'Courses', help='An offer can contain some courses'),
        'duration' : fields.function(_duration_compute,
                                     method=True,
                                     string='Duration',
                                     type='float',
                                    ),
        'objective' : fields.text('Objective',
                                  help='The objective of the course will be used by the internet web site'
                                 ),
        'description' : fields.text('Description',
                                    help="Allows to write the description of the course"),
        'requeriments' : fields.text('Requeriments',
                                    help="Allows to write the requeriments of the course"),
        'management' : fields.text('Management',
                                    help="Allows to write the management of the course"),
        'sequence' : fields.integer('Sequence', help="Allows to order the offers by its importance"),
        'format_id' : fields.many2one('training.offer.format', 'Format', required=True, select=1,
                                    help="Delivery format of the course"),
        'state' : fields.selection([('draft', 'Draft'),
                                    ('validated', 'Validated'),
                                    ('deprecated', 'Deprecated')
                                   ],
                                   'State',
                                   required=True,
                                   readonly=True,
                                   select=1,
                                   help="The status of the course",
                                  ),
        'kind' : fields.selection(training_offer_kind_compute,
                                  'Kind',
                                  required=True,
                                  select=1),
        'target_public_id' : fields.many2one('training.offer.public.target',
                                          'Target Audience', select=1,
                                          help="Set the target audience"),
        'lang_id' : fields.many2one('res.lang', 'Language'),
        'create_date' : fields.datetime('Create Date', readonly=True),

        'preliminary_offer_ids' : fields.many2many('training.offer',
                                                   'training_offer_pre_offer_rel',
                                                   'offer_id',
                                                   'prel_offer_id',
                                                   'Preliminary Offers',
                                                   domain="[('state', '=', 'validated')]"),

        'complementary_offer_ids' : fields.many2many('training.offer',
                                                     'training_offer_cpl_offer_rel',
                                                     'offer_id',
                                                     'cpl_offer_id',
                                                     'Complementary Offers',
                                                     domain="[('state', '=', 'validated')]"),

        'included_offer_ids' : fields.many2many('training.offer',
                                                     'training_offer_incl_offer_rel',
                                                     'offer_id',
                                                     'incl_offer_id',
                                                     'Included Offers',
                                                     domain="[('state', '=', 'validated')]"),

        'is_standalone' : fields.function(_is_standalone_compute,
                                          method=True,
                                          string='Is Standalone',
                                          type="boolean",
                                          help="Allows to know if an offer is standalone or a block of courses"),

        'purchase_line_ids' : fields.one2many('training.offer.purchase.line',
                                              'offer_id',
                                              'Procurements'),
        'purchase_line_log_ids': fields.one2many('training.offer.purchase.line.log',
                                              'offer_id',
                                              'Procurements Logs'),
        'theme_ids' : fields.many2many('training.course.theme', 'training_offer_them_rel', 'offer_id',
                                      'theme_id', 'Theme'),
        'notification_note': fields.text('Notification Note', help='This note will be show on notification emails'),
        'is_certification': fields.boolean('Is a certification?', help='Indicate is this Offer is a Certification Offer'),

        'can_be_planned' : fields.function(_can_be_planned_compute, method=True,
                                           fnct_search=_can_be_planned_search,
                                           type='boolean',
                                           string='Can Be Planned'),

        'is_planned': fields.function(is_planned_compute, method=True,
                                      fnct_search=is_planned_search,
                                      type='boolean',
                                      string='Is Planned'),
    }

    _defaults = {
        'state' : lambda *a: 'draft',
        'kind' : lambda *a: 'standard',
        'is_certification': lambda *a: False,
    }

    def search(self, cr, uid, domain, offset=0, limit=None, order=None, context=None, count=False):
        course_id = context and context.get('course_id', False) or False

        if course_id:
            cr.execute("""SELECT offer_id FROM training_course_offer_rel WHERE course_id = %s""", (course_id,))
            return [x[0] for x in cr.fetchall()]

        offer_id = context and context.get('offer_id', False) or False

        if offer_id:
            cr.execute("""SELECT course_id FROM training_course_offer_rel WHERE offer_id = %s""", (offer_id,))
            return [x[0] for x in cr.fetchall()]

        return super(training_offer, self).search(cr, uid, domain, offset=offset, limit=limit, order=order, context=context, count=count)

    def action_workflow_deprecate(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'deprecated'}, context=context)

training_offer()

class training_session(osv.osv):
    _name = 'training.session'

training_session()

class training_catalog(osv.osv):
    _name = 'training.catalog'
    _description = 'Catalog'
    _columns = {
        'name' : fields.char('Title', size=64, required=True, select=1),
        'year' : fields.integer('Year',
                                size=4,
                                required=True,
                                select=1,
                                help="The year when the catalog has been published",
                               ),
        'session_ids' : fields.one2many('training.session',
                                        'catalog_id',
                                        'Sessions',
                                        help="The sessions in the catalog"),
        'note' : fields.text('Note',
                             translate=True,
                             help="Allows to write a note for the catalog"),
        'state' : fields.selection([('draft','Draft'),
                                    ('validated', 'Validated'),
                                    ('inprogress', 'In Progress'),
                                    ('deprecated', 'Deprecated'),
                                    ('cancelled','Cancelled'),
                                   ],
                                   'State',
                                   required=True,
                                   readonly=True,
                                   select=1,
                                   help="The status of the catalog",
                                  ),
    }

    _defaults = {
        'year' : lambda *a: int(time.strftime('%Y'))+1,
        'state' : lambda *a: 'draft',
    }

training_catalog()

def get_zip_from_directory(directory, b64enc=True):
    RE_exclude = re.compile('(?:^\..+\.swp$)|(?:\.py[oc]$)|(?:\.bak$)|(?:\.~.~$)', re.I)

    def _zippy(archive, path):
        path = os.path.abspath(path)
        base = os.path.basename(path)
        for f in tools.osutil.listdir(path, True):
            bf = os.path.basename(f)
            if not RE_exclude.search(bf):
                archive.write(os.path.join(path, f), os.path.join(base, f))

    archname = StringIO()
    archive = PyZipFile(archname, "w", ZIP_DEFLATED)
    archive.writepy(directory)
    _zippy(archive, directory)
    archive.close()
    val = archname.getvalue()
    archname.close()

    if b64enc:
        val = base64.encodestring(val)

    return val

class training_seance_generate_pdf_wizard(osv.osv_memory):
    _name = 'training.seance.generate.zip.wizard'

    _columns = {
        'presence_list_report' : fields.boolean('Presence List Report',
                                                help="If you select this option you will print the report for the presence list. " \
                                                "The file format is Presence_List_DATEOFSEANCE_SEANCEID.pdf"),
        'remuneration_form_report' : fields.boolean('Remuneration Form',
                                                    help="If you select this option, you will print the report for the remuneration " \
                                                    "forms of all contacts. The file format is Request_REQUESTNAME_Invoice_INVOICEID.pdf"),
        'zip_file' : fields.binary('Zip File', readonly=True),
        'zip_file_name' : fields.char('File name', readonly=True, size=64),
        'state' : fields.selection( [ ('selection', 'Selection'), ('result', 'Result') ], 'State', readonly=True, required=True),
    }

    _defaults = {
        'presence_list_report' : lambda *a: 0,
        'remuneration_form_report' : lambda *a: 0,
        'state' : lambda *a: 'selection',
    }

    def action_close(self, cr, uid, ids, context=None):
        return { 'type' : 'ir.actions.act_window.close' }

    def action_generate_zip(self, cr, uid, ids, context=None):
        try:
            import tempfile
            parent_directory = tempfile.mkdtemp(prefix='openerp_', suffix='_reports')
            directory = os.path.join(parent_directory, 'Reports')
            os.mkdir(directory)
            self.add_selections(cr, uid, ids, directory, context=context)
            result = get_zip_from_directory(directory, True)
            fp = file(os.path.join(parent_directory, 'output.zip'), 'w')
            fp.write(result)
            fp.close()

            active_id = context and context.get('active_id')
            seance = self.pool.get('training.seance').browse(cr, uid, active_id, context=context)
            ts = time.strptime(seance.date, '%Y-%m-%d %H:%M:%S')
            date = time.strftime('%Y%m%d', ts)

            values = {
                'state' : 'result',
                'zip_file' : result,
                'zip_file_name' : 'Seance_Reports_%s_%06d.zip' % (date, seance.id),
            }
        finally:
            import shutil
            shutil.rmtree(parent_directory)
        return self.write(cr, uid, ids, values, context=context)

    def _get_report(self, cr, uid, oid, reportname, context=None):
        srv = netsvc.LocalService(reportname)
        pdf, _ = srv.create(cr, uid, [oid], {}, context=context)
        return pdf

    def add_selections(self, cr, uid, ids, directory, context=None):
        active_id = context and context.get('active_id')
        seance = self.pool.get('training.seance').browse(cr, uid, active_id, context=context)
        ts = time.strptime(seance.date, '%Y-%m-%d %H:%M:%S')
        date = time.strftime('%Y%m%d', ts)
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.presence_list_report:
                res = self._get_report(cr, uid, active_id, 'report.training.seance.presence.report', context=context)
                filename = os.path.join(directory, 'Presence_List_%s_%06d.pdf' % (date, seance.id,))
                fp = file(filename, 'w')
                fp.write(res)
                fp.close()

            if obj.remuneration_form_report:
                for contact in seance.contact_ids:
                    if not contact.request_id:
                        raise osv.except_osv(_('Error'),
                                             _('The stakeholder %s %s has not a request') % (contact.job_id.fist_name, contact.job_id.name) )

                    if not contact.request_id.purchase_order_id:
                        raise osv.except_osv(_('Error'),
                                             _('There is no Purchase Order for a request'))

                    if not contact.request_id.purchase_order_id.invoice_id:
                        raise osv.except_osv(_('Error'),
                                             _('There is no Invoice for the Purchase Order for this request'))

                    res = self._get_report(cr, uid, contact.request_id.purchase_order_id.invoice_id.id, 'report.account.invoice', context=context)
                    filename = os.path.join(directory, 'Request_%s_Invoice_%06d.pdf' % (re.sub('/|-', '_', contact.request_id.reference),
                                                                                        contact.request_id.purchase_order_id.invoice_id.id))
                    fp = file(filename, 'w')
                    fp.write(res)
                    fp.close()

training_seance_generate_pdf_wizard()

class training_seance(osv.osv):
    _name = 'training.seance'

training_seance()

class training_group(osv.osv):
    _name = 'training.group'
    _description = 'Group'
    _columns = {
        'name': fields.char('Name', size=64, required=True, select=True, help="The group's name",),
        'session_id' : fields.many2one('training.session', 'Session', select=1, required=True, ondelete='cascade'),
        'seance_ids' : fields.one2many('training.seance', 'group_id', 'Seances', readonly=True),
    }

    _sql_constraints = [
        ('uniq_name_session', 'unique(name, session_id)', 'It already exists a group with this name'),
    ]

training_group()

class training_session(osv.osv):
    _name = 'training.session'
    _description = 'Session'
    _order = 'date desc, name'

    def _has_shared_seances_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, False)
        for session in self.browse(cr, uid, ids, context=context):
            res[session.id] = any(seance.shared for seance in session.seance_ids)

        return res

    # training.session
    #def _name_compute(self, cr, uid, ids, name, args, context=None):
    #    res = dict.fromkeys(ids, '')

    #    for obj in self.browse(cr, uid, ids):
    #        date = time.strftime('%Y-%m-%d', time.strptime(obj.date, '%Y-%m-%d %H:%M:%S'))
    #        res[obj.id] = "[%s] %s (%s)" % (obj.kind[0].upper(),
    #                                        obj.offer_id.name,
    #                                        date,)

    #    return res

    # training.session
    def _store_get_participation(self, cr, uid, ids, context=None):
        result = set()

        for line in self.pool.get('training.subscription.line').browse(cr, 1, ids, context=context):
            result.add(line.session_id.id)

        return list(result)

    def _participant_count(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)

        cr.execute("""SELECT ss.session_id, COUNT(DISTINCT(tsl.contact_id))
                        FROM training_participation tp, training_subscription_line tsl, training_session_seance_rel ss
                       WHERE tp.subscription_line_id = tsl.id
                         AND ss.seance_id = tp.seance_id
                         AND ss.session_id in (%s)
                         AND tsl.state in ('confirmed', 'done')
                    GROUP BY ss.session_id
                   """ % (','.join(['%s'] * len(ids)),),
                   ids
                  )
        for seance_id, count in cr.fetchall():
            res[seance_id] = int(count)
        return res

    # training.session
    def _confirmed_subscriptions_count(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)
        sl_proxy = self.pool.get('training.subscription.line')
        for session_id in ids:
            res[session_id] = int(sl_proxy.search_count(cr, uid, [('session_id', '=', session_id),('state', 'in', ['confirmed', 'done'])], context=context))

        return res

    # training.session
    def _available_seats_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)

        for session in self.browse(cr, uid, ids, context=context):
            if session.manual:
                value_max = session.participant_count_manual
            else:
                value_max = session.participant_count
            res[session.id] = int(session.max_limit) - int(value_max)

        return res

    # training.session
    def _draft_subscriptions_count(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)

        proxy = self.pool.get("training.subscription.line")
        for session_id in ids:
            res[session_id] = int(proxy.search_count(cr, uid, [('session_id', '=', session_id),('state', '=', 'draft')], context=context))

        return res

    # training.session
    def _limit_all(self, cr, uid, ids, fieldnames, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {'min_limit' : 0, 'max_limit' : 0}
            groups = {}
            def _add_to_group(seance_id, group_id):
                if seance_id not in groups:
                    groups[seance_id] = set()
                groups[seance_id].add(group_id)

            if len(obj.seance_ids) > 0:
                seances = iter(obj.seance_ids)
                seance = seances.next()
                if seance.group_id:
                    _c = seance.course_id and seance.course_id.id or 0
                    _add_to_group(_c, seance.group_id.id)
                value_min = seance.min_limit
                value_max = seance.max_limit

                for seance in seances:
                    if seance.group_id:
                        _c = seance.course_id and seance.course_id.id or 0
                        _add_to_group(_c, seance.group_id.id)
                    value_min = min(seance.min_limit, value_min)
                    value_max = min(seance.max_limit, value_max)

                max_groups = 0
                for v in groups.values():
                    if len(v) > max_groups:
                        max_groups = len(v)
                res[obj.id]['min_limit'] = value_min
                res[obj.id]['max_limit'] = value_max * max(max_groups, 1)

        return res

    def _min_limit_reached(self, cr, uid, ids, fn, args, context=None):
        result = dict.fromkeys(ids, False)
        for session in self.browse(cr, uid, ids, context):
            count = ['participant_count', 'participant_count_manual'][session.manual]
            result[session.id] =  session[count] >= session.min_limit
        return result

    # training.session
    def _store_get_seances(self, cr, uid, ids, context=None):
        values = set()

        for obj in self.pool.get('training.seance').browse(cr, uid, ids, context=context):
            for session in obj.session_ids:
                values.add(session.id)

        return list(values)

    _columns = {
        'id' : fields.integer('Seance ID', readonly=True),
        'has_shared_seances' : fields.function(_has_shared_seances_compute,
                                               method=True,
                                               type='boolean',
                                               string="Has Shared Seances",
                                               help="Allows to know if the session has a shared seance"
                                              ),
        'name' : fields.char('Name', size=64, required=True, select=1),
        #'name' : fields.function(_name_compute,
        #                         method=True,
        #                         type="char",
        #                         size=64,
        #                         select=1,
        #                         store=True,
        #                         string='Name',
        #                         help="The session's name"),
        'state' : fields.selection([('draft', 'Draft'),
                                    ('opened', 'Opened'),
                                    ('opened_confirmed', 'Confirmed'),
                                    ('closed_confirmed', 'Closed Subscriptions'),
                                    ('inprogress', 'In Progress'),
                                    ('closed', 'Closed'),
                                    ('cancelled', 'Cancelled')],
                                   'State',
                                   required=True,
                                   readonly=True,
                               select=1,
                               help="The status of the session",
                                  ),
        'group_ids' : fields.one2many('training.group', 'session_id', 'Group', readonly=True),
        'done' : fields.boolean('Done'),
        'offer_id' : fields.many2one('training.offer',
                                     'Offer',
                                     select=1,
                                     required=True,
                                     help="Allows to select a validated offer for the session",
                                     domain="[('state', '=', 'validated')]"
                                    ),
        'offer_product_line_id' : fields.related('offer_id', 'product_line_id', type='many2one', relation='training.course_category', select=1, string='Product Line'),
        'kind' : fields.related('offer_id',
                                'kind',
                                type='selection',
                                selection=training_offer_kind_compute,
                                string='Kind',
                                readonly=True),
        'catalog_id' : fields.many2one('training.catalog', 'Catalog',
                                       select=1,
                                       help="Allows to select a published catalog"
                                      ),
        'seance_ids' : fields.many2many('training.seance',
                                        'training_session_seance_rel',
                                        'session_id',
                                        'seance_id',
                                        'Seances',
                                        ondelete='cascade',
                                        help='List of the events in the session'),
        'date' : fields.datetime('Date',
                                 required=True,
                                 select=1,
                                 help="The date of the planned session"
                                ),
        'date_end' : fields.datetime('End Date',
                                 help="The end date of the planned session"
                                ),
        'address_id' : fields.many2one('res.partner.address', 'Training place',
                                    help='Address where the training is planned'),
        'format_id' : fields.many2one('training.offer.format', 'Format', required=True, select=2,
                                    help="Delivery format of the planned session"),
        'user_id' : fields.many2one('res.users',
                                    'Responsible',
                                    select=1,
                                    required=True),
        'available_seats' : fields.function(_available_seats_compute,
                                            method=True,
                                            string="Available Seats",
                                            help="Available Seats = Maximum Threshold - Total Confirmed Seats",
                                            type='integer'),

        'participant_count' : fields.function(_participant_count,
                                              method=True,
                                              string='Total Confirmed Seats',
                                              type='integer',
                                             ),

        'confirmed_subscriptions' : fields.function(_confirmed_subscriptions_count,
                                                    method=True,
                                                    string='Confirmed Subscriptions',
                                                    type='integer',
                                                    #store={
                                                    #    'training.subscription.line' : (_store_get_participation, None, 10),
                                                    #}
                                                   ),
        'draft_subscriptions' : fields.function(_draft_subscriptions_count,
                                                method=True,
                                                string="Draft Subscriptions",
                                                type="integer",
                                                help="Draft Subscriptions for this session",
                                               ),

        'subscription_line_ids': fields.one2many('training.subscription.line',
                                                 'session_id',
                                                 'Subscription Lines',
                                                 readonly=True),

        'participant_count_manual' : fields.integer('Manual Confirmed Seats',
                                                    help="The quantity of supports, catering, ... relative to the number of participants coming from the confirmed seats"),
        'manual' : fields.boolean('Manual', help="Allows to the user to specify the number of participants"),
        'min_limit' : fields.function(_limit_all,
                                      method=True,
                                      string='Mininum Threshold',
                                      #store={
                                      #    'training.seance' : (_store_get_seances, None, 10),
                                      #},
                                      type='integer',
                                      multi='limit',
                                      help="The minimum threshold is the minimum of the minimum threshold of each seance",
                                      readonly=True),
        'max_limit' : fields.function(_limit_all,
                                      method=True,
                                      string='Maximum Threshold',
                                      #store={
                                      #    'training.seance' : (_store_get_seances, None, 10),
                                      #},
                                      type='integer',
                                      multi='limit',
                                      help="The maximum threshold is the minimum of the maximum threshold of each seance",
                                      readonly=True),
        'min_limit_reached': fields.function(_min_limit_reached,
                                             method=True,
                                             string='Minimum Threshold Reached',
                                             type='boolean',
                                             readonly=True,
                                             store={
                                                'training.seance' : (_store_get_seances, None, 10),
                                                'training.subscription.line' : (_store_get_participation, None, 10),
                                             },
                                             ),

        'request_ids': fields.one2many('training.participation.stakeholder.request', 'session_id', 'Requests'),
        'stylegroup_id': fields.many2one('training.email.stylegroup', 'Style Group'),
    }

    _order = "date asc"

    def _check_date_before_now(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        res = obj.date >= time.strftime('%Y-%m-%d %H:%M:%S')
        return res

    def _check_date_holiday(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        date = time.strftime('%Y-%m-%d', time.strptime(obj.date, '%Y-%m-%d %H:%M:%S'))

        res = not self.pool.get('training.holiday.period').is_in_period(cr, date)
        return res

    def _check_date_of_seances(self, cr, uid, ids, context=None):
        for session in self.browse(cr, uid, ids, context=context):
            for seance in session.seance_ids:
                if seance.date < session.date:
                    return False

        return True

    _constraints = [
        #(_check_date_before_now, "You cannot create a date before now", ['date']),
        #(_check_date_holiday, "You cannot assign a date in a public holiday", ['date']),

        (_check_date_of_seances, "You have a seance with a date inferior to the session's date", ['date']),
    ]

    def _find_catalog_id(self, cr, uid, context=None):
        ids = self.pool.get('training.catalog').search(cr, uid, [('year', '=', mx.DateTime.today().year)], context=context)
        return ids and ids[0]

    _defaults = {
        'catalog_id' : _find_catalog_id,
        'state' : lambda *a: 'draft',
        'user_id' : lambda obj,cr,uid,context: uid,
        'done' : lambda *a: 0,
        'manual' : lambda *a: 0,
        'min_limit' : lambda *a: 1,
        'max_limit' : lambda *a: 1,
    }

    def _create_seance(self, cr, uid, session, context=None):
        seance_ids = []
        seance_proxy = self.pool.get('training.seance')

        holiday_proxy = self.pool.get('training.holiday.year')

        if not holiday_proxy.search(cr, uid, [('year', '=', time.strftime('%Y'))], context=context):
            raise osv.except_osv(_('Warning'),
                                 _('Please, Can you configure the holidays ?'))

        def get_list_of_courses(lst, course):
            if course.course_ids:
                for child in course.course_ids:
                    get_list_of_courses(lst, child)
            else:
                lst.append(course)

        group_proxy = self.pool.get('training.group')
        group_ids = group_proxy.search(cr, uid, [('session_id', '=', session.id)])
        if group_ids:
            group_id = group_ids[0]
        else:
            group_id = group_proxy.create(cr, uid, {'name' : _('Class %d') % (1,), 'session_id': session.id}, context=context)

        def _inner_create_seance(item, session, date, duration, master_seance_id = None):
            values = {
                'name' : self.pool.get('training.seance').on_change_course(cr, uid, [], item.id, session.kind, context=context)['value']['name'],
                'original_session_id' : session.id,
                'course_id' : item.id,
                'kind': item.kind,
                'min_limit' : item.course_type_id.min_limit,
                'max_limit' : item.course_type_id.max_limit,
                'user_id' : session.user_id.id,
                'date' : date.strftime('%Y-%m-%d %H:%M:%S'),
                'master_id' : master_seance_id,
                'duration' : duration,
                'group_id': group_id,
            }
            if session.manual:
                values['manual'] = session.manual
                values['participant_count_manual'] = session.participant_count_manual

            return seance_proxy.create(cr, uid, values, context=context)



        planned_seance_ids = []
        planned_course_ids = set()
        if session.seance_ids:
            proxy_seance = self.pool.get('training.seance')

            for seance in session.seance_ids:
                planned_course_ids.add(seance.course_id.id)
                if seance.master_id:
                    planned_seance_ids.extend(proxy_seance.search(cr, uid, [('master_id', '=', seance.master_id.id)], context=context))
                else:
                    planned_seance_ids.append(seance.id)
                    planned_seance_ids.extend(proxy_seance.search(cr, uid, [('master_id', '=', seance.id)], context=context))

        date = mx.DateTime.strptime(session.date, '%Y-%m-%d %H:%M:%S')

        seance_counter = 0

        lst = []
        for course in session.offer_id.course_ids:
            if course.course_id.id in planned_course_ids:
                continue
            tmp_lst = []
            get_list_of_courses(tmp_lst, course.course_id)

            splitted_by = int(course.course_id.splitted_by) or 8
            for item in tmp_lst:
                duration = item.duration
                while duration > 0:
                    seance_counter += 1
                    duration -= splitted_by

            lst.extend(tmp_lst)

        sdate_tuple = time.strptime(session.date, '%Y-%m-%d %H:%M:%S')
        sdate = datetime.datetime(*sdate_tuple[:7])
        sdate_incr = datetime.timedelta(days=1)

        dates = []

        # Day by day search for a valid working day
        rec = 0
        max_rec = 365
        while len(dates) < seance_counter and rec < max_rec:
            try_session_date = sdate.strftime('%Y-%m-%d')
            cr.execute(
                "SELECT count(*) "
                "FROM training_holiday_period p "
                "WHERE date(%s) >= p.date_start "
                "  AND date(%s) <= p.date_stop ",
                (try_session_date, try_session_date))
            r = cr.fetchall()
            if len(r) == 1 and r[0][0] == 0:
                dates.append(sdate)
            sdate += sdate_incr
            rec += 1

        if not dates:
            cr.execute(
                "SELECT date(%s) + s.t AS date FROM generate_series(0,%s) AS s(t)",
                (session.date, seance_counter+1))

            for x in cr.fetchall():
                dates.append(mx.DateTime.strptime(x[0] + " " + date.strftime('%H:%M:%S'), '%Y-%m-%d %H:%M:%S'))

        # later we will use date.pop() so we need to reverse date,
        # so that first date are a end of array, at poped first
        dates.reverse()

        def create_purchase_lines(purchase_line_ids, seance_id, procurement_quantity):
            proxy = self.pool.get('training.seance.purchase_line')
            for pl in purchase_line_ids:
                if pl.procurement_quantity == procurement_quantity:
                    if pl.attachment_id:
                        product_price = pl.attachment_price
                        description = "%s (%s)" % (pl.product_id.name, pl.attachment_id.datas_fname)
                    else:
                        product_price = pl.product_price
                        description = pl.description or pl.product_id.name

                    if pl.description:
                        description = "%s - %s" % (description, pl.description,)

                    values = {
                        'seance_id' : seance_id,
                        'course_id': pl.course_id.id,
                        'product_id' : pl.product_id.id,
                        'description' : description,
                        'product_qty' : pl.product_qty,
                        'product_uom' : pl.product_uom.id,
                        'product_price' : product_price,
                        'fix' : pl.fix,
                        'attachment_id' : pl.attachment_id and pl.attachment_id.id,
                    }

                    purchase_line_id = proxy.create(cr, uid, values, context=context)

        seance_id = None
        first_seance_id = None
        for item in lst:
            duration = item.duration
            splitted_by = int(item.splitted_by) or 8

            master_seance_id = None
            counter_part = 0
            while duration > 0:
                date = dates.pop()
                tmp_id = _inner_create_seance(item, session, date, duration <= splitted_by and duration or splitted_by, master_seance_id)

                proxy = self.pool.get('training.seance.purchase_line')
                for pl in session.offer_id.purchase_line_ids:
                    if pl.procurement_quantity == 'on_all_seances':
                        if pl.attachment_id:
                            product_price = pl.attachment_price
                            description = "%s (%s)" % (pl.product_id.name, pl.attachment_id.datas_fname)
                        else:
                            product_price = pl.product_price
                            description = pl.product_id.name

                        if pl.description:
                            description = "%s - %s" % (description, pl.description,)

                        values = {
                            'seance_id' : tmp_id,
                            'course_id': pl.course_id.id,
                            'product_id' : pl.product_id.id,
                            'description' : description,
                            'product_qty' : pl.product_qty,
                            'product_uom' : pl.product_uom.id,
                            'product_price' : product_price,
                            'fix' : pl.fix,
                            'attachment_id' : pl.attachment_id and pl.attachment_id.id,
                        }

                        purchase_line_id = proxy.create(cr, uid, values, context=context)

                if master_seance_id is None:
                    master_seance_id = tmp_id

                seance_ids.append(tmp_id)

                duration -= splitted_by

            seance_id = master_seance_id

            if master_seance_id:
                seance = self.pool.get('training.seance').browse(cr, uid, master_seance_id, context=context)

                proxy = self.pool.get('training.seance.purchase_line')
                for pl in session.offer_id.purchase_line_ids:
                    if pl.procurement_quantity == 'on_seance_course' and pl.course_id and pl.course_id.id == seance.course_id.id:
                        if pl.attachment_id:
                            product_price = pl.attachment_price
                            description = "%s (%s)" % (pl.product_id.name, pl.attachment_id.datas_fname)
                        else:
                            product_price = pl.product_price
                            description = pl.product_id.name

                        if pl.description:
                            description = "%s - %s" % (description, pl.description,)

                        values = {
                            'seance_id' : master_seance_id,
                            'course_id': pl.course_id.id,
                            'product_id' : pl.product_id.id,
                            'description' : description,
                            'product_qty' : pl.product_qty,
                            'product_uom' : pl.product_uom.id,
                            'product_price' : product_price,
                            'fix' : pl.fix,
                            'attachment_id' : pl.attachment_id and pl.attachment_id.id,
                        }

                        purchase_line_id = proxy.create(cr, uid, values, context=context)

            if first_seance_id is None:
                first_seance_id = seance_id

        if first_seance_id:
            self.pool.get('training.seance').write(cr, uid, [first_seance_id], {'is_first_seance' : 1}, context=context)
            create_purchase_lines(session.offer_id.purchase_line_ids, first_seance_id, 'on_first_seance')

        if seance_id != first_seance_id:
            create_purchase_lines(session.offer_id.purchase_line_ids, seance_id, 'on_last_seance')

        return list(set(seance_ids + planned_seance_ids))

    # training.session
    def action_create_seances(self, cr, uid, ids, context=None):
        for session in self.browse(cr, uid, ids, context=context):
            seance_ids = self._create_seance(cr, uid, session, context)

            self.write(cr, uid, session.id, {'seance_ids' : [(6, 0, seance_ids)]}, context=context)

        return True

    def on_change_offer(self, cr, uid, ids, offer_id, context=None):
        if not offer_id:
            return False

        offer_proxy = self.pool.get('training.offer')
        offer = offer_proxy.browse(cr, uid, offer_id, context=context)

        return {
            'value' : {
                'kind' : offer.kind,
                'name' : offer.name
            }
        }

    def on_change_date(self, cr, uid, ids, date, offer_id, context=None):
        old_date = ids and self.browse(cr, uid, ids[0], context=context).date or 0

        if self.pool.get('training.holiday.period').is_in_period(cr, date):
            return {
                'value' : {
                    'date' : old_date,
                },
                'warning' : {
                    'title' : _("Selection Date"),
                    'message' : _("You can not select this date because it is a public holiday"),
                },
            }
        return {}


    # training.session
    def _create_participation(self, cr, uid, ids, subscription_line, context=None):
        proxy = self.pool.get('training.participation')
        proxy_seance = self.pool.get('training.seance')

        if subscription_line.session_id.group_ids:
            for group in subscription_line.session_id.group_ids:
                if len(group.seance_ids) > 0:
                    for seance in group.seance_ids:
                        participation_id = proxy_seance._create_participation(cr, uid, seance, subscription_line, context=context)
                        if seance.state == 'confirmed':
                            proxy.create_procurements(cr, uid, [participation_id], delayed=True, context=context)
                    break
        else:
            for seance in subscription_line.session_id.seance_ids:
                participation_id = proxy_seance._create_participation(cr, uid, seance, subscription_line, context=context)
                if seance.state == 'confirmed':
                    proxy.create_procurements(cr, uid, [participation_id], delayed=True, context=context)

    # training.session
    def action_workflow_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'draft'}, context=context)

    # training.session
    def test_workflow_open(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if not len(obj.seance_ids):
                raise osv.except_osv(_('Warning'), _("Please, do not forget to have the seances in your session"))
            else:
                min_date = obj.date
                for seance in obj.seance_ids:
                    if seance.state == 'draft':
                        raise osv.except_osv(_('Warning'), _('Please, you have at least a draft seance'))
                    else:
                        if seance.date < obj.date:
                            raise osv.except_osv(_('Warning'), _("Please, Check the date of your seances because there is one seance with a date inferior to the session's date"))

                    min_date = min(min_date, seance.date)

        return True

    # training.session
    def action_workflow_open(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'opened'}, context=context)

    # training.session
    def action_workflow_open_confirm(self, cr, uid, ids, context=None):

        proxy = self.pool.get('training.subscription.line')
        subscription_line_ids = proxy.search(cr, uid, [('session_id', 'in', ids), ('state', '=', 'confirmed')], context=context)
        proxy.send_email(cr, uid, subscription_line_ids, 'session_open_confirmed', context)

        proxy = self.pool.get('training.participation.stakeholder')
        for session in self.browse(cr, uid, ids, context=context):
            objs = {}
            for seance in session.seance_ids:
                for contact in seance.contact_ids:
                    if contact.state == 'accepted':
                        objs.setdefault(contact.id, {}).setdefault('seances', []).append(seance)

            proxy.send_email(cr, uid, objs.keys(), 'session_open_confirmed', session, context, objs)

        return self.write(cr, uid, ids, {'state' : 'opened_confirmed'}, context=context)

    # training.session
    def test_workflow_open_confirm(self, cr, uid, ids, context=None):
        return True

        # Disabled code

        for obj in self.browse(cr, uid, ids, context=context):
            # Check the minimum for this session
            number_of_participants = proxy.search_count(cr, uid, [('session_id', '=', obj.id)], context=context)
            if number_of_participants:
                if number_of_participants <= obj.min_limit:
                    raise osv.except_osv(_('Warning'),
                                         _('The number of participants is less than the required minimal limit'))

            # Check the date of the first seance > J-X
            #date = mx.DateTime.strptime(obj.seance_ids[0].date, '%Y-%m-%d %H:%M:%S')
            #new_date = (mx.DateTime.now() + mx.DateTime.RelativeDate(days=number_of_days)).strftime('%Y-%m-%d %H:%M:%S')
            #if mx.DateTime.now() > date -mx.DateTime.strptime(new_date, '%Y-%m-%d %H:%M:%S') :
            #    raise osv.except_osv(_('Warning'),
            #                         _('There is a seance with a start date inferior to %(days)s day(s)') % values)

        return True

    # training.session
    def action_workflow_close_confirm(self, cr, uid, ids, context=None):
        #proxy = self.pool.get('training.participation.stakeholder')
        #for session in self.browse(cr, uid, ids, context):
        #    objs = {}
        #    for seance in session.seance_ids:
        #        for contact in seance.contact_ids:
        #            if contact.state == 'confirmed':
        #                objs.setdefault(contact.id, {}).setdefault('seances', []).append(seance)

        #    proxy.send_email(cr, uid, objs.keys(), '???', session, context, objs)

        return self.write(cr, uid, ids, {'state' : 'closed_confirmed'}, context=context)

    # training.session
    def action_create_invoice(self, cr, uid, ids, context=None):
        sl_proxy = self.pool.get('training.subscription.line')
        for session in self.browse(cr, uid, ids, context=context):
            sl_ids = sl_proxy.search(cr, uid, [('session_id', '=', session.id),('invoice_line_id', '=', False),('state', 'in', ('confirmed', 'done'))], context=context)
            sl_proxy.action_create_invoice(cr, uid, sl_ids, context=context)

        return True

    # training.session
    def action_workflow_inprogress(self, cr, uid, ids, context=None):
        self.action_create_invoice(cr, uid, ids, context=context)
        return self.write(cr, uid, ids, {'state' : 'inprogress'}, context=context)

    # training.session
    def action_workflow_close(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')
        proxy = self.pool.get('training.subscription.line')
        for session in self.browse(cr, uid, ids, context):
            subscription_line_ids = proxy.search(cr, uid, [('session_id', '=', session.id), ('state', '=', 'confirmed')], context=context)
            for sl_id in subscription_line_ids:
                workflow.trg_validate(uid, 'training.subscription.line', sl_id, 'signal_done', cr)

        return self.write(cr, uid, ids, {'state' : 'closed'}, context=context)

    # trainin.session
    def test_workflow_close(self, cr, uid, ids, context=None):
        return all(seance.state in ('done','cancelled') for session in self.browse(cr, uid, ids, context=context)
                                          for seance in session.seance_ids)

    # training.session
    def action_cancellation_session(self, cr, uid, ids, context=None):

        # just send emails...

        proxy = self.pool.get('training.subscription.line')
        subscription_line_ids = proxy.search(cr, uid, [('session_id', 'in', ids), ('state', '=', 'confirmed')], context=context)
        proxy.send_email(cr, uid, subscription_line_ids, 'session_confirm_cancelled', context)

        proxy = self.pool.get('training.participation.stakeholder')
        for session in self.browse(cr, uid, ids, context=context):
            objs = {}
            for seance in session.seance_ids:
                for contact in seance.contact_ids:
                    if contact.state == 'accepted':
                        objs.setdefault(contact.id, {}).setdefault('seances', []).append(seance)

            proxy.send_email(cr, uid, objs.keys(), 'session_confirm_cancelled', session, context, objs)

    # training.session
    def action_workflow_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state' : 'cancelled'}, context=context)

        workflow = netsvc.LocalService('workflow')
        for session in self.browse(cr, uid, ids, context=context):

            if not session.has_shared_seances:
                for request in session.request_ids:
                    workflow.trg_validate(uid, 'training.participation.stakeholder.request', request.id, 'signal_cancel', cr)
            else:
                ### What to do with requests to shared seances ?
                pass

            for seance in session.seance_ids:
                workflow.trg_validate(uid, 'training.seance', seance.id, 'signal_cancel', cr)

            for subline in session.subscription_line_ids:
                workflow.trg_validate(uid, 'training.subscription.line', subline.id, 'signal_cancel', cr)

        return True


    def search(self, cr, uid, domain, offset=0, limit=None, order=None, context=None, count=False):
        subscription_id = context and context.get('subscription_id', False) or False

        if subscription_id:
            proxy = self.pool.get('training.subscription.line')
            ids = proxy.search(cr, uid, [('subscription_id', '=', subscription_id)], context=context)
            return [sl.session_id.id for sl in proxy.browse(cr, uid, ids, context=context)]


        return super(training_session, self).search(cr, uid, domain, offset=offset, limit=limit, order=order, context=context, count=count)

    def copy(self, cr, uid, object_id, values, context=None):
        raise osv.except_osv(_("Error"),
                             _("You can not duplicate a session"))

training_session()

class training_subscription_mass_wizard(osv.osv_memory):
    _name = 'training.subscription.mass.wizard'
    _description = 'Mass Subscription Wizard'

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close'}

    def action_apply(self, cr, uid, ids, context=None):
        subscription_form_view = context and context.get('subscription_form_view', False) or False
        record_id = context and context.get('record_id', False) or False

        this = self.browse(cr, uid, ids)[0]

        subscription_proxy = self.pool.get('training.subscription')
        subscription_line_proxy = self.pool.get('training.subscription.line')
        subscription_line_second_proxy = self.pool.get('training.subscription.line.second')

        subscriptions = {}

        if record_id:
            for job in this.job_ids:
                for subscription_mass_line in this.session_ids:
                    sl_id = subscription_line_proxy._create_from_wizard(cr, uid, this, record_id, job, subscription_mass_line, context=context)

            return {
                'type' : 'ir.actions.act_window_close',
            }

        for job in this.job_ids:
            # if the job hasn't a partner, we put this subscription in waiting mode
            if not job.name:
                for subscription_mass_line in this.session_ids:
                    subscription_line_second_proxy._create_from_wizard(cr, uid, this, job, subscription_mass_line, context=context)

            else:
                for subscription_mass_line in this.session_ids:
                    subscriptions.setdefault(job.name.id, []).append((job, subscription_mass_line,))

        subscription_ids = []

        # We create all subscription where there is a partner associated to the job
        for partner_id, lines in subscriptions.iteritems():
            values = subscription_proxy.on_change_partner(cr, uid, [], partner_id)['value']
            values.update({
                'partner_id' : partner_id,
            })

            subscription_id = subscription_proxy.create(cr, uid, values, context=context)

            for job, subscription_mass_line in lines:
                subscription_line_proxy._create_from_wizard(cr, uid, this, subscription_id, job, subscription_mass_line, context=context)

            subscription_ids.append(subscription_id)

        return {'type' : 'ir.actions.act_window_close'}

    _columns = {
        'partner_id' : fields.many2one('res.partner', 'Partner'),
        'job_ids' : fields.many2many('res.partner.job',
                                     'tms_contact_job_rel',
                                     'ms_id',
                                     'job_id',
                                     'Contacts',
                                    ),
        'session_ids' : fields.one2many('training.subscription.mass.line', 'wizard_id', 'Sessions'),
    }

    def default_get(self, cr, uid, fields, context=None):
        record_id = context and context.get('record_id', False) or False

        res = super(training_mass_subscription_wizard, self).default_get(cr, uid, fields, context=context)

        if record_id:
            partner_id = self.pool.get('training.subscription').browse(cr, uid, record_id, context=context).partner_id.id
            res['partner_id'] = partner_id

        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        record_id = context and context.get('record_id', False) or False

        res = super(training_mass_subscription_wizard, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if record_id:
            if 'fields' in res and 'partner_id' in res['fields']:
                res['fields']['partner_id']['readonly'] = True

        return res

training_subscription_mass_wizard()

class mass_subscription_line(osv.osv_memory):
    _name = 'training.subscription.mass.line'

    _columns = {
        'wizard_id' : fields.many2one('training.subscription.mass.wizard', 'Wizard'),
        'session_id' : fields.many2one('training.session', 'Session',
                                       domain="[('state', 'in', ('opened','opened_confirmed', 'closed_confirmed', 'inprogress'))]", required=True),
        'allow_closed_session': fields.boolean('Allow Closed Session'),
        'kind' : fields.related('session_id','offer_id', 'kind',
                                type='selection',
                                selection=training_offer_kind_compute,
                                string='Kind',
                                readonly=True),
    }

    def on_change_allow_closed_session(self, cr, uid, ids, new_allow, context=None):
        if new_allow:
            return {
                'domain': {'session_id': []}
            }
        else:
            return {
                'domain': {'session_id': [('state', 'in', ('opened','opened_confirmed', 'closed_confirmed', 'inprogress'))]}
            }


    def on_change_session(self, cr, uid, ids, context=None):
        return {}

mass_subscription_line()

class training_subscription_line_second(osv.osv):
    _name = 'training.subscription.line.second'
    _rec_name='partner_id'
    _columns = {
        'job_id' : fields.many2one('res.partner.job', 'Contact', required=True),
        'partner_id' : fields.related('job_id', 'name',
                                      string='Partner',
                                      type='many2one',
                                      relation='res.partner',
                                      store=True),
        'session_id' : fields.many2one('training.session', 'Session', required=True),
    }

    def _create_from_wizard(self, cr, uid, the_wizard, job, subscription_mass_line, context=None):
        proxy = self.pool.get('training.subscription.line.second')
        values = {
            'job_id' : job.id,
            'session_id' : subscription_mass_line.session_id.id,
        }

        return proxy.create(cr, uid, values, context=context)

training_subscription_line_second()


class training_subscription(osv.osv):
    _name = 'training.subscription'

training_subscription()

class training_subscription_line(osv.osv):
    _name = 'training.subscription.line'

training_subscription_line()

class training_participation(osv.osv):
    _name = 'training.participation'
    _description = 'Participation'
    _rec_name = 'job_id'
    _order = 'seance_id, contact_lastname, contact_firstname'

    def _store_get_sublines(self, cr, uid, sl_ids, context=None):
        sublines = self.pool.get('training.subscription.line')
        result = []
        for subline in sublines.browse(cr, uid, sl_ids, context):
            result.extend(p.id for p in subline.participation_ids)
        return result

    _columns = {
        'id' : fields.integer('Database ID', readonly=True),
        'seance_id' : fields.many2one('training.seance', 'Seance', select=True, required=True, readonly=True, ondelete='cascade'),
        'seance_date' : fields.related('seance_id', 'date', type='datetime', store=True, select=1, string="Seance Date"),
        'group_id' : fields.related('seance_id', 'group_id', string='Group', type='many2one', relation='training.group', select=1, store=True, readonly=True),
        'subscription_line_id' : fields.many2one('training.subscription.line', 'Subscription Line', select=True, required=True, readonly=True, ondelete='cascade'),
        'session_id' : fields.related('subscription_line_id', 'session_id', type='many2one', relation='training.session', select=True, store=True),
        'course_id' : fields.related('seance_id', 'course_id', 'name', type='char', size=64, readonly=True,
                                     string="Course", select=2),
        'duration' : fields.related('seance_id', 'duration', string='Duration', type='float', readonly=True, store=True),
        'kind' : fields.related('seance_id', 'kind', type='selection', selection=[('standard', 'Course')], string='Kind', select=1),

        'present' : fields.boolean('Present', help="Allows to know if a participant was present or not", select=1),

        'subscription_id' : fields.related('subscription_line_id', 'subscription_id',
                                           type='many2one',
                                           relation='training.subscription',
                                           string='Subscription', readonly=True),
        'job_id' : fields.related('subscription_line_id', 'job_id',
                                  type='many2one', relation='res.partner.job',
                                  string='Participant', select=1, readonly=True,
                                  store={
                                      'training.subscription.line' : (_store_get_sublines, None, 9),
                                  }
                                 ),
        'contact_id' : fields.related('subscription_line_id', 'job_id', 'contact_id',
                                      type='many2one', relation='res.partner.contact',
                                      string='Contact', select=1, readonly=True,
                                      store={
                                          'training.subscription.line': (_store_get_sublines, None, 10),
                                      }
                                      ),
        'contact_lastname': fields.related('contact_id', 'name', readonly=True, type='char', size=64, string='Contact Last Name',
                                            store={
                                                'training.subscription.line': (_store_get_sublines, None, 11),
                                            }
                                            ),

        'contact_firstname': fields.related('contact_id', 'first_name', readonly=True, type='char', size=64, string='Contact First Name',
                                            store={
                                                'training.subscription.line': (_store_get_sublines, None, 11),
                                            }
                                            ),

        'partner_id' : fields.related('subscription_line_id', 'partner_id',
                                      type='many2one', relation='res.partner',
                                      string='Partner', select=2, readonly=True),
        'date' : fields.related('seance_id', 'date', type='datetime', string='Date', select=1,
                                readonly=True, store=True),
        'purchase_ids': fields.many2many('purchase.order.line',
                                         'training_participation_purchase_rel',
                                         'participation_id',
                                         'purchase_id',
                                         'Purchases'),
        'purchase_state': fields.selection([('draft','To Do'),
                                            ('done', 'Done'),
                                            ('cancelled', 'Cancelled')
                                           ], 'Purchase State', required=True, readonly=True),

        'summary': fields.text('Summary'),
    }

    _defaults = {
        'present' : lambda *a: 0,
        'purchase_state' : lambda *a: 'draft',
    }

    _sql_constraints = [
        ('uniq_seance_sl', 'unique(seance_id, subscription_line_id)', "The subscription and the seance must be unique !"),
    ]

    def on_change_seance(self, cr, uid, ids, seance_id, context=None):
        if not seance_id:
            return {'value' : {'group_id' : 0}}

        seance = self.pool.get('training.seance').browse(cr, uid, seance_id, context=context)

        return {
            'value' : {
                'group_id' : seance.group_id and seance.group_id.id,
                'date' : seance.date,
            }
        }


    def name_get(self, cr, uid, ids, context=None):
        res = []
        for obj in self.browse(cr, uid, list(set(ids)), context=context):
            sl = obj.subscription_line_id
            oid = obj.id
            if sl.contact_id:
                name = "%s %s (%s)" % (sl.job_id.contact_id.first_name, sl.job_id.contact_id.name, sl.partner_id.name,)
            else:
                name = super(training_participation, self).name_get(cr, uid, [oid], context=context)[0][1]
            res.append((oid, name,))
        return res

    # training.participation
    def create_procurements(self, cr, uid, participation_ids, delayed=False, context=None):
        purchase_order_pool = self.pool.get('purchase.order')
        products = {}
        for participation in self.browse(cr, uid, participation_ids, context=context):
            if participation.seance_id and participation.seance_id.purchase_line_ids:
                for purchase_line in participation.seance_id.purchase_line_ids:
                    products.setdefault(purchase_line, [0.0, []])
                    products[purchase_line][0] = purchase_line.product_qty

                    if purchase_line.fix == 'by_subscription':
                        products[purchase_line][0] = purchase_line.product_qty * len(participation_ids)

                    products[purchase_line][1].append(participation)

        location_id = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')], context=context)[0]

        participations = {}
        for po_line, (quantity, parts) in products.items():
            # Create purchase order from this po_line ('seance.purchase.line')
            purchase_id = purchase_order_pool.create_from_procurement_line(cr, uid, po_line, quantity, location_id, context=context)
            purchase = self.pool.get('purchase.order').browse(cr, uid, purchase_id, context=context)
            # Then get ids of all create purchase.order.line
            purchase_order_line_ids = [ pol.id for pol in purchase.order_line ]

            for part in parts:
                participations.setdefault(part, []).extend(purchase_order_line_ids)

        # write relate purchase.order.line on each participations
        for participation, purchase_ids in participations.items():
            participation.write({'purchase_ids' : [(6, 0, purchase_ids)]}, context=context)

        # mark the purchase as done for this participations
        return self.write(cr, uid, participation_ids, {'purchase_state' : 'done'}, context=context)

    def unlink(self, cr, uid, ids, context=None):
        # TODO cancel the procurements ??
        return super(training_participation, self).unlink(cr, uid, ids, context=context)

training_participation()

class training_seance(osv.osv):
    _name = 'training.seance'
    _description = 'Seance'

    def _shared_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)
        for seance in self.browse(cr, uid, ids, context=context):
            res[seance.id] = len(seance.session_ids) > 1
        return res

    # training.seance
    def _available_seats_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)

        for seance in self.browse(cr, uid, ids, context=context):
            count = ['participant_count', 'participant_count_manual'][seance.manual]
            res[seance.id] = seance.max_limit - int(seance[count])

        return res

    # training.seance
    def _draft_seats_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)

        cr.execute("SELECT rel.seance_id, count(1) "
                   "FROM training_subscription_line sl, training_session_seance_rel rel "
                   "WHERE sl.state = 'draft' "
                   "AND sl.session_id = rel.session_id "
                   "AND rel.seance_id IN (" + ",".join(['%s'] * len(ids)) + ") "
                   "GROUP BY rel.seance_id ", ids)

        for seance_id, count in cr.fetchall():
            res[seance_id] = int(count)

        return res

    # training.seance
    def _participant_count(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, 0)

        cr.execute('SELECT tp.seance_id, COUNT(DISTINCT(tsl.contact_id)) '
                   'FROM training_participation tp, training_subscription_line tsl '
                   'WHERE tp.subscription_line_id = tsl.id '
                   'AND tp.seance_id in (' + ",".join(['%s'] * len(ids)) + ") "
                   "AND tsl.state in ('confirmed', 'done') "
                   'GROUP BY tp.seance_id',
                   ids
                  )
        for seance_id, count in cr.fetchall():
            res[seance_id] = int(count)

        return res

    _order = "date asc"

    def _confirmed_lecturer_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 'no')
        proxy = self.pool.get('training.participation.stakeholder')
        for seance in self.browse(cr, uid, ids, context=context):
            #if seance.kind == 'standard':
                has = len(seance.contact_ids) > 0 and any(c.state in ['accepted', 'done'] for c in seance.contact_ids)
                res[seance.id] = ['no', 'yes'][has]

        return res

    def _get_stakeholders(self, cr, uid, ids, context=None):
        values = set()
        for part in self.pool.get('training.participation.stakeholder').browse(cr, uid, ids, context=context):
            values.add(part.seance_id.id)

        return list(values)

    def _get_sessions_type(self, cr, uid, ids, fieldnames, args, context=None):
        res = []
        for seance in self.browse(cr, uid, ids, context=context):
            types = set()
            for session in seance.session_ids:
                if session.offer_id:
                    types.add(session.offer_id.kind.capitalize())
            res.append((seance.id, types))
        res = dict((x[0], ' / '.join(map(_, x[1]))) for x in res)
        return res

    def _contact_names_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 'None')
        for seance in self.browse(cr, uid, ids, context=context):
            name = []
            for contact in seance.contact_ids:
                # skip lecturer request which has been cancelled
                if contact.state in ['cancelled','refused']:
                    continue
                if contact.job_id:
                    lecturer_name = "%s %s" % (contact.job_id.contact_id.name, contact.job_id.contact_id.first_name,)
                    if contact.state == 'draft':
                        name.append("[%s]" % (lecturer_name))
                    else:
                        name.append(lecturer_name)

                else:
                    tools.debug("Check this job: %r" % (contact.job_id))
            res[seance.id] = ", ".join(name)
        return res

    # training.seance
    def name_get(self, cr, uid, ids, context=None):
        return [(obj.id, "%s (%s)" % (obj.name, obj.group_id.name or _('Class %d') % (1,))) for obj in self.browse(cr, uid, list(set(ids)), context=context)]

    def on_change_course(self, cr, uid, ids, course_id, kind, context=None):
        if not course_id:
            return {
                'value' : {
                    'min_limit' : 0,
                    'max_limit' : 0,
                    'duration' : 0.0,
                }
            }

        course = self.pool.get('training.course').browse(cr, uid, course_id, context=context)

        return {
            'value':{
                'name' : course.name,
                'min_limit' : course.course_type_id.min_limit,
                'max_limit' : course.course_type_id.max_limit,
                'duration' : course.duration,
            }
        }


    _columns = {
        'id' : fields.integer('Database ID', readonly=True),
        'is_first_seance' : fields.boolean('First Seance', select=1),
        'name' : fields.char('Name', size=64, required=True, select=1),
        'session_ids' : fields.many2many('training.session',
                                         'training_session_seance_rel',
                                         'seance_id',
                                         'session_id',
                                         'Sessions',
                                         select=1,
                                         ondelete='cascade'),
        'sessions_type': fields.function(_get_sessions_type,
                                         method=True,
                                         string='Session(s) Type',
                                         type='char',
                                         size=32,
                                         ),
        'forced_lecturer' : fields.boolean('Forced Lecturer(s)'),
        'confirmed_lecturer' : fields.function(_confirmed_lecturer_compute,
                                               method=True,
                                               select=1,
                                               store={
                                                   'training.participation.stakeholder' : (_get_stakeholders, None, 10),
                                               },
                                               string="Confirmed Lecturer",
                                               type='selection',
                                               selection=[('no', 'No'),('yes','Yes')],
                                              ),
        'original_session_id' : fields.many2one('training.session', 'Original Session', ondelete='cascade'),
        'original_offer_id': fields.related('original_session_id', 'offer_id', string="Original Offer", type='many2one', relation='training.offer', select=1),
        'original_offer_kind': fields.related('original_offer_id', 'kind', type='selection', selection=training_offer_kind_compute, string='Original Offer Kind', readonly=True),
        'duplicata' : fields.boolean('Duplicata', required=True),
        'duplicated' : fields.boolean('Duplicated', required=True),
        'date' : fields.datetime('Date', required=True, select=1, help="The create date of seance"),
        'duration' : fields.float('Duration', select=1, help="The duration of the seance"),
        'participant_ids' : fields.one2many('training.participation',
                                            'seance_id',
                                            'Participants',
#                                            domain="[('group_id', '=', group_id)]" #error in v6.0 RC1
                                            ),
        'group_id' : fields.many2one('training.group', 'Group',
                                     #required=True,
                                     help='The group of participants',
                                    ),
        'state' : fields.selection([('opened', 'Opened'),
                                    ('confirmed', 'Confirmed'),
                                    ('inprogress', 'In Progress'),
                                    ('closed', 'Closed'),
                                    ('cancelled', 'Cancelled'),
                                    ('done', 'Done')],
                                   'State',
                                   required=True,
                                   readonly=True,
                                   select=1,
                                   help="The status of the Seance",
                                  ),
        'contact_ids' : fields.one2many('training.participation.stakeholder', 'seance_id', 'Lecturers', readonly=True),
        'contact_names' : fields.function(_contact_names_compute, method=True,
                                          type='char', size=256,
                                          string='Lecturers'),
        'course_id' : fields.many2one('training.course',
                                      'Course',
                                      select=1,
                                      domain="[('state_course', '=', 'validated')]"),
        'state_course' : fields.related('course_id', 'state_course',
                                        string="Course's State",
                                        type='selection',
                                        selection=[('draft', 'Draft'),
                                                   ('pending', 'Pending'),
                                                   ('deprecated', 'Deprecated'),
                                                   ('validated', 'Validated')],
                                        readonly=True),
        'purchase_line_ids' : fields.one2many('training.seance.purchase_line', 'seance_id', 'Supplier Commands'),
        'min_limit' : fields.integer("Minimum Threshold", help='The Minimum of Participants in Seance'),
        'max_limit' : fields.integer("Maximum Threshold", help='The Maximum of Participants in Seance'),
        'user_id' : fields.many2one('res.users', 'Responsible', required=True, select=1),

        'available_seats' : fields.function(_available_seats_compute,
                                            method=True,
                                            string='Available Seats',
                                            type='integer',
                                            help='Available seats in Seance'
                                           ),
        'draft_seats' : fields.function(_draft_seats_compute,
                                        method=True,
                                        string='Draft Subscriptions',
                                        type='integer',
                                        help='Draft Subscriptions',
                                       ),

        'presence_form' : fields.selection([('yes', 'Yes'),
                                            ('no', 'No')],
                                           'Presence Form Received',
                                           help='The training center has received the presence list from the lecturer'),
        'shared' : fields.function(_shared_compute,
                                   method=True,
                                   string='Shared',
                                   type='boolean',
                                   help="Allows to know if the seance is linked with a lot of sessions"),

        'kind': fields.selection(training_course_kind_compute, 'Kind', required=True, select=1),
        'master_id' : fields.many2one('training.seance', 'Master Seance'),

        'participant_count' : fields.function(_participant_count,
                                              method=True,
                                              type="integer",
                                              string="Confirmed Seats",
                                              help="Confirmed Subscriptions for this seance",
                                             ),
        'participant_count_manual' : fields.integer('Manual Confirmed Seats',
                                                    help="The quantity of supports, catering, ... relative to the number of participants coming from the confirmed seats"),
        'manual' : fields.boolean('Manual', help="Allows to the user to specify the number of participants"),
    }

    def _check_limits(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids)[0]
        return obj.min_limit <= obj.max_limit

    def _check_date_before_now(self,cr,uid,ids,context=None):
        obj = self.browse(cr, uid, ids[0])
        res = obj.date > time.strftime('%Y-%m-%d %H:%M:%S')
        return res

    def _check_date_holiday(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        date = time.strftime('%Y-%m-%d', time.strptime(obj.date, '%Y-%m-%d %H:%M:%S'))
        return not self.pool.get('training.holiday.period').is_in_period(cr, date)

    def _check_date_of_sessions(self, cr, uid, ids, context=None):
        for seance in self.browse(cr, uid, ids, context=context):
            for session in seance.session_ids:
                if seance.date < session.date:
                    return False

        return True

    _constraints = [
        #(_check_date_before_now, "You cannot create a date before now", ['date']),
        #(_check_date_holiday, "You cannot assign a date in a public holiday", ['date']),
        (_check_limits, 'The minimum limit is greater than the maximum limit', ['min_limit', 'max_limit']),
        (_check_date_of_sessions, "You have a session with a date inferior to the seance's date", ['date']),
    ]

    _defaults = {
        'min_limit' : lambda *a: 0,
        'max_limit' : lambda *a: 0,
        'user_id' : lambda obj,cr,uid,context: uid,
        'presence_form' : lambda *a: 'no',
        'confirmed_lecturer' : lambda *a: 'no',
        'state' : lambda *a: 'opened',
        'date' : lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'kind' : lambda *a: 'standard',
        'duplicata' : lambda *a: 0,
        'duplicated' : lambda *a: 0,
        'is_first_seance' : lambda *a: 0,
        'duration' : lambda *a: 2.0,
        'forced_lecturer' : lambda *a: 0,
    }

    # training.seance
    def action_workflow_open(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'opened'}, context=context)

    # training.seance
    def test_workflow_confirm(self, cr, uid, ids, context=None):
        for seance in self.browse(cr, uid, ids, context=context):
            if any(session.state in ('draft', 'opened') for session in seance.session_ids):
                raise osv.except_osv(_('Warning'),
                                     _('There is at least a session in the "Draft" or "Confirmed" state'))

        return True

    # training.seance
    def action_workflow_confirm(self, cr, uid, ids, context=None):
        proxy = self.pool.get('training.participation')
        emails = self.pool.get('training.email')
        report = netsvc.LocalService('report.training.seance.support.delivery.report')

        if not context:
            context = {}
        report_ctx = context.copy()

        for seance in self.browse(cr, uid, ids, context=context):
            if not seance.manual:
                proxy.create_procurements(cr, uid, [x.id for x in seance.participant_ids], context=context)
            else:
                self.create_procurements(cr, uid, [seance.id], context=context)

            # send email to suppliers
            partners = set()
            for po_line in seance.purchase_line_ids:
                for seller in po_line.product_id.seller_ids:
                    partners.add(seller.name)


            for partner in partners:
                to = None
                for address in partner.address:
                    if not address.email:
                        continue
                    if address.type == 'delivery':
                        to = address.email
                        break
                    elif address.type == 'default':
                        to = address.email

                if to is None:
                    continue

                report_ctx['partner'] = partner
                pdf, _ = report.create(cr, uid, [seance.id], {}, context=report_ctx)
                filename = seance.name.replace('/', ' ') + '.pdf'
                emails.send_email(cr, uid, 'procurements', 's', to=to, attachments=[(filename, pdf),], context=context, seance=seance, partner=partner)

        return self.write(cr, uid, ids, {'state' : 'confirmed'}, context=context)

    # training.seance
    def action_workflow_inprogress(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')

        for seance in self.browse(cr, uid, ids, context=context):
            for session in seance.session_ids:
                workflow.trg_validate(uid, 'training.session', session.id, 'signal_inprogress', cr)

        return self.write(cr, uid, ids, {'state' : 'inprogress'}, context=context)

    # training.seance
    def action_workflow_close(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'closed'}, context=context)

    # training.seance
    def test_workflow_done(self, cr, uid, ids, context=None):
        return True

    # training.seance
    def action_workflow_done(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')
        self.write(cr, uid, ids, {'state' : 'done'}, context=context)

        for seance in self.browse(cr, uid, ids, context=context):
            for participation in seance.contact_ids:
                workflow.trg_validate(uid, 'training.participation.stakeholder', participation.id, 'signal_done', cr)
            for session in seance.session_ids:
                workflow.trg_validate(uid, 'training.session', session.id, 'signal_close', cr)

        return True

    # training.seance
    def test_workflow_cancel(self, cr, uid, ids, context=None):
        can_be_cancelled = any(session.state in ('cancelled', 'inprogress') for seance in self.browse(cr, uid, ids, context)
                               for session in seance.session_ids)
        return can_be_cancelled

    # training.seance
    def action_workflow_cancel(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')

        # Annulation des commandes, des formateurs et des procurements
        mrp_products = {}
        part_ids = []
        for seance in self.browse(cr, uid, ids, context=context):

            for line in seance.purchase_line_ids:
                mrp_products[(seance.id, line.product_id.id,)] = line.fix

            for participation in seance.participant_ids:
                part_ids.append(participation.id)
                for purchase in participation.purchase_ids:
                    key = (seance.id, purchase.product_id.id,)
                    if purchase.state == 'confirmed' and key in mrp_products:
                        workflow.trg_validate(uid, 'purchase.order', purchase.order_id.id, 'purchase_cancel', cr)

            for participation in seance.contact_ids:
                ### if not participation.participation_sh_session_id:
                ###    # participation on this seance only...
                workflow.trg_validate(uid, 'training.participation.stakeholder', participation.id, 'signal_cancel', cr)

            for session in seance.session_ids:
                workflow.trg_validate(uid, 'training.session', session.id, 'signal_close', cr)

        self.pool.get('training.participation').unlink(cr, uid, part_ids, context=context)

        return self.write(cr, uid, ids, {'state' : 'cancelled'}, context=context)

    # training.seance
    def _create_participation(self, cr, uid, seance, subscription_line, context=None):
        proxy = self.pool.get('training.participation')
        values = {
            'seance_id' : seance.id,
            'subscription_line_id' : subscription_line.id,
        }
        return proxy.create(cr, uid, values, context=context)

    def on_change_date(self, cr, uid, ids, date, context=None):
        old_date = ids and self.browse(cr, uid, ids[0], context=context).date or 0

        if self.pool.get('training.holiday.period').is_in_period(cr, date):
            return {
                'value' : {
                    'date' : old_date,
                },
                'warning' : {
                    'title' : _("Selection Date"),
                    'message' : _("You can not select this date because it is a public holiday"),
                },
            }
        return {}

    # training.seance
    def create_procurements(self, cr, uid, ids, context=None):
        purchase_order_pool = self.pool.get('purchase.order')
        location_id = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')], context=context)[0]

        for seance in self.browse(cr, uid, ids, context=context):
            if seance.manual:
                for po_line in seance.purchase_line_ids:
                    quantity = po_line.product_qty
                    if po_line.fix == 'by_subscription':
                        quantity = quantity * seance.participant_count_manual

                    procurement_id = purchase_order_pool.create_from_procurement_line(cr, uid, po_line, quantity, location_id, context=context)

        return True

    def unlink(self, cr, uid, ids, context=None):
        for seance in self.browse(cr, uid, ids, context=context):
            if seance.state == 'confirmed':
                for pl in seance.purchase_line_ids:
                    if pl.procurement_id:
                        raise osv.except_osv(_("Warning"),
                                             _("You can not suppress a seance with a confirmed procurement"))
            else:
                for participant in seance.participant_ids:
                    if participant.subscription_line_id.invoice_line_id:
                        raise osv.except_osv(_('Warning'),
                                             _("You can not suppress a seance with a invoiced subscription"))

        return super(training_seance, self).unlink(cr, uid, ids, context=context)

    def copy(self, cr, uid, object_id, values, context=None):
        if not 'is_first_seance' in values:
            values['is_first_seance'] = 0

        return super(training_seance, self).copy(cr, uid, object_id, values, context=context)

    def search(self, cr, uid, domain, offset=0, limit=None, order=None, context=None, count=False):
        offer_id = context and context.get('offer_id', False) or False

        if offer_id:
            date = context and context.get('date', False) or False
            if not date:
                date = time.strftime('%Y-%m-%d')
            cr.execute("SELECT seance.id AS seance_id, rel.offer_id, seance.course_id, seance.name, seance.state, seance.date "
                       "FROM training_seance seance, training_course_offer_rel rel "
                       "WHERE seance.course_id = rel.course_id "
                       "AND rel.offer_id = %s "
                       "AND seance.state = %s "
                       "AND seance.date >= %s "
                       "AND seance.duplicated = %s ",
                       (offer_id, 'opened', date, False,))

            return [x[0] for x in cr.fetchall()]

        job_id = context and context.get('job_id', False) or False
        request_session_id = context and context.get('request_session_id', False) or False

        if job_id and request_session_id:
            session = self.pool.get('training.session').browse(cr, uid, request_session_id, context=context)
            course_proxy = self.pool.get('training.course')
            seance_ids = []
            for seance in session.seance_ids:
                if seance.course_id and job_id:
                    cr.execute('select course_id from training_course_job_rel where course_id = %s and job_id = %s',
                               (seance.course_id.id, job_id,)
                              )

                    res = [x[0] for x in cr.fetchall()]
                    if res:
                        seance_ids.append(seance.id)

            return seance_ids


        return super(training_seance, self).search(cr, uid, domain, offset=offset,
                                                   limit=limit, order=order, context=context, count=count)

    def _get_product(self, cr, uid, ids, context=None):
        assert len(ids) == 1
        seance = self.browse(cr, uid, ids[0], context)
        return seance.course_id.course_type_id.product_id

training_seance()

class training_seance_purchase_line(osv.osv):
    _name = 'training.seance.purchase_line'
    _rec_name = 'product_id'

    def _proc_qty_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)
        for pl in self.browse(cr, uid, ids, context=context):
            if pl.fix == 'fix':
                multi = 1
            else:
                if pl.seance_id.manual:
                    multi = pl.seance_id.participant_count_manual
                else:
                    multi = pl.seance_id.participant_count


            res[pl.id] = pl.product_qty * multi

        return res

    _columns = {
        'seance_id' : fields.many2one('training.seance', 'Seance', required=True, ondelete="cascade"),
        'seance_date': fields.related('seance_id', 'date', string="Sceance Date", type="datetime"),
        'course_id': fields.many2one('training.course', 'For Course'),
        'product_id' : fields.many2one('product.product', 'Product', required=True),
        'product_qty' : fields.integer('Quantity', required=True),
        'product_uom' : fields.many2one('product.uom', 'Product UoM', required=True),
        'product_price' : fields.float('Unit Price', digits_compute=dp.get_precision('Account')),
        'fix' : fields.selection([('fix', 'Fix'),('by_subscription', 'By Subscription')], 'Invoiced Quantity', required=True),
        'description' : fields.char('Description', size=128, required=True),
        'attachment_id' : fields.many2one('ir.attachment', 'Attachment'),
#        'procurement_id' : fields.many2one('mrp.procurement', 'Procurement'),
        'procurement_id' : fields.many2one('procurement.order', 'Procurement'),
        'proc_qty' : fields.function(_proc_qty_compute,
                                     method=True,
                                     string='Ordered Quantity',
                                     type='integer',
                                    ),
        'auto_update': fields.boolean('Auto. Update'),
    }

    _defaults = {
        'product_qty' : lambda *a: 1,
        'fix' : lambda *a: 'fix',
        'auto_update': lambda *a: True,
    }

    def on_change_product(self, cr, uid, ids, product_id, context=None):
        if not product_id:
            return {'value' : {'product_uom' : 0,
                               'description' : '',
                               'product_price' : 0}}

        product = self.pool.get('product.product').browse(cr, uid, product_id)

        proxy = self.pool.get('training.config.product')
        ids = proxy.search(cr, uid,
                           [('type', 'in', ('support_of_course','voucher')),
                            ('product_id', '=', product.id)
                           ],
                           context=context)
        fix = ids and 'by_subscription' or 'fix'

        return {
            'value' : {
                'product_uom' : product.uom_id.id,
                'product_price' : product.standard_price,
                'description' : product.name,
                'fix' : fix,
            }
        }

    def on_change_product_qty(self, cr, uid, ids, product_qty, fix, manual, participant_manual, participant):
        if product_qty and fix:
            if fix == 'fix':
                multi = 1
            else:
                if manual:
                    multi = participant_manual
                else:
                    multi = participant

            return {'value' : {'proc_qty': product_qty * multi}}
        else:
            return {}


training_seance_purchase_line()


class training_subscription(osv.osv):
    _name = 'training.subscription'
    _description = 'Subscription'

    def check_notification_mode(self, cr, uid, ids, context=None):
        for subr in self.browse(cr, uid, ids, context=context):
            if not subr.partner_id.notif_contact_id \
                and not subr.partner_id.notif_participant:
                raise osv.except_osv(_('Error'),
                        _('No notification mode (HR and/or Participant) for this partner "%s", please choose at least one') % (subr.partner_id.name))

    def _notification_text_compute(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, '')

        for obj in self.browse(cr, uid, ids):
            notifications = []
            if obj.partner_id.notif_contact_id:
                notifications.append(_('Partner'))
            if obj.partner_id.notif_participant:
                notifications.append(_('Participant'))
            res[obj.id] = _(" and ").join(notifications)

        return res

    def _get_partner(self, cr, uid, ids, context=None):
        return self.pool.get('training.subscription').search(cr, uid, [('partner_id', 'in', ids),('state', '=', 'draft')], context=context)

    _columns = {
        'name' : fields.char('Reference', size=32, required=True, select=1, readonly=True, help='The unique identifier is generated by the system (customizable)'),
        'create_date' : fields.datetime('Creation Date', select=True, readonly=True),
        'state' : fields.selection([('draft', 'Draft'), ('confirmed','Request Sent'), ('cancelled','Cancelled'), ('done', 'Done') ], 'State', readonly=True, required=True, select=1, help='The state of the Subscription'),

        'partner_id' : fields.many2one('res.partner', 'Partner', select=1, required=True, help='The Subscription name', **WRITABLE_ONLY_IN_DRAFT),
        'partner_rh_email' : fields.char('Subscription Contact', size=64),
        'address_id' : fields.many2one('res.partner.address', 'Invoice Address', select=1, required=True, help='The Subscription invoice address', **WRITABLE_ONLY_IN_DRAFT),
        'subscription_line_ids' : fields.one2many('training.subscription.line', 'subscription_id',
                                                  'Subscription Lines', select=1, **WRITABLE_ONLY_IN_DRAFT),

        'pricelist_id' : fields.related('partner_id', 'property_product_pricelist', string='Pricelist', type='many2one', relation='product.pricelist', readonly=True),
        'payment_term_id' : fields.many2one('account.payment.term', 'Payment Term', **WRITABLE_ONLY_IN_DRAFT),

        'responsible_id' : fields.many2one('res.users', 'Creator', required=True, readonly=True, select=1),

        'origin' : fields.char('Origin', size=64, **WRITABLE_ONLY_IN_DRAFT),

        'notification_active' : fields.boolean('Notification Active', **WRITABLE_ONLY_IN_DRAFT),
        'notification_text' : fields.function(_notification_text_compute, method=True,
                                              string='Kind', type='char',
                                              store={
                                                  'res.partner' : (_get_partner, None, 10),
                                                  'training.subscription' : (lambda self, cr, uid, ids, context=None: ids, None, 10),
                                              },
                                              size=64),
        'is_from_web': fields.boolean('Is from Web?', help='Is this subscription come from an online order', readonly=True),
    }

    def create(self, cr, uid, vals, context):
        if vals.get('name', '/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'training.subscription')
        return super(training_subscription, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, vals, context):
        subscriptions = self.read(cr, uid, vals, ['state'])
        unlink_ids = []
        for s in subscriptions:
            if s['state'] in ['draft']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid action !'), _('Only draft subscriptions could be deleted !'))
        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)

    _defaults = {
        'state' : lambda *a: 'draft',
        'name' : lambda *args: '/',
        'responsible_id' : lambda obj, cr, uid, context: uid,
        'notification_active' : lambda *a: 1,
    }

    def copy(self, cr, uid, subscription_id, default_values, context=None):
        default_values.update({
            'name' : '/',
            'subscription_line_ids' : [],
        })

        return super(training_subscription, self).copy(cr, uid, subscription_id, default_values, context=context)

    def on_change_partner(self, cr, uid, ids, partner_id):
        """
        This function returns the invoice address for a specific partner, but if it didn't find an
        address, it takes the first address from the system
        """
        if not partner_id:
            return {'value' :
                    {'address_id' : 0,
                     'partner_rh_email' : '',
                     'pricelist_id' : 0,
                     'payment_term_id' : 0,
                    }
                   }

        values = {}

        proxy = self.pool.get('res.partner')
        partner = proxy.browse(cr, uid, partner_id)

        partner_rh = partner.notif_contact_id
        if partner_rh and partner_rh.email:
            partner_rh_email = partner_rh.email
            values['partner_rh_email'] = partner_rh.email

        price_list_id = partner.property_product_pricelist
        if price_list_id:
            values['pricelist_id'] = price_list_id.id

        payment_term_id = partner.property_payment_term
        if payment_term_id:
            values['payment_term_id'] = payment_term_id.id

        proxy = self.pool.get('res.partner.address')
        ids = proxy.search(cr, uid, [('partner_id', '=', partner_id),('type', '=', 'invoice')])

        if not ids:
            ids = proxy.search(cr, uid, [('partner_id', '=', partner_id)])

        if ids:
            values['address_id'] = ids[0]

        return {'value' : values}

    # training.subscription
    def action_workflow_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'draft'}, context=context)

    def trg_validate_workflow(self, cr, uid, ids, signal, context=None):
        workflow = netsvc.LocalService("workflow")
        for subscription in self.browse(cr, uid, ids, context=context):
            for sl in subscription.subscription_line_ids:
                workflow.trg_validate(uid, 'training.subscription.line', sl.id, signal, cr)


    # training.subscription
    def action_workflow_cancel(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')
        sl_proxy = self.pool.get('training.subscription.line')
        sl_ids = []
        for subscription in self.browse(cr, uid, ids, context=context):
            if subscription.state == 'draft':
                for sl in subscription.subscription_line_ids:
                    workflow.trg_validate(uid, sl._name, sl.id, 'signal_cancel', cr)
            elif subscription.state == 'confirmed':
                sh = self.pool.get('training.participation.stakeholder')
                for sl in subscription.subscription_line_ids:
                    if sl.state == 'draft':
                        sl_ids.append(sl.id)
                    elif sl.state != 'confirmed':
                        continue
                    objs = {}
                    for seance in sl.session_id.seance_ids:
                        for contact in seance.contact_ids:
                            if contact.state == 'confirmed':
                                objs.setdefault(contact.id, {}).setdefault('seances', []).append(seance)

                    sh.send_email(cr, uid, objs.keys(), 'sub_cancelled', sl.session_id, context, objs)
                    sl_ids.append(sl.id)

        sl_proxy.action_workflow_invoice_and_send_emails(cr, uid, sl_ids, context)
        workflow = netsvc.LocalService('workflow')
        for oid in sl_ids:
            workflow.trg_validate(uid, 'training.subscription.line', oid, 'signal_cancel', cr)

        return self.write(cr, uid, ids, {'state' : 'cancelled'}, context=context)

    # training.subscription
    def action_workflow_confirm(self, cr, uid, ids, context=None):
        self.check_notification_mode(cr, uid, ids, context=context)
        return self.write(cr, uid, ids, {'state' : 'confirmed'}, context=context)

    # training.subscription
    def action_workflow_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'done'}, context=context)

    def test_wkf_done(self, cr, uid, ids, context=None):
        subs = self.browse(cr, uid, ids, context)
        lines = [line for sub in subs for line in sub.subscription_line_ids]
        return any(line.state != 'cancelled' for line in lines) and \
               all(line.state in ('cancelled', 'done') for line in lines)

    def test_wkf_cancel(self, cr, uid, ids, context=None):
        subs = self.browse(cr, uid, ids, context)
        lines = [line for sub in subs for line in sub.subscription_line_ids]
        return all(line.state == 'cancelled' for line in lines)

    _order = 'create_date desc'

    _sql_constraints=[
        ('uniq_name', 'unique(name)', 'The name of the subscription must be unique !'),
    ]

training_subscription()

class training_subscription_line(osv.osv):
    _name = 'training.subscription.line'
    _description = 'Subscription Line'

    def on_change_job(self, cr, uid, ids, job_id, context=None):
        if not job_id:
            return False

        return {'value' : {'job_email' : self.pool.get('res.partner.job').browse(cr, uid, job_id, context=context).email}}

    def on_change_subscription(self, cr, uid, ids, subscription_id, context=None):
        if not subscription_id:
            return False

        return {'value' : {'partner_id' : self.pool.get('training.subscription').browse(cr, uid, subscription_id, context=context).partner_id.id}}


    def _paid_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)

        for obj in self.browse(cr, uid, ids, context=context):
            if obj.invoice_line_id:
                res[obj.id] = obj.invoice_line_id.invoice_id.state == 'paid'

        return res

    def _theoritical_disponibility_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)

        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = int(obj.session_id.available_seats) - int(obj.session_id.draft_subscriptions)

        return res

    def _was_present_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, False)

        for sl in self.browse(cr, uid, ids, context=context):
            res[sl.id] = any(part.present for part in sl.participation_ids)

        return res

    _columns = {
        'name' : fields.char('Reference', size=64, required=True, readonly=True, select=1),

        'create_uid': fields.many2one('res.users', 'Created by', readonly=True, select=1),
        'create_date': fields.datetime('Created at', readonly=True),
        'validation_uid': fields.many2one('res.users', 'Validated by', readonly=True, select=2),
        'validation_date': fields.datetime('Validated at', readonly=True),
        'cancellation_uid': fields.many2one('res.users', 'Cancelled by', readonly=True, select=2),
        'cancellation_date': fields.datetime('Cancelled at', readonly=True),

        'subscription_id' : fields.many2one('training.subscription', 'Subscription',
                                            required=True,
                                            ondelete='cascade',
                                            select=1, help='Select the subscription', **WRITABLE_ONLY_IN_DRAFT),
        'subscription_state' : fields.related('subscription_id', 'state',
                                              type='selection',
                                              selection=[
                                                  ('draft', 'Draft'),
                                                  ('confirmed','Confirmed'),
                                                  ('cancelled','Cancelled'),
                                                  ('done', 'Done'),
                                              ],
                                              string='State',
                                              readonly=True,
                                              required=True,
                                              select=1,
                                              help='The state of the Subscription'),
        'price_list_id' : fields.many2one('product.pricelist', 'Pricelist', required=True, domain="[('type', '=', 'sale')]", **WRITABLE_ONLY_IN_DRAFT),
        'partner_hr_email' : fields.related('subscription_id', 'partner_rh_email', type='char', size=64, string='HR Email', readonly=True),
        'notification_text' : fields.related('subscription_id', 'notification_text', type='char', size=64, store=True, string='Notification (Kind)', readonly=True),
        'session_id' : fields.many2one('training.session', 'Session', select=1, required=True,
                                       domain="[('state', 'in', ('opened','opened_confirmed', 'closed_confirmed', 'inprogress'))]",
                                       help='Select the session', **WRITABLE_ONLY_IN_DRAFT),
        'session_state': fields.related('session_id', 'state', readonly=True,
                                        type='selection',
                                        selection= [
                                            ('draft', 'Draft'),
                                            ('opened', 'Opened'),
                                            ('opened_confirmed', 'Confirmed'),
                                            ('closed_confirmed', 'Closed Subscriptions'),
                                            ('inprogress', 'In Progress'),
                                            ('closed', 'Closed'),
                                            ('cancelled', 'Cancelled'),
                                        ],
                                        string='Session State', select=2),
        'session_date': fields.related('session_id', 'date', readonly=True, type="datetime", string="Session Date", select=2),
        'offer_id' : fields.related('session_id', 'offer_id', type='many2one', relation='training.offer', string='Offer', select=1, store=True, readonly=True),
        'offer_product_line_id' : fields.related('session_id', 'offer_id', 'product_line_id', type='many2one', relation='training.course_category', select=1, string='Product Line'),

        'price' : fields.float('Sales Price', digits_compute=dp.get_precision('Sale Price'), required=True, write=['base.group_user'], **WRITABLE_ONLY_IN_DRAFT),
        'partner_id' : fields.related('subscription_id', 'partner_id', type='many2one', store=True,
                                      relation='res.partner', string="Partner", select=1, readonly=True),
        'job_id' : fields.many2one('res.partner.job', 'Participant', select=1, required=True,
                                   domain="[('name', '=', parent.partner_id),('state', '=', 'current')]",
                                   help='Select the Participant', **WRITABLE_ONLY_IN_DRAFT),
        'job_email' : fields.char('Participant Email', size=64, help='Participant Email Address'), #**WRITABLE_ONLY_IN_DRAFT),
        'contact_id' : fields.related('job_id', 'contact_id', type='many2one', relation='res.partner.contact', string='Contact', select=1, readonly=True, store=True),
        'contact_firstname' : fields.related('contact_id', 'first_name', string='Contact Firstname',
                                             type='char', size=64, readonly=True),
        'contact_lastname' : fields.related('contact_id', 'name', string='Contact Lastname',
                                             type='char', size=64, readonly=True),

        'partner_rh' : fields.related('partner_id', 'notif_contact_id', type='many2one', relation='res.partner.job', readonly=True, string='Subscription Contact', store=True),

        'invoice_line_id' : fields.many2one('account.invoice.line', 'Invoice Line', readonly=True),
        'invoice_id' : fields.related('invoice_line_id', 'invoice_id', type='many2one', relation='account.invoice', string="Invoice", readonly=True, store=True),
        'paid' : fields.function(_paid_compute,
                                 method=True,
                                 string='Paid',
                                 type='boolean',
                                 readonly=True),
        'kind' : fields.related('session_id', 'kind',
                                string="Kind",
                                type="selection",
                                selection=training_offer_kind_compute,
                                select=1,
                                readonly=True),
        'state' : fields.selection([('draft', 'Draft'),
                                    ('confirmed','Confirmed'),
                                    ('cancelled','Cancelled'),
                                    ('done', 'Done') ],
                                   'State',
                                   required=True,
                                   readonly=True,
                                   select=1, help='The state of participant'),
        'date' : fields.related('session_id', 'date', type='datetime', string='Date',
                                readonly=True),
        'available_seats' : fields.related('session_id', 'available_seats',
                                           type='integer',
                                           readonly=True,
                                           string='Available Seats'),
        'draft_subscriptions' : fields.related('session_id', 'draft_subscriptions',
                                       type='integer',
                                       readonly=True,
                                       string='Draft Subscriptions'),
        'has_certificate' : fields.boolean('Has Certificate', readonly=True, select=2),
        'reason_cancellation' : fields.text('Reason of Cancellation', readonly=True),
        'theoritical_disponibility' : fields.function(_theoritical_disponibility_compute,
                                      method=True,
                                      string='Theoritical Disponibility',
                                      type='integer'),
        'max_limit' : fields.related('session_id', 'max_limit', string='Maximum Threshold', type='integer', store=True, readonly=True),
        'confirmed_subscriptions' : fields.related('session_id', 'confirmed_subscriptions',
                                                   string='Confirmed Subscriptions',
                                                   type='integer', readonly=True,
                                                  ),

        'participation_ids' : fields.one2many('training.participation', 'subscription_line_id', 'Participations', readonly=True),
        'internal_note' : fields.text("Internal Note"),
        'email_note': fields.text("Email Note"),

        'was_present' : fields.function(_was_present_compute, method=True,
                                        type='boolean',
                                        string='Was Present'),
    }

    def _default_name(self, cr, uid, context=None):
        return self.pool.get('ir.sequence').get(cr, uid, 'training.subscription.line')

    def unlink(self, cr, uid, vals, context):
        subscription_lines = self.read(cr, uid, vals, ['state'])
        unlink_ids = []
        for s in subscription_lines:
            if s['state'] in ['draft']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid action !'), _('Only draft subscription lines could be deleted !'))
        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)

    _defaults = {
        'state' : lambda *a: 'draft',
        'name' : _default_name,
        #lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'training.subscription.line'),
        'has_certificate' : lambda *a: 0,
    }

    _order = 'name desc'

    def copy(self, cr, uid, object_id, values, context=None):
        if 'name' not in values:
            values['name'] = self._default_name(cr, uid, context=context)

        if 'participation_ids' not in values:
            values['participation_ids'] = []

        if 'session_id' in values:
            session = self.pool.get('training.session').browse(cr, uid, values['session_id'], context=context)
            values['session_state'] = session.state
            values['session_date'] = session.date

        return super(training_subscription_line, self).copy(cr, uid, object_id, values, context=context)

    # training.subscription.line
    def _check_subscription(self, cr, uid, ids, context=None):
        for sl in self.browse(cr, 1, ids, context=context):
            session = sl.session_id
            contact = sl.job_id.contact_id
            name = "%s %s" % (contact.first_name, contact.name)

            same_contact_same_session = ['&', '&', '&', ('contact_id', '=', contact.id), ('session_id', '=', session.id), ('id', '!=', sl.id), ('state', '!=', 'cancelled')]

            sl_ids = self.search(cr, 1, same_contact_same_session, context=context)
            if sl_ids:
                raise osv.except_osv(_('Error'), _('%(participant)s is already following the session "%(session)s"') % {'participant': name, 'session': session.name})

        return True

    _constraints = [
        (lambda self, *args, **kwargs: self._check_subscription(*args, **kwargs), 'Invalid Subscription', ['session_id', 'contact_id', 'state']),
    ]

    def _get_price_list_from_product_line(self, session, partner_id, default_price_list):
        pl = default_price_list
        if session.offer_id.product_line_id and session.offer_id.product_line_id.price_list_id:
            if any(partner.id == partner_id for partner in session.offer_id.product_line_id.partner_ids):
                pl = session.offer_id.product_line_id.price_list_id.id

        if not pl:
            raise osv.except_osv(_('Warning'),
                                 _("Please, Can you check the price list of the partner ?"))
        return pl

    # training.subscription.line
    def on_change_session(self, cr, uid, ids, session_id, price_list_id, partner_id, context=None):
        if not session_id:
            return False

        session = self.pool.get('training.session').browse(cr, uid, session_id, context=context)
        if (not price_list_id) and partner_id:
            part = self.pool.get('res.partner').browse(cr, uid, partner_id)
            price_list_id = part.property_product_pricelist and part.property_product_pricelist.id or False

        if not session.offer_id.product_id:
            if session.kind == 'intra':
                return {
                    'value': {
                        'price': 0.0,
                        'kind': session.kind,
                        'price_list_id': price_list_id,
                        'session_date': session.date,
                    }
                }
            else:
                return False

        price_list = self._get_price_list_from_product_line(session, partner_id, price_list_id)

        price = self.pool.get('product.pricelist').price_get(cr, uid, [price_list], session.offer_id.product_id.id, 1.0)[price_list]

        values = {
            'value' : {
                'price' : price,
                'kind' : session.kind,
                'price_list_id' : price_list,
                'session_date' : session.date,
            }
        }

        return values

    def on_change_price_list(self, cr, uid, ids, session_id, price_list_id, context=None):
        if not price_list_id or not session_id:
            return False

        pricelist_proxy = self.pool.get('product.pricelist')
        session = self.pool.get('training.session').browse(cr, uid, session_id, context=context)

        if not session.offer_id.product_id:
            return False

        return {
            'value' : {
                'price' : pricelist_proxy.price_get(cr, uid, [price_list_id], session.offer_id.product_id.id, 1.0)[price_list_id]
            }
        }

    # training.subscription.line
    def _get_values_from_wizard(self, cr, uid, subscription_id, job, subscription_mass_line, context=None):
        # this method can easily surcharged by inherited modules
        subscription = self.pool.get('training.subscription').browse(cr, uid, subscription_id, context=context)
        session = subscription_mass_line.session_id

        def_pricelist_id = job.name.property_product_pricelist.id

        values = {
            'subscription_id' : subscription_id,
            'job_id' : job.id,
            'job_email': job.email,
            'session_id' : session.id,
            'kind': session.kind,
            'price_list_id': def_pricelist_id,
            'price': 0,
        }
        ocv = self.on_change_session(cr, uid, [], session.id, def_pricelist_id, job.name.id, context=context)
        if ocv and 'value' in ocv:
            values.update(ocv['value'])
        ocv = self.on_change_price_list(cr, uid, [], values['session_id'], values.get('price_list_id', False), context=context)
        if ocv and 'value' in ocv:
            values.update(ocv['value'])

        return values

    # training.subscription.line
    def _create_from_wizard(self, cr, uid, the_wizard, subscription_id, job, subscription_mass_line, context=None):
        values = self._get_values_from_wizard(cr, uid,
                                              subscription_id, job,
                                              subscription_mass_line,
                                              context=context)
        return self.create(cr, uid, values, context=context)

    # training.subscription.line
    def action_workflow_draft(self, cr, uid, ids, context=None):
        #if self.test_workflow_confirm(cr, uid, ids, context=context):
        #    raise osv.except_osv(_('Warning'), _('Please, Could you check the subscription of your contact(s)'))
        return self.write(cr, uid, ids, {'state' : 'draft'}, context=context)

    # training.subscription.line
    def test_workflow_confirm(self, cr, uid, ids, context=None):
        subs = set()
        for subl in self.read(cr, uid, ids, ['subscription_id'], context=context):
                if subl['subscription_id']:
                    subs.add(subl['subscription_id'][0])
        self.pool.get('training.subscription').check_notification_mode(cr, uid, list(subs), context=context)
        return True

    # training.subscription.line
    def action_create_participation(self, cr, uid, ids, context=None):
        for sl in self.browse(cr, uid, ids, context=context):
            sl.session_id._create_participation(sl, context=context)
            sl.write({'state' : sl.state})

        return True

    # training.subscription.line
    def action_workflow_send_confirm_emails(self, cr, uid, ids, context=None):
        # the confirm function will send an email to the participant and/or the HR Manager

        lines = {}

        for sl in self.browse(cr, uid, ids, context=context):
            sl.session_id._create_participation(sl, context=context)

            # opened -> opened; opened_confirmed and closed_confirmed -> confirmed
            state = sl.session_id.state.rsplit('_', 1)[-1]

            if state in ('opened', 'confirmed', 'inprogress'):
                lines.setdefault(state, []).append(sl.id)

        if 'opened' in lines:
            self.send_email(cr, uid, lines['opened'], 'sub_confirm_open', context)
        if 'confirmed' in lines:
            # TODO: change signal name (as closed confirmed sessions are also possible)
            self.send_email(cr, uid, lines['confirmed'], 'sub_confirm_openconf', context)
        if 'inprogress' in lines:
            self.send_email(cr, uid, lines['inprogress'], 'sub_confirm_openconf', context)

        return True

    # training.subscription.line
    def action_workflow_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed', 'validation_date': time.strftime('%Y-%m-%d %H:%M:%S'), 'validation_uid': uid}, context=context)
        return True

    def action_create_refund(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        invoice_proxy = self.pool.get('account.invoice')
        invoice_line_proxy = self.pool.get('account.invoice.line')
        seance_proxy = self.pool.get('training.seance')

        invoices = {}

        for sl in self.browse(cr, uid, ids, context=context):
            if sl.price >= -0.00001 and sl.price <= 0.00001:
                # sale price is ZERO, nothing to refund
                continue
            invoices.setdefault(sl.invoice_id, []).append( sl )

        for invoice, subscription_lines in invoices.iteritems():
            invoice_values = {
                'name' : "[REFUND] %s - %s" % (invoice.name, _('Cancellation')),
                'origin' : invoice.origin,
                'type' : 'out_refund',
                'reference' : "[INVOICE] %s" % (invoice.reference,),
                'partner_id' : invoice.partner_id.id,
                'address_contact_id' : invoice.address_contact_id and invoice.address_contact_id.id,
                'address_invoice_id' : invoice.address_invoice_id and invoice.address_invoice_id.id,
                # NOTE: Use the same journal as orignial invoice, otherwise
                #       we have to create a new analytic distribution for
                #       each lines
                'journal_id': invoice.journal_id.id,
                'account_id' : invoice.account_id.id,
                'fiscal_position' : invoice.fiscal_position.id,
                'date_invoice' : time.strftime('%Y-%m-%d'),
            }
            invoice_id = invoice_proxy.create(cr, uid, invoice_values, context=context)

            fpos_proxy = self.pool.get('account.fiscal.position')
            fpos = invoice_values['fiscal_position'] and fpos_proxy.browse(cr, uid, [invoice_values['fiscal_position']])[0] or False

            il_proxy = self.pool.get('account.invoice.line')

            for sl in subscription_lines:

                orig_invoice_line = sl.invoice_line_id
                if not orig_invoice_line:
                     raise osv.except_osv(_('Error'),
                                     _("Subscription line %s doesn't have any corresponding invoice line"))

                refund_line_obj = il_proxy.browse(cr, uid, [orig_invoice_line.id])
                if refund_line_obj:
                    refund_line_obj = refund_line_obj[0]

                refund_line = {
                        'invoice_id': invoice_id,
                        'product_id': refund_line_obj.product_id.id,
                        'quantity': refund_line_obj.quantity,
                        'name': refund_line_obj.name,
                        'origin': sl.name,
                        'account_id': refund_line_obj.account_id.id,
                        'discount': context.get('discount', 0.0),
                        'price_unit': refund_line_obj.price_unit,
                        'invoice_line_tax_id': [(6, 0, [ t.id for t in refund_line_obj.invoice_line_tax_id])],
                        # NOTE: reuse the same analytic distribution as orignal
                        #       invoice. ;-)
                        'analytics_id': refund_line_obj.analytics_id.id,
                    }
                refl = refund_line

                _to_pay = refl['price_unit'] * float(100.0 - (refl['discount'] or 0.0) / 100.0)
                # Creation ligne de facture uniquement si montant non-null
                if _to_pay < -0.0001 or _to_pay > 0.0001:
                    invoice_line_proxy.create(cr, uid, refund_line, context=context)
            invoice_proxy.button_compute(cr, uid, [invoice_id])

            _total_untaxed = invoice_proxy.browse(cr, uid, [invoice_id])[0].amount_untaxed
            if not _total_untaxed:
                invoice_proxy.unlink(cr, uid, [invoice_id])

        return True


    # training.subscription.line
    def action_workflow_invoice_and_send_emails(self, cr, uid, ids, context=None):
        self.action_create_invoice_and_refund(cr, uid, ids, context)
        self.send_email(cr, uid, ids, 'sub_cancelled', context)

    # training.subscription.line
    def _delete_participations(self, cr, uid, ids, context=None):
        proxy = self.pool.get('training.participation')
        part_ids = []
        mrp_products = {}

        for sl in self.browse(cr, uid, ids, context=context):
            for part in sl.participation_ids:
                part_ids.append(part.id)

                seance = part.seance_id
                for line in seance.purchase_line_ids:
                    mrp_products[(seance.id, line.product_id.id,)] = line.fix

                for purchase in part.purchase_ids:
                    key = (seance.id, purchase.product_id.id,)
                    # before deleting participations we need to check
                    # for relate purchases. If still not acceped or refused
                    # by supplier, we can still modify it
                    if purchase.state == 'confirmed' and key in mrp_products:
                        if mrp_products[key] != 'fix':
                            # we need to use 'read' to bypass 'browse' cache
                            prod_qty = purchase.read(['product_qty'])[0]['product_qty']
                            purchase.write({'product_qty': prod_qty - 1})

                        prod_qty = purchase.read(['product_qty'])[0]['product_qty']
                        # if final quantity is null, we can simply cancel the purchase
                        if prod_qty == 0:
                            workflow.trg_validate(uid, 'purchase.order', purchase.order_id.id, 'purchase_cancel', cr)
        proxy.unlink(cr, uid, part_ids, context=context)
        return True

    # training.subscription.line
    def action_create_invoice_and_refund(self, cr, uid, ids, context=None):

        def get_penality(trigger, default_value):
            proxy = self.pool.get('training.config.penality')
            ids = proxy.search(cr, uid, [('trigger', '=', trigger)], context=context)
            return ( ids and proxy.browse(cr, uid, ids[0], context=context).rate or default_value)

        DISCOUNT_DAYS = 7           # 7 calendar days   # TODO: read this value from config object. (by offer ?)
        #DISCOUNT_PERCENT = 80.0     # below x calendar days have a discount of y percent... # TODO: idem
        #DISCOUNT_REFUND_PERCENT = 20.0      # TODO: ibidem

        DISCOUNT_PERCENT = get_penality('discount_invoice', 80.0)
        DISCOUNT_REFUND_PERCENT = get_penality('discount_refund', 20.0)

        if not context:
            context = {}

        full_invoices = []
        discount_invoices = []
        full_refunds = []
        discount_refunds = []

        # Selection de toutes les lignes d'inscriptions
        for sl in self.browse(cr, uid, ids, context=context):
            today = mx.DateTime.today()
            session_date_minus_x = mx.DateTime.strptime(sl.session_id.date[:10], '%Y-%m-%d') - mx.DateTime.RelativeDateTime(days=DISCOUNT_DAYS)
            before_x_days = today < session_date_minus_x
            if sl.price >= -0.00001 and sl.price <= 0.00001:
                # Ignore subscription line with a sale price of ZERO
                continue
            if sl.invoice_line_id:
                if sl.partner_id.no_penalties:
                    # No pernalties, full refund
                    full_refunds.append(sl.id)
                elif before_x_days:
                    # Create a refund excepts for exams
                    if sl.kind != 'exam':
                        discount_refunds.append(sl.id)
                else:
                    # No refund at all
                    continue
            else:
                if not sl.partner_id.no_penalties:
                    if sl.kind == 'exam' or not before_x_days:
                        full_invoices.append(sl.id)
                    else:
                        discount_invoices.append(sl.id)

        ctx = context.copy()
        ctx['cancellation'] = True
        ctx['discount'] = 0.0

        if full_refunds:
            self.action_create_refund(cr, uid, full_refunds, context=ctx)

        if full_invoices:
            self.action_create_invoice(cr, uid, full_invoices, context=ctx)

        if discount_refunds:
            ctx['discount'] = DISCOUNT_REFUND_PERCENT
            self.action_create_refund(cr, uid, discount_refunds, context=ctx)

        if discount_invoices:
            ctx['discount'] = DISCOUNT_PERCENT
            self.action_create_invoice(cr, uid, discount_invoices, context=ctx)


    def _invoice_min_max(self, cr, uid, values, context=None):
        # NOTE: replace values in place
        if not context or not context.get('cancellation', False):
            return True

        def get_threshold_invoice(threshold, default_value):
            proxy = self.pool.get('training.config.invoice')
            ids = proxy.search(cr, uid, [('threshold', '=', threshold)], context=context)
            return ( ids and proxy.browse(cr, uid, ids[0], context=context).price or default_value)

        MIN_AMOUNT = get_threshold_invoice('minimum', 50.0)
        MAX_AMOUNT = get_threshold_invoice('maximum', 1200.0)

        price = values['price_unit']
        discount = values['discount'] or 0.0

        amount = price * (1.0 - discount / 100.0)
        if amount < MIN_AMOUNT:
            price = min(price, MIN_AMOUNT)
            discount = 0.0
        elif amount > MAX_AMOUNT:
            price = MAX_AMOUNT
            discount = 0.0

        values['price_unit'] = price
        values['discount'] = discount


    def _get_courses(self, cr, uid, ids, context=None):
        res = dict.fromkeys(ids, [])

        for sl in self.browse(cr, uid, ids, context=context):
            res[sl.id] = set(seance.course_id for seance in sl.session_id.seance_ids if seance.course_id)

        return res

    # training.subscription.line
    def _get_invoice_data(self, cr, uid, name, partner, session, sublines, context=None):
        return {}

    # training.subscription.line
    def _get_invoice_line_data(self, cr, uid, name, invoice_id, partner, session, subline, context=None):
        return {}

    # training.subscription.line
    def _get_invoice_line_taxes(self, cr, uid, subline, fiscal_position, partner, session, context=None):
        if session.offer_id.product_id:
            if session.offer_id.product_id.taxes_id:
                taxes = session.offer_id.product_id.taxes_id
                tax_id = self.pool.get('account.fiscal.position').map_tax(cr, uid, fiscal_position, taxes)
                return [(6, 0, [t for t in tax_id])]
        return []

    # training.subscription.line
    def action_create_invoice(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        # Creation des factures

        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        if user.company_id:
            company_id = user.company_id.id
            prop_obj = self.pool.get('ir.property')
            prop_ids = prop_obj.search(cr, uid, [('name','=','property_account_income_categ'),('company_id','=',company_id)])
            if not prop_ids:
                prop_ids = prop_obj.search(cr, uid, [('name','=','property_account_income'),('company_id','=',company_id)])
            if prop_ids:
                prop = prop_obj.browse(cr, uid, prop_ids[0], context=context)
                if prop.value_reference:
                    account_id = prop.value_reference.id

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

        partners = {}
        for sl in self.browse(cr, uid, ids, context=context):
            if sl.price >= -0.00001 and sl.price <= 0.00001:
                # Ignore subscription line with a sale price of ZERO
                continue
            if sl.invoice_line_id:
                continue
            key = (sl.subscription_id.partner_id, sl.session_id, sl.subscription_id.payment_term_id.id,)
            partners.setdefault(key, []).append(sl)

        if partners == {}:
            raise osv.except_osv(_('Error'), _("This Subscription line was invoiced or price is 0") )

        invoice_ids = []

        for (partner, session, payment_term), subscription_lines in partners.items():
            name = session.name
            if context.get('cancellation', False) is True:
                name += ' - ' + _('Cancellation')

            invoice_values = {
                'name' : name,
                'origin' : session.name,
                'type' : 'out_invoice',
                'reference' : "%s - %s" % (partner.name, session.name),
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
            fpos = invoice_values['fiscal_position'] and fpos_proxy.browse(cr, uid, invoice_values['fiscal_position']) or False

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

                if not journal_sales.analytic_journal_id.id:
                    raise osv.except_osv(_('Error'), _("Select Analytic Journal from Financial Journals Configuration") )

                # Create 'analytic distribution instance'
                adist_id = proxy_adist.create(cr, uid, {
                    'journal_id': journal_sales.analytic_journal_id.id,
                })

                for course in courses:
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

    # training.subscription.line
    def action_workflow_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state' : 'done'}, context=context)

        workflow = netsvc.LocalService('workflow')
        for line in self.browse(cr, uid, ids, context):
            workflow.trg_validate(uid, 'training.subscription', line.subscription_id.id, 'signal_done_cancel', cr)
        return True

    # training.subscription.line
    def action_workflow_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancelled', 'cancellation_date': time.strftime('%Y-%m-%d %H:%M:%S'), 'cancellation_uid': uid}, context=context)

        self._delete_participations(cr, uid, ids, context)

        workflow = netsvc.LocalService('workflow')
        for line in self.browse(cr, uid, ids, context):
            workflow.trg_validate(uid, 'training.subscription', line.subscription_id.id, 'signal_done_cancel', cr)
        return True


    def send_email(self, cr, uid, ids, trigger, context=None, **objects):
        """Send email to participant and to HR (grouped by session)"""
        email_proxy = self.pool.get('training.email')
        groups = {}
        email_to_subs = {}
        for sl in self.browse(cr, uid, ids, context=context):
            if sl.subscription_id.notification_active:
                partner = sl.job_id.name
                if partner.notif_participant:
                    email_proxy.send_email(cr, uid, trigger, 'p', sl.job_email, session=sl.session_id, stylegroup=sl.session_id.stylegroup_id, context=context, partner=partner, subline=sl, **objects)

                hremail = sl.partner_hr_email
                # do not group HR emails...
                email_proxy.send_email(cr, uid, trigger, 'hr', hremail, session=sl.session_id, stylegroup=sl.session_id.stylegroup_id, context=context, subline=sl, **objects)

#                key = hremail, sl.session_id
#                email_to_subs.setdefault(hremail, set()).add(sl.subscription_id)
#                groups.setdefault(key, []).append(sl)
#
#        for (hremail, session), sublines in groups.iteritems():
#            subs = list(email_to_subs[hremail])
#            email_proxy.send_email(cr, uid, trigger, 'hr', hremail, session=session, context=context, sublines=sublines, **objects)

training_subscription_line()

class training_participation_stakeholder(osv.osv):
    _name = 'training.participation.stakeholder'
training_participation_stakeholder()

class training_participation_stakeholder_request(osv.osv):
    _name = 'training.participation.stakeholder.request'
    _rec_name = 'reference'

    def _store_get_requests(self, cr, uid, ids, context=None):
        keys = set()
        for this in self.pool.get('training.participation.stakeholder').browse(cr, uid, ids, context=context):
            if this.request_id:
                keys.add(this.request_id.id)

        return list(keys)

    def _price_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0.0)
        for this in self.browse(cr, uid, ids, context=context):
            res[this.id] = sum(p.price for p in this.participation_ids)
        return res

    def _date_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, False)
        for this in self.browse(cr, uid, ids, context):
            if this.participation_ids:
                res[this.id] = min(p.seance_id.date for p in this.participation_ids)
        return res

    def _amount_to_pay(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, 'N/A')
        if not ids:
            return res

        invoice_pool = self.pool.get('account.invoice')
        request_invoices = {}

        for request in self.browse(cr, uid, ids, context=context):
            try:
                invoice_id = request.purchase_order_id.invoice_id.id
                if invoice_id:
                    request_invoices[invoice_id] = request.id
            except AttributeError:
                # catch: "bool object doesn't have 'x' attributte" errors
                pass
        invoice_residual_amounts = invoice_pool._amount_to_pay(cr, uid, request_invoices.keys(), None, None, context)
        for invoice_id, residual_amount in invoice_residual_amounts.items():
            res[request_invoices[invoice_id]] = unicode(residual_amount)
        return res

    _columns = {
        'reference': fields.char('Reference', size=16, readonly=True, required=True),
        'session_id': fields.many2one('training.session', 'Session', select=1, required=True, readonly=True),
        'date': fields.function(_date_compute, method=True,
                                string='First Seance Date',
                                type='datetime',
                                store={
                                    'training.participation.stakeholder': (_store_get_requests, None, 25),
                                },
                                select=1,
                                ),
        'kind' : fields.related('session_id', 'offer_id', 'kind', type='char', readonly=True, select=1, string="Offer's Kind"),
        'job_id': fields.many2one('res.partner.job', 'Contact', required=True, select=1, **WRITABLE_ONLY_IN_DRAFT),
        'email' : fields.char('Email', size=128, select=1, **WRITABLE_ONLY_IN_DRAFT),
        'payment_mode' : fields.selection([('contract', 'Contract'),
                                           ('invoice', 'Invoice')
                                          ],
                                          'Payment Mode',
                                          select=1),
        'participation_ids': fields.one2many('training.participation.stakeholder', 'request_id', 'Participations', **WRITABLE_ONLY_IN_DRAFT),
        'notes' : fields.text('Notes'),
        'state': fields.selection([('draft', 'Draft'),
                                   ('valid', 'Validated'),
                                   ('requested', 'Requested'),
                                   ('accepted', 'Accepted'),
                                   ('refused', 'Refused'),
                                   ('cancelled', 'Cancelled'),
                                   ('done', 'Done'),
                                  ],
                                  'State',
                                  readonly=True,
                                  required=True,
                                  select=1,
                                 ),
        'purchase_order_id': fields.many2one('purchase.order', 'Purchase Order', readonly=True),
        'amount_to_pay': fields.function(_amount_to_pay, string='Amount to pay', type='char', size='20', readonly=True, method=True),
        'price' : fields.function(_price_compute, method=True,
                                  string='Remuneration',
                                  type='float',
                                  digits_compute=dp.get_precision('Account'),
                                  store={
                                      'training.participation.stakeholder': (_store_get_requests, None, 25),
                                  },
                                  ),
    }

    _defaults = {
        'state': lambda *a: 'draft',
        'reference' : lambda *args: '/',
    }

    def create(self, cr, uid, values, context=None):
        if values.get('reference', '/') == '/':
            values['reference'] = self.pool.get('ir.sequence').get(cr, uid, 'training.pshr')
        return super(training_participation_stakeholder_request, self).create(cr, uid, values, context)

    def on_change_job(self, cr, uid, ids, job_id, context=None):
        if not job_id:
            return False

        job = self.pool.get('res.partner.job').browse(cr, uid, job_id, context=context)
        return {
            'value' : {
                'email': job.email,
                'manual_price': False,
            }
        }

    @tools.cache(skiparg=4)
    def _get_stock_location(self, cr, uid, context=None):
        r = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')], context=context, limit=1)
        if not r:
            return False
        return r[0]

    def _create_PO(self, cr, uid, ids, context=None):
        po_proxy = self.pool.get('purchase.order')

        for this in self.browse(cr, uid, ids, context=context):
            po_id = po_proxy.create(cr, uid, {
                'name': "Session - %s" % (this.session_id.name),
                'partner_id': this.job_id.name.id,
                'contact_id': this.job_id.contact_id.id,
                'partner_address_id': this.job_id.address_id.id,
                'pricelist_id': this.job_id.name.property_product_pricelist_purchase.id,
                'location_id': self._get_stock_location(cr, uid, context),
                'invoice_method' : 'order',
            }, context=context)

            this.write({'purchase_order_id' : po_id})

            for sh in this.participation_ids:
                sh.create_purchase_order_line(po_id)

    def action_create_purchase_order(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if not obj.payment_mode:
                raise osv.except_osv(_('Error'),
                                     _('The Payment Mode is not specified'))
        self._create_PO(cr, uid, ids, context=context)

        tax_ids = self.pool.get('account.tax').search(cr, uid, [('description', '=', 'VP00')], context=context)

        for obj in self.browse(cr, uid, ids, context=context):
            if obj.purchase_order_id:
                for line in obj.purchase_order_id.order_line:
                    if obj.payment_mode == 'contract':
                        line.write({'taxes_id' : [(6, 0, tax_ids)]})
        return True

    def _confirm_PO(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')
        for this in self.browse(cr, uid, ids, context=context):
            #if not this.purchase_order_id:
            #    this._create_PO(context)

            workflow.trg_validate(uid, 'purchase.order', this.purchase_order_id.id, 'purchase_confirm', cr)

    def _approve_PO(self,cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')

        for this in self.browse(cr, uid, ids, context=context):
            if this.purchase_order_id:
                workflow.trg_validate(uid, 'purchase.order', this.purchase_order_id.id, 'purchase_approve', cr)

    def _cancel_PO(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')
        for this in self.browse(cr, uid, ids, context=context):
            if this.purchase_order_id:
                workflow.trg_validate(uid, 'purchase.order', this.purchase_order_id.id, 'purchase_cancel', cr)


    def _spread_wkf_signal(self, cr, uid, ids, signal, context=None):
        workflow = netsvc.LocalService('workflow')
        for this in self.browse(cr, uid, ids, context):
            for sh in this.participation_ids:
                workflow.trg_validate(uid, 'training.participation.stakeholder', sh.id, signal, cr)


    def action_wkf_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancelled'}, context=context)
        self._cancel_PO(cr, uid, ids, context)
        self._spread_wkf_signal(cr, uid, ids, 'signal_cancel', context)

    def test_wkf_valid(self, cr, uid, ids, context=None):
        return all(bool(request.purchase_order_id) != False for request in self.browse(cr, uid, ids, context=context))

    def action_wkf_valid(self, cr, uid, ids, context=None):
        self._confirm_PO(cr, uid, ids, context)
        return self.write(cr, uid, ids, {'state': 'valid'}, context=context)

    def test_wkf_request(self, cr, uid, ids, context=None):
        return all(bool(request.purchase_order_id) != False for request in self.browse(cr, uid, ids, context=context))

    def action_wkf_request(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'requested'}, context=context)
        #self._create_PO(cr, uid, ids, context=context)

    def test_wkf_accept(self, cr, uid, ids, context=None):
        return all(bool(request.purchase_order_id) != False for request in self.browse(cr, uid, ids, context=context))

    def sh_sort_by_date(self, x, y):
        """Used for sorting list of browse_record() by date
           Usage: List.sort(cmp=sh_short_by_date)"""
        if x.date < y.date:
            return -1
        if x.date > y.date:
            return 1
        return 0

    def action_wkf_accept(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'accepted'}, context=context)
        self._approve_PO(cr, uid, ids, context=context)
        self._spread_wkf_signal(cr, uid, ids, 'signal_accept', context)

        email_proxy = self.pool.get('training.email')
        for this in self.browse(cr, uid, ids, context=context):
            seances = list(sh.seance_id for sh in this.participation_ids)
            seances.sort(cmp=self.sh_sort_by_date)
            email_proxy.send_email(cr, uid, 'sh_accept', 'sh', this.email, session=this.session_id, context=context, seances=seances, request=this)

        return True

    def action_wkf_send_request_email(self, cr, uid, ids, context=None):
        email_proxy = self.pool.get('training.email')
        for this in self.browse(cr, uid, ids, context=context):
            seances = list(sh.seance_id for sh in this.participation_ids)
            seances.sort(cmp=self.sh_sort_by_date)
            email_proxy.send_email(cr, uid, 'sh_request', 'sh', this.email, session=this.session_id, context=context, seances=seances, request=this)

        return True

    def action_wkf_send_cancellation_email(self, cr, uid, ids, context=None):
        email_proxy = self.pool.get('training.email')
        for this in self.browse(cr, uid, ids, context=context):
            seances = list(sh.seance_id for sh in this.participation_ids)
            seances.sort(cmp=self.sh_sort_by_date)
            email_proxy.send_email(cr, uid, 'sh_cancel', 'sh', this.email, session=this.session_id, context=context, seances=seances, request=this)

        return True

    def action_wkf_refuse(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'refused'}, context=context)
        self._cancel_PO(cr, uid, ids, context)
        self._spread_wkf_signal(cr, uid, ids, 'signal_refuse', context)

        email_proxy = self.pool.get('training.email')

        for this in self.browse(cr, uid, ids, context=context):
            seances = list(sh.seance_id for sh in this.participation_ids)
            seances.sort(cmp=self.sh_sort_by_date)
            email_proxy.send_email(cr, uid, 'sh_refuse', 'sh', this.email, session=this.session_id, context=context, seances=seances, request=this)

        return True

    def test_wkf_done(self, cr, uid, ids, context=None):
        return all(participation.state == 'done' for request in self.browse(cr, uid, ids, context) for participation in request.participation_ids)

    def action_wkf_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)

training_participation_stakeholder_request()

class training_participation_stakeholder(osv.osv):
    _name = 'training.participation.stakeholder'
    _rec_name = 'job_id'

    def on_change_job(self, cr, uid, ids, job_id, context=None):
        if not job_id:
            return False

        job = self.pool.get('res.partner.job').browse(cr, uid, job_id, context=context)
        return {'value' : {
            'manual_price': False,
        }}

    def on_change_seance(self, cr, uid, _, job_id, seance_id, context=None):
        seance = seance_id and self.pool.get('training.seance').browse(cr, uid, seance_id, context) or False
        return {'value': {
            'group_id': seance and seance.group_id.id or False,
            'date': seance and seance.date or False,
            'kind': seance and seance.kind or False,
            'course_id': seance and seance.course_id.id or False,
            'duration': seance and seance.duration or False,
            'state_seance': seance and seance.state or False,
            'product_id': seance and seance._get_product().id or False,

            'price': self._default_price_compute(cr, uid, job_id, seance, context=context)
        }}

    def on_change_manual(self, cr, uid, ids, manual, job_id, seance_id, context=None):
        if not manual:
            return {}
        return {'value': {
            'forced_price': self._default_price_compute(cr, uid, job_id, seance_id, context=context),
        }}

    def on_change_product(self, cr, uid, ids, job_id, seance_id, product_id, context=None):
        return {'value': {
            'price': self._default_price_compute(cr, uid, job_id, seance_id, product_id, context)
        }}

    def _default_price_compute(self, cr, uid, job, seance, product_id=None, context=None):
        if not job or not seance:
            return False

        if isinstance(seance, (int, long)):
            seance = self.pool.get('training.seance').browse(cr, uid, seance, context=context)

        course = seance.course_id
        if not course:
            return False

        if product_id and isinstance(product_id, (int,long)):
            product = self.pool.get('product.product').browse(cr, uid, product_id)
        else:
            product = seance._get_product()
        if not product:
            raise osv.except_osv(_('Error'),
                                 _("The type of the course (%s) of this seance has no product defined") % course.name)

        if isinstance(job, (int, long)):
            job = self.pool.get('res.partner.job').browse(cr, uid, job, context=context)

        pricelist = job.name.property_product_pricelist_purchase
        if not pricelist:
            # no pricelist available: use the product cost price
            unit_price = product.standard_price
        else:
            pricelists = self.pool.get('product.pricelist')
            unit_price = pricelists.price_get(cr, uid, [pricelist.id], product.id, seance.duration, job.name)[pricelist.id]

        return unit_price * seance.duration

    def _get_price(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0.0)
        for this in self.browse(cr, uid, ids, context=context):
            if this.manual_price:
                res[this.id] = this.forced_price
            else:
                prod_id = this.product_id and this.product_id.id or None
                res[this.id] = self._default_price_compute(cr, uid, this.job_id, this.seance_id, product_id=prod_id, context=context)
        return res

    _columns = {
        'request_id': fields.many2one('training.participation.stakeholder.request', 'Request', readonly=True, required=True, ondelete='cascade'),
        'request_session_id': fields.related('request_id', 'session_id', type='many2one', relation='training.session', readonly=True),
        'seance_id' : fields.many2one('training.seance',
                                      'Seance',
                                      required=True,
                                      select=1,
                                      help='Select the Seance',
                                      ondelete='cascade',
                                      domain="[('date', '>=', time.strftime('%Y-%m-%d'))]"
                                     ),
        'group_id' : fields.related('seance_id', 'group_id', type='many2one', relation='training.group', readonly=True, select=1, store=True, string='Group'),
        'job_id': fields.related('request_id', 'job_id', string="Contact", type='many2one', relation='res.partner.job', readonly=True),
        'contact_id' : fields.related('job_id', 'contact_id', type='many2one', relation='res.partner.contact', readonly=True, store=True, select=2),
        'partner_id' : fields.related('job_id', 'name', type='many2one', relation='res.partner', readonly=True, store=True, string="Partner", select=2),
        'date' : fields.related('seance_id', 'date', type='datetime', string='Date', readonly=True, select=1, store=True),
        'kind' : fields.related('seance_id', 'kind',
                                type='selection',
                                selection=[('standard', 'Course')],
                                string='Kind',
                                readonly=True,
                                select=1),
        'course_id' : fields.related('seance_id', 'course_id',
                                     type='many2one',
                                     relation='training.course',
                                     string='Course',
                                     readonly=True,
                                     select=1),

        'state' : fields.selection([('draft', 'Draft'),
                                    ('accepted', 'Accepted'),
                                    ('refused', 'Refused'),
                                    ('cancelled', 'Cancelled'),
                                    ('done', 'Done'),
                                   ],
                                   'State',
                                   required=True,
                                   readonly=True,
                                   select=1,),
        'duration' : fields.related('seance_id', 'duration', type='float', string='Duration', readonly=True, store=True),

        'state_seance' : fields.related('seance_id', 'state', type='selection',
                                        selection=[('opened', 'Opened'),
                                                   ('confirmed', 'Confirmed'),
                                                   ('inprogress', 'In Progress'),
                                                   ('closed', 'Closed'),
                                                   ('cancelled', 'Cancelled'),
                                                   ('done', 'Done')
                                                  ],
                                        string='State of Seance',
                                        readonly=True,
                                       ),

        'purchase_order_line_id' : fields.many2one('purchase.order.line',
                                                   'Purchase Order Line',
                                                   readonly=True),
        'purchase_order_id' : fields.related('purchase_order_line_id', 'order_id',
                                             string='Purchase Order',
                                             type='many2one',
                                             relation='purchase.order',
                                             readonly=True),

        'paid' : fields.related('purchase_order_id', 'invoiced', type='boolean', string='Invoiced & Paid', readonly=True, select=1),

        'manual_price': fields.boolean('Manual Price'),
        'forced_price': fields.float('Renumeration', required=True, digits_compute=dp.get_precision('Account'),),
        'price' : fields.function(_get_price, method=True,
                                  string='Remuneration',
                                  type='float',
                                  digits_compute=dp.get_precision('Account'),
                                  store=True,
                                 ),
        'product_id' : fields.many2one('product.product', 'Product', select=2),
    }

    _defaults = {
        'manual_price': lambda *a: False,
    }

    def create_purchase_order_line(self, cr, uid, ids, po_id, context=None):
        po_proxy = self.pool.get('purchase.order')
        pol_proxy = self.pool.get('purchase.order.line')
        workflow = netsvc.LocalService('workflow')

        for obj in self.browse(cr, uid, ids, context=context):
            #product = obj.seance_id.course_id.course_type_id.product_id
            product = obj.seance_id._get_product()
            if not product:
                raise osv.except_osv(_('Error'),
                                     _("The type of the course (%s) of this seance hasn't a product") % obj.seance_id.course_id.name)

            price = obj.price
            qty = obj.seance_id.duration * 1.0

            values = {
                'name' : 'Seance %s - %s' % (obj.seance_id.name, obj.seance_id.date),
                'date_planned' : obj.seance_id.date,
                'order_id' : po_id,
                'price_unit' : price / qty,
                'product_qty' : qty,
                'product_id' : product.id,
                'product_uom' : product.uom_id.id,
                'taxes_id': [(6, 0, [ tax.id for tax in product.supplier_taxes_id if product.supplier_taxes_id ])],
                'account_analytic_id': obj.seance_id.course_id.analytic_account_id and obj.seance_id.course_id.analytic_account_id.id or '',
            }

            pol_id = pol_proxy.create(cr, uid, values, context=context)
            obj.write({'purchase_order_line_id' : pol_id})
            #workflow.trg_validate(uid, 'purchase.order', po_id, 'purchase_confirm', cr)

    def _check_disponibility(self, cr, uid, ids, context=None):
        for this in self.browse(cr, uid, ids, context=context):
            contact = this.job_id.contact_id
            cr.execute("""SELECT s.id
                            FROM training_participation_stakeholder sh INNER JOIN training_seance s ON sh.seance_id = s.id,
                                 training_participation_stakeholder this INNER JOIN training_seance this_seance ON this.seance_id = this_seance.id
                           WHERE sh.id != %s
                             AND this.id = %s
                             AND sh.state in ('requested', 'confirmed')
                             AND sh.contact_id = %s
                             AND (     (this_seance.date BETWEEN s.date AND s.date + (s.duration * interval '1 hour'))
                                  OR (this_seance.date + (this_seance.duration * interval '1 hour') BETWEEN s.date AND s.date + (s.duration * interval '1 hour'))
                                  OR (this_seance.date < s.date AND this_seance.date + (this_seance.duration * interval '1 hour') > s.date + (s.duration * interval '1 hour'))
                                  )
                       """, (this.id, this.id, contact.id))
            res = cr.fetchone()
            if res:
                name = '%s %s' % (contact.first_name, contact.name)
                other_seance = self.pool.get('training.seance').browse(cr, uid, res[0], context)

                raise osv.except_osv(_('Error'), _('%(stakeholder)s is not available for seance "%(this_seance)s" because (s)he is already requested or confirmed for the seance "%(other_seance)s"') % {'stakeholder':name, 'this_seance': this.seance_id.name, 'other_seance': other_seance.name})

        return True

    def send_email(self, cr, uid, ids, trigger, session, context=None, objects_by_ids=None):
        if objects_by_ids is None:
            objects_by_ids = {}
        email_proxy = self.pool.get('training.email')
        for sh in self.browse(cr, uid, ids, context=context):
            if sh.request_id and sh.request_id.email:
                email_proxy.send_email(cr, uid, trigger, 'sh', sh.request_id.email, session=session, context=context, sh=sh, **objects_by_ids.get(sh.id, {}))

    def _test_wkf(self, cr, uid, ids, state, context=None):
        for this in self.browse(cr, uid, ids, context):
            if this.request_id:
                if this.request_id.state != state:
                    return False
        return True

    def _action_wkf(self, cr, uid, ids, state, purchase_order_signal, context=None):
        # First, validate or cancel the purcchase order line (at least try to)
        wkf = netsvc.LocalService('workflow')
        for this in self.browse(cr, uid, ids, context):
            if this.purchase_order_line_id:
                wkf.trg_validate(uid, 'purchase.order.line', this.purchase_order_line_id.id, purchase_order_signal, cr)

        # Second, change the participation state
        self.write(cr, uid, ids, {'state': state}, context=context)
        return True

    def action_wkf_cancel(self, cr, uid, ids, context=None):
        return self._action_wkf(cr, uid, ids, 'cancelled', 'purchase_cancel', context)

    def test_wkf_accept(self, cr, uid, ids, context=None):
        return self._test_wkf(cr, uid, ids, 'accepted', context)

    def action_wkf_accept(self, cr, uid, ids, context=None):
        return self._action_wkf(cr, uid, ids, 'accepted', 'purchase_approve', context)

    def test_wkf_refuse(self, cr, uid, ids, context=None):
        return self._test_wkf(cr, uid, ids, 'refused', context)

    def action_wkf_refuse(self, cr, uid, ids, context=None):
        return self._action_wkf(cr, uid, ids, 'refused', 'purchase_cancel', context)

    def test_wkf_done(self, cr, uid, ids, context=None):
        return all(participation.state_seance == 'done' for participation in self.browse(cr, uid, ids, context))

    def action_wkf_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done'}, context=context)

        # spread the signal to the request
        wkf = netsvc.LocalService('workflow')
        for this in self.browse(cr, uid, ids, context):
            wkf.trg_validate(uid, 'training.participation.stakeholder.request', this.request_id.id, 'signal_done', cr)

        return True

    def _check_request(self, cr, uid, ids, context=None):
        return all(this.request_id.session_id in this.seance_id.session_ids for this in self.browse(cr, uid, ids, context))

    _constraints = [
#        (lambda self, *args, **kwargs: self._check_disponibility(*args, **kwargs), "Please, Can you check the disponibility of the stakeholder", ['date', 'seance_id', 'contact_id']),
         (_check_request, "The request is not linked to a session of the seance", ['seance_id', 'request_id']),
    ]

    _sql_constraints = [
        ('uniq_seance_lecturer', 'unique(seance_id, contact_id)', "The contact is already associated to the seance"),
    ]

    def _state_default(self, cr, uid, context=None):
        return 'draft'

    _defaults = {
        #'state' : lambda *a: 'draft',
        'state' : _state_default,
    }

    _order = "date asc"

training_participation_stakeholder()

class training_course_pending_reason(osv.osv):
    _name = 'training.course.pending.reason'

    _columns = {
        'code' : fields.char('Code', size=32, required=True),
        'name' : fields.char('Name', size=32, translate=True, required=True),
    }

    _sql_constraints = [
        ('uniq_code', 'unique(code)', "Must be unique"),
    ]

training_course_pending_reason()

def training_course_pending_reason_compute(obj, cr, uid, context=None):
    proxy = obj.pool.get('training.course.pending.reason')
    return [(reason.code, reason.name) for reason in proxy.browse(cr, uid, proxy.search(cr, uid, []))] or []

class training_course_pending(osv.osv):
    _name = 'training.course.pending'


    def _seance_next_date_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, '') #time.strftime('%Y-%m-%d %H:%M:%S'))

        for obj in self.browse(cr, uid, ids, context=context):
            cr.execute("""
                       SELECT MIN(sea.date)
                       FROM training_session_seance_rel tssr, training_seance sea, training_session ses
                       WHERE sea.id = tssr.seance_id
                       AND ses.id = tssr.session_id
                       AND sea.date >= %s
                       AND ses.STATE IN ('opened', 'opened_confirmed', 'inprogress', 'closed_confirmed')
                       AND sea.course_id = %s
                       """, (time.strftime('%Y-%m-%d %H:%M:%S'), obj.course_id.id))
            values = cr.fetchone()
            value = values[0]

            if value:
                res[obj.id] = value

        return res

    _columns = {
        'followup_by' : fields.many2one('res.users', 'Followup By', required=True, select=1),
        'course_id' : fields.many2one('training.course', 'Course', select=1, required=True),
        'type_id' : fields.related('course_id', 'course_type_id', type='many2one', relation='training.course_type',  string='Type'),
        'category_id' : fields.related('course_id', 'category_id', type='many2one', relation='training.course_category',  string='Category'),
        'lang_id' : fields.related('course_id', 'lang_id', type='many2one', relation='res.lang', string='Language'),
        'state' : fields.related('course_id', 'state_course',
                                 type='selection',
                                 selection=[('draft', 'Draft'),
                                            ('pending', 'Pending'),
                                            ('inprogress', 'In Progress'),
                                            ('deprecated', 'Deprecated'),
                                            ('validated', 'Validated'),
                                           ],
                                 select=1,
                                 string='State',
                                ),
        'type' : fields.selection(training_course_pending_reason_compute,
                                    'Reason',
                                    size=32,
                                    select=1),
        'date' : fields.date('Planned Date'),
        'reason' : fields.text('Note'),
        'purchase_order_id' : fields.many2one('purchase.order', 'Purchase Order'),
        'create_date' : fields.datetime('Create Date', readonly=True),
        'job_id' : fields.many2one('res.partner.job', 'Contact', required=True),
        'job_email' : fields.char('Email', size=64),
        'seance_next_date' : fields.function(_seance_next_date_compute,
                                             method=True,
                                             string='Seance Next Date',
                                             type='datetime'),
        'todo' : fields.boolean('Todo'),
    }

    def on_change_job(self, cr, uid, ids, job_id, context=None):
        if not job_id:
            return False

        job = self.browse(cr, uid, job_id, context=context)
        return {
            'value' : {
                'job_email' : job.email
            }
        }

    def action_open_course(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)

        res = {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'training.course',
            'view_id': self.pool.get('ir.ui.view').search(cr,uid,[('name','=','training.course.form')]),
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id' : this.course_id.id,
        }
        return res

    def action_validate_course(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)

        workflow = netsvc.LocalService("workflow")
        return workflow.trg_validate(uid, 'training.course', this.course_id.id, 'signal_validate', cr)

    _defaults = {
        'todo' : lambda *a: 0,
        'followup_by' : lambda obj, cr, uid, context: uid,
    }

training_course_pending()

class training_course_pending_wizard(osv.osv_memory):
    _name = 'training.course.pending.wizard'

    _columns = {
        'course_id' : fields.many2one('training.course', 'Course'),
        'type' : fields.selection(training_course_pending_reason_compute,
                                    'Type',
                                    size=32,
                                    required=True),
        'date' : fields.date('Planned Date'),
        'reason' : fields.text('Reason'),
        'job_id' : fields.many2one('res.partner.job', 'Contact', required=True),
        'state' : fields.selection([('first_screen', 'First Screen'),
                                    ('second_screen', 'Second Screen')],
                                   'State')
    }

    _defaults = {
        'type' : lambda *a: 'update_support',
        'state' : lambda *a: 'first_screen',
        'course_id' : lambda obj, cr, uid, context: context.get('active_id', 0)
    }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type' : 'ir.actions.act_window_close'}

    def action_apply(self, cr, uid, ids, context=None):
        course_id = context and context.get('active_id', False) or False

        if not course_id:
            return False

        this = self.browse(cr, uid, ids)[0]

        workflow = netsvc.LocalService('workflow')
        workflow.trg_validate(uid, 'training.course', course_id, 'signal_pending', cr)

        values = {
            'course_id' : course_id,
            'type' : this.type,
            'date' : this.date,
            'reason' : this.reason,
            'job_id' : this.job_id and this.job_id.id,
        }

        self.pool.get('training.course.pending').create(cr, uid, values, context=context)

        return {'res_id' : course_id}

training_course_pending_wizard()


class training_contact_course(osv.osv):
    _name = 'training.contact.course'
    _auto = False

    _columns = {
        'function' : fields.char('Function', size=64, readonly=True),
        'course_id' : fields.many2one('training.course', 'Course', readonly=True),
        'contact_id' : fields.many2one('res.partner.contact', 'Contact', readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'training_contact_course')
        cr.execute("CREATE OR REPLACE VIEW training_contact_course as ( "
                   "SELECT job.id, function, rel.course_id, rel.job_id, job.contact_id "
                   "FROM training_course_job_rel rel, (SELECT id, contact_id, function FROM res_partner_job) AS job "
                   "WHERE job.id = rel.job_id )")

training_contact_course()

class res_partner_contact(osv.osv):
    _inherit = 'res.partner.contact'

    _columns = {
        'course_ids' : fields.one2many('training.contact.course', 'contact_id', 'Courses', readonly=True),
    }

res_partner_contact()

class training_session_duplicate_wizard(osv.osv_memory):
    _name = 'training.session.duplicate.wizard'

    _columns = {
        'session_id': fields.many2one('training.session', 'Session',
                                      required=True,
                                      readonly=True,
                                      domain=[('state', 'in', ['opened', 'opened_confirmed'])]),
        'group_id' : fields.many2one('training.group', 'Group',
                                     domain="[('session_id', '=', session_id)]"),
        'subscription_line_ids' : fields.many2many('training.subscription.line',
                                                   'training_sdw_participation_rel',
                                                   'wizard_id',
                                                   'participation_id',
                                                   'Participations',
                                                   domain="[('session_id', '=', session_id),('state', '=', 'confirmed')]"),
    }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type' : 'ir.actions.act_window_close'}

    def action_apply(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)

        if len(this.subscription_line_ids) == 0:
            raise osv.except_osv(_('Error'),
                                 _('You have not selected a participant of this session'))

        seances = []

        if any(len(seance.session_ids) > 1 for seance in this.session_id.seance_ids):
            raise osv.except_osv(_('Error'),
                                 _('You have selected a session with a shared seance'))

        #if not all(seance.state == 'opened' for seance in this.session_id.seance_ids):
        #    raise osv.except_osv(_('Error'),
        #                         _('You have to open all seances in this session'))

        lengths = [len(group.seance_ids)
                   for group in this.session_id.group_ids
                   if group != this.group_id]

        if len(lengths) == 0:
            raise osv.except_osv(_('Error'),
                                 _('There is no group in this session !'))

        minimum, maximum = min(lengths), max(lengths)

        if minimum != maximum:
            raise osv.except_osv(_('Error'),
                                 _('The defined groups for this session does not have the same number of seances !'))

        group_id = this.session_id.group_ids[0]

        seance_sisters = {}
        for group in this.session_id.group_ids:
            for seance in group.seance_ids:
                seance_sisters.setdefault((seance.date, seance.duration, seance.course_id, seance.kind,), {})[seance.id] = None

        seance_ids = []

        if len(this.group_id.seance_ids) == 0:
            proxy_seance = self.pool.get('training.seance')

            for seance in group_id.seance_ids:
                values = {
                    'group_id' : this.group_id.id,
                    'presence_form' : 'no',
                    'manual' : 0,
                    'participant_count_manual' : 0,
                    'contact_ids' : [(6, 0, [])],
                    'participant_ids' : [],
                    'duplicata' : 1,
                    'duplicated' : 1,
                    'is_first_seance' : seance.is_first_seance,
                }

                seance_ids.append( proxy_seance.copy(cr, uid, seance.id, values, context=context) )
        else:
            # If the there are some seances in this group
            seance_ids = [seance.id for seance in this.group_id.seance_ids]

        for seance in self.pool.get('training.seance').browse(cr, uid, seance_ids, context=context):
            key = (seance.date, seance.duration, seance.course_id, seance.kind,)
            if key in seance_sisters:
                for k, v in seance_sisters[key].items():
                    seance_sisters[key][k] = seance.id
            else:
                seance_sisters[key][seance.id] = seance.id

        final_mapping = {}
        for key, values in seance_sisters.iteritems():
            for old_seance_id, new_seance_id in values.iteritems():
                final_mapping[old_seance_id] = new_seance_id

        for sl in this.subscription_line_ids:
            for part in sl.participation_ids:
                part.write({'seance_id' : final_mapping[part.seance_id.id]})

        return {'type' : 'ir.actions.act_window_close'}

    def default_get(self, cr, uid, fields, context=None):
        record_id = context and context.get('record_id', False) or False

        res = super(training_session_duplicate_wizard, self).default_get(cr, uid, fields, context=context)

        if record_id:
            res['session_id'] = record_id

        return res

training_session_duplicate_wizard()

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    _columns = {
        'contact_id': fields.many2one('res.partner.contact', 'Contact'),
        'seance_id': fields.many2one('training.seance', 'Seance', readonly=True),
        'course_id': fields.many2one('training.course', 'Course', readonly=True),

        'date_approved' : fields.datetime('Date Approved', readonly=True),
    }

    def action_po_create(self, cr, uid, po_line_ids, location_id, context=None):
        """ function action_po_assign from mrp module, modified to fullfill needs
            or basing training purchase system """
        if not context:
            context = {}
        purchase_id = False
        company = self.pool.get('res.users').browse(cr, uid, uid, context).company_id
        for po_line in self.pool.get('training.seance.purchase_line').browse(cr, uid, po_line_ids, context=context):
            partner = po_line.product_id.seller_ids[0].name
            partner_id = partner.id
            address_id = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['delivery'])['delivery']
            pricelist_id = partner.property_product_pricelist_purchase.id

            uom_id = po_line.product_id.uom_po_id.id

            qty = self.pool.get('product.uom')._compute_qty(cr, uid, po_line.product_uom.id, po_line.proc_qty, uom_id)
            if po_line.product_id.seller_ids[0].qty:
                qty=max(qty,po_line.product_id.seller_ids[0].qty)

            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id], po_line.product_id.id, qty, False, {'uom': uom_id})[pricelist_id]

            newdate = mx.DateTime.strptime(po_line.seance_id.date, '%Y-%m-%d %H:%M:%S')
            newdate = newdate - mx.DateTime.RelativeDateTime(days=company.po_lead)
            newdate = newdate - po_line.product_id.seller_ids[0].delay

            #Passing partner_id to context for purchase order line integrity of Line name
            context.update({'lang':partner.lang, 'partner_id':partner_id})

            product=self.pool.get('product.product').browse(cr,uid, po_line.product_id.id,context=context)


            line = {
                'name': product.partner_ref,
                'product_qty': qty,
                'product_id': po_line.product_id.id,
                'product_uom': uom_id,
                'price_unit': po_line.product_price,
                'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
                'notes':product.description_purchase,
                'seance_id': po_line.seance_id.id,
                'course_id': po_line.course_id.id,
            }

            if po_line.course_id:
                journal_ids = self.pool.get('account.analytic.journal').search(cr, uid, [('type','=','general'),('active','=',True)])
                if journal_ids:
                    journal_id = journal_ids[0]

                    plan_id = self.pool.get('account.analytic.plan.instance').create(cr, uid, {
                        'name': po_line.course_id.name,
                        'journal_id': journal_id,
                        'account_ids': [(0, 0, {'analytic_account_id': po_line.course_id.analytic_account_id.id, 'rate': 100.0})],
                    }, context=context)

                    line['analytics_id'] = plan_id

            if po_line.attachment_id:
                if not po_line.description:
                    name = "%s (%s)" % (po_line.product_id.name, po_line.attachment_id.name,)
                else:
                    name = po_line.description

                note = []
                for component in po_line.attachment_id.component_ids:
                    note.append("%sx %s" % (component.product_qty, component.product_id.name,))

                if po_line.attachment_id.support_note:
                    note.append("==================================")
                    note.append(po_line.attachment_id.support_note)

                if po_line.seance_id.location_id:
                   note.append("==================================")
                   note.append(po_line.seance_id.location_id.name)

                line.update({'name': name, 'notes' : "\n".join(note)})

            else:
                line.update({'name' : po_line.description})

            taxes_ids = po_line.product_id.product_tmpl_id.supplier_taxes_id
            taxes = self.pool.get('account.fiscal.position').map_tax(cr, uid, partner.property_account_position, taxes_ids)
            line.update({
                'taxes_id':[(6,0,taxes)]
            })
            purchase_id = self.pool.get('purchase.order').create(cr, uid, {
                'name': 'Seance %s - %s' % (po_line.seance_id.name, po_line.seance_id.date,),
                'origin': '',
                'partner_id': partner_id,
                'partner_address_id': address_id,
                'location_id': po_line.seance_id.location_id and po_line.seance_id.location_id.id or False,
                'pricelist_id': pricelist_id,
                'order_line': [(0,0,line)],
                'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                'seance_id': po_line.seance_id.id,
                'course_id': po_line.course_id.id,
            })

            get_first_po_line = self.pool.get('purchase.order').browse(cr, uid, purchase_id, context=context).order_line[0]
            if po_line.attachment_id:
                attachment = {'res_model': 'purchase.order.line', 'res_id': get_first_po_line.id}
                new_id = self.pool.get('ir.attachment').copy(cr, uid, po_line.attachment_id.id, attachment, context=context)

            workflow = netsvc.LocalService('workflow')
            workflow.trg_validate(uid, 'purchase.order', purchase_id, "purchase_confirm", cr)
        return purchase_id

    def create_from_procurement_line(self, cr, uid, po_line, quantity, location_id, context=None):
        """ proxy function for creating procurment from seance.purchase.line object """
        procurement_id = self.action_po_create(cr, uid, [po_line.id], location_id, context=context)
        return procurement_id

purchase_order()

class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'

    _columns = {
        'seance_id_int' : fields.related('seance_id', 'id', type='integer', readonly=True, string="Seance ID"),

        'seance_id': fields.many2one('training.seance', 'Seance', readonly=True),
        'course_id': fields.many2one('training.course', 'Course', readonly=True),
        'state': fields.related('order_id', 'state',
                                type='selection',
                                selection = [('draft', 'Request for Quotation'),
                                             ('wait', 'Waiting'),
                                             ('confirmed', 'Confirmed'),
                                             ('approved', 'Approved'),
                                             ('except_picking', 'Shipping Exception'),
                                             ('except_invoice', 'Invoice Exception'),
                                             ('done', 'Done'),
                                             ('cancel', 'Cancelled')
                                            ],
                                string='Order Status',
                                readonly=True,
                                help="The state of the purchase order or the quotation request. A quotation is a purchase order in a 'Draft' state. Then the order has to be confirmed by the user, the state switch to 'Confirmed'. Then the supplier must confirm the order to change the state to 'Approved'. When the purchase order is paid and received, the state becomes 'Done'. If a cancel action occurs in the invoice or in the reception of goods, the state becomes in exception.",
                                select=True
                               ),
    }

    def approved_cb(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')
        for pol in self.browse(cr, uid, ids, context=context):
            if len(pol.order_id.order_line) in (0, 1):
                workflow.trg_validate(uid, 'purchase.order', pol.order_id.id, 'purchase_approve', cr)
                pol.order_id.write({'date_approved' : time.strftime('%Y-%m-%d %H:%M:%S')})
            else:
                raise osv.except_osv(_('Warning'),
                                     _('You can not approve this purchase line it is not the only one purchase order lines in the purchase order'))

        return True

    def cancel_cb(self, cr, uid, ids, context=None):
        workflow = netsvc.LocalService('workflow')
        for pol in self.browse(cr, uid, ids, context=context):
            if len(pol.order_id.order_line) in (0, 1):
                workflow.trg_validate(uid, 'purchase.order', pol.order_id.id, 'purchase_cancel', cr)
            else:
                raise osv.except_osv(_('Warning'),
                                     _('You can not cancel this purchase line it is not the only one purchase order lines in the purchase order'))

        return True

purchase_order_line()


class training_config_product(osv.osv):
    _name = 'training.config.product'

    _columns = {
        'type' : fields.selection(
            [
                ('support_of_course', 'Support of Course'),
                ('voucher', 'Voucher'),
            ],
            'Type',
            required=True),
        'product_id' : fields.many2one('product.product', 'Product', required=True),
    }

    _sql_constraints = [
        ('uniq_type_product', 'unique(type, product_id)', "You can not assign twice the same product to the same type"),
    ]

training_config_product()

class res_lang(osv.osv):
    _inherit = 'res.lang'

    _columns = {
        'code' : fields.char('Code', size=5, required=True, select=1),
        'name' : fields.char('Name', size=64, required=True, select=1),
    }

res_lang()

class training_subscription_cancellation_wizard(osv.osv_memory):
    _name = 'training.subscription.cancellation.wizard'

    _description = 'Training Subscription Cancellation Wizard'

    _columns = {
        'subscription_line_id' : fields.many2one('training.subscription.line', 'Subscription Line',
                                                 domain="[('state', 'in', ['draft', 'confirmed']),('session_id.state', 'in', ('opened', 'opened_confirmed', 'closed_confirmed'))]",
                                                 required=True
                                                ),
        'subscription_id' : fields.related('subscription_line_id', 'subscription_id',
                                           type='many2one',
                                           relation='training.subscription',
                                           string='Subscription',
                                           readonly=True),

        'partner_id' : fields.related('subscription_line_id', 'subscription_id', 'partner_id',
                                      type='many2one',
                                      relation='res.partner',
                                      string='Partner',
                                      readonly=True),

        'participant_id' : fields.related('subscription_line_id', 'job_id',
                                          type='many2one',
                                          relation='res.partner.job',
                                          string='Participant',
                                          readonly=True),

        'session_id' : fields.related('subscription_line_id', 'session_id',
                                      type='many2one',
                                      relation='training.session',
                                      string='Session',
                                      readonly=True),

        'session_offer_id' : fields.related('subscription_line_id', 'session_id', 'offer_id',
                                            type='many2one',
                                            relation='training.session',
                                            string='Session Offer',
                                            readonly=True),

        'session_date' : fields.related('subscription_line_id', 'session_id', 'date',
                                        type='datetime',
                                        string='Session Date',
                                        readonly=True),

        'session_state' : fields.related('subscription_line_id', 'session_id', 'state',
                                         type='selection',
                                         selection=[
                                             ('draft', 'Draft'),
                                             ('opened', 'Opened'),
                                             ('opened_confirmed', 'Confirmed'),
                                             ('closed_confirmed', 'Closed Subscriptions'),
                                             ('inprogress', 'In Progress'),
                                             ('closed', 'Closed'),
                                             ('cancelled', 'Cancelled')
                                         ],
                                         string='Session State',
                                         readonly=True),

        'new_participant_id' : fields.many2one('res.partner.job', 'Participant',
                                               domain="[('name', '=', partner_id),('id', '!=', participant_id),('state', '=', 'current')]"),

        'new_participant_email' : fields.char('Email', size=128),

        'new_session_id' : fields.many2one('training.session', 'Session',
                                           domain="[('state', 'in', ('opened', 'opened_confirmed')),('date', '>', time.strftime('%Y-%m-%d')),('date', '>', session_date),('offer_id', '=', session_offer_id)]"
                                          ),

        'new_session_date' : fields.related('new_session_id', 'date', type='datetime', string='Session Date', readonly=True),

        'cancellation_reason' : fields.text('Reason'),
        'cancellation_medical_certificate_toggle' : fields.boolean('Has Justification'),
        'cancellation_medical_certificate_name' : fields.char('Filename', size=128),
        'cancellation_medical_certificate' : fields.binary('Justification'),

        'state' : fields.selection([('init', 'Init'),
                                    ('replacement', 'Replacement'),
                                    ('postponement', 'Postponement'),
                                    ('cancellation', 'Cancellation'),
                                    ('end', 'End')],
                                   'State',
                                   required=True,
                                   readonly=True
                                  ),



    }

    _defaults = {
        'subscription_line_id' : lambda obj, cr, uid, context: context['active_id'],
        'state' : lambda *a: 'init',
    }

    def on_change_subscription_line(self, cr, uid, ids, subscription_line_id, context=None):
        if not subscription_line_id:
            return {}

        subscription_line = self.pool.get('training.subscription.line').browse(cr, uid, subscription_line_id, context=context)
        return {
            'value' : {
                'subscription_id' : subscription_line.subscription_id.id,
                'subscription_line_id' : subscription_line.id,
                'session_id' : subscription_line.session_id.id,
                'session_date' : subscription_line.session_id.date,
                'session_state' : subscription_line.session_id.state,
                'partner_id' : subscription_line.subscription_id.partner_id.id,
                'participant_id' : subscription_line.job_id.id,
                'session_offer_id' : subscription_line.session_id.offer_id.id,
            }
        }

    def on_change_new_participant(self, cr, uid, ids, new_participant_id, context=None):
        if not new_participant_id:
            return {}

        job = self.pool.get('res.partner.job').browse(cr, uid, new_participant_id, context=context)
        return {'value' : {'new_participant_email' : job.email }}

    def on_change_new_session(self, cr, uid, ids, new_session_id, context=None):
        if not new_session_id:
            return {}

        session = self.pool.get('training.session').browse(cr, uid, new_session_id, context=context)

        return {
            'value' : {
                'new_session_date' : session.date,
            }
        }


    def action_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close'}

    def action_cancellation(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'cancellation'}, context=context)

    def action_replacement(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'replacement'}, context=context)

    def action_postponement(self, cr, uid, ids, context=None):
        # Assign a new session to the subscription line
        return self.write(cr, uid, ids, {'state' : 'postponement'}, context=context)

    def action_apply(self, cr, uid, ids, context=None):
        if not ids:
            return False

        this = self.browse(cr, uid, ids[0], context=context)

        old_participant_id = this.participant_id

        workflow = netsvc.LocalService('workflow')

        context2 = context.copy()
        if 'default_state' in context2:
            del context2['default_state']

        if this.state == 'cancellation':
            if this.cancellation_medical_certificate:
                values = {
                    'name' : 'Medical Certificate',
                    'datas' : this.cancellation_medical_certificate,
                    'datas_fname' : this.cancellation_medical_certificate_name,
                    'description' : 'Medical Certificate',
                    'res_model' : 'training.subscription.line',
                    'res_id' : this.subscription_line_id.id,
                }

                self.pool.get('ir.attachment').create(cr, uid, values, context=context2)

            this.subscription_line_id.write(
                {
                    'has_certificate' : this.cancellation_medical_certificate_toggle,
                    'reason_cancellation' : this.cancellation_reason,
                },
                context=context2
            )

            workflow.trg_validate(uid, 'training.subscription.line', this.subscription_line_id.id, 'signal_cancel', cr)
            sl_proxy = self.pool.get('training.subscription.line')
            sl_proxy.send_email(cr, uid, [ this.subscription_line_id.id ], 'sub_cancelled', context=context)


        elif this.state == 'replacement':
            email_proxy = self.pool.get('training.email')

            objects = {
                'new_participant_id' : this.new_participant_id,
                'old_participant_id' : old_participant_id,
            }

            this.subscription_line_id.write( { 'job_id' : this.new_participant_id.id, 'job_email' : this.new_participant_email, })

            internal_note = []

            if this.subscription_line_id.internal_note:
                internal_note.append(this.subscription_line_id.internal_note)

            internal_note.append(_("Replacement: %s %s -> %s %s") % (old_participant_id.contact_id.first_name,
                                                                     old_participant_id.contact_id.name,
                                                                     this.new_participant_id.contact_id.first_name,
                                                                     this.new_participant_id.contact_id.name))

            this.subscription_line_id.write({'internal_note' : "\n----\n".join(internal_note)})

            email_proxy.send_email(cr, uid,
                             'sub_replacement',
                             'hr',
                             this.subscription_line_id.partner_hr_email,
                             session=this.subscription_line_id.session_id,
                             context=context2,
                             subline=this.subscription_line_id,
                             **objects)

            #if this.subscription_line_id.job_id.name.notif_participant and this.new_participant_email:
            #    email_proxy.send(cr, uid,
            #                     'sub_replacement',
            #                     'p',
            #                     this.new_participant_email,
            #                     session=sl.session_id,
            #                     context=context,
            #                     subline=this.subscription_line_id,
            #                     **objects)



        elif this.state == 'postponement':
            values = {
                'session_id' : this.new_session_id.id,
            }
            sl_proxy = self.pool.get('training.subscription.line')

            new_sl_id = sl_proxy.copy(cr, uid, this.subscription_line_id.id, values, context = context2 or {})

            new_sl = sl_proxy.browse(cr, uid, new_sl_id, context=context2)
            new_sl.write({'internal_note' : _("Created by Postponement of %s") % this.subscription_line_id.name})
            this.subscription_line_id.write({'reason_cancellation' : _("Cancelled by Postponement: %s") % new_sl.name })

            if this.subscription_line_id.state == 'confirmed':
                workflow.trg_validate(uid, 'training.subscription.line', new_sl_id, 'signal_confirm', cr)
            workflow.trg_validate(uid, 'training.subscription.line', this.subscription_line_id.id, 'signal_cancel', cr)
        return self.write(cr, uid, ids, {'state' : 'end'}, context=context)

    def action_done(self, cr, uid, ids, context=None):
        return {'type' : 'ir.actions.act_window_close'}

training_subscription_cancellation_wizard()

class training_config_penality(osv.osv):
    _name = 'training.config.penality'

    _columns = {
        'trigger' : fields.selection(
            [
                ('discount_refund', 'Discount Refund'),
                ('discount_invoice', 'Discount Invoice'),
            ],
            'Trigger',
            required=True,
            select=1,
        ),
        'rate' : fields.float('Rate'),
    }

    def _check_value(self, cr, uid, ids, context=None):
        return all(obj.rate >= 0.0 and obj.rate <= 100.0 for obj in self.browse(cr, uid, ids, context=context))

    _constraints = [
        (_check_value, "You can not have a value lesser than 0.0 !", ['rate'])
    ]

    _sql_constraints = [
        ('uniq_trigger', 'unique(trigger)', "You can not define twice the same trigger !"),
    ]

training_config_penality()

class training_config_invoice(osv.osv):
    _name = 'training.config.invoice'

    _columns = {
        'threshold' : fields.selection(
            [
                ('minimum', 'Minimum'),
                ('maximum', 'Maximum'),
            ],
            'Threshold',
            required=True,
            select=1,
        ),
        'price' : fields.float('Price'),
    }

    def _check_value(self, cr, uid, ids, context=None):
        return all(obj.price >= 0.0 for obj in self.browse(cr, uid, ids, context=context))

    _constraints = [
        (_check_value, "You can not have a value lesser than 0.0 !", ['price'])
    ]

    _sql_constraints = [
        ('uniq_threshold', 'unique(threshold)', "You can not define twice the same threshold !"),
    ]

training_config_invoice()

class training_participation_reassign_wizard(osv.osv_memory):
    _name = 'training.participation.reassign.wizard'

    _columns = {
        'participation_id' : fields.many2one('training.participation', 'Participation', required=True),
        'participation_seance_id' : fields.related('participation_id', 'seance_id', type='many2one', relation='training.seance', readonly=True, string='Seance'),
        'participation_seance_date' : fields.related('participation_id', 'seance_id', 'date', type='datetime', readonly=True, string='Date'),
        'participation_sl' : fields.related('participation_id', 'subscription_line_id', type='many2one', relation='training.subscription.line', readonly=True, string='Subscription Line'),
        'participation_session_id' : fields.related('participation_id', 'subscription_line_id', 'session_id', type='many2one', relation='training.session',
                                                    readonly=True,
                                                    string='Session'),
        'seance_id' : fields.many2one('training.seance', 'Seance',
                                      #domain="[('session_ids', 'in', [participation_session_id])]",
                                      required=True),
    }

    def on_change_seance(self, cr, uid, ids, seance_id, context=None):
        values = {
            'domain' : {
                'participation_id' : not seance_id and [] or [('seance_id', '=', seance_id)],
            }
        }

        return values

    def on_change_participation(self, cr, uid, ids, participation_id, context=None):
        if not participation_id:
            return {
                'value' : {
                    'seance_id' : 0,
                },
                'domain' : {
                    'seance_id' : [],
                },
            }

        p = self.pool.get('training.participation').browse(cr, uid, participation_id, context=context)
        return {
            'value' : {
                'participation_seance_id' : p.seance_id.id,
                'participation_seance_date' : p.seance_id.date,
                'participation_sl' : p.subscription_line_id.id,
                'participation_session_id' : p.subscription_line_id.session_id.id,
            },
            'domain' : {
                'seance_id' : [('id', 'in', [seance.id for seance in p.subscription_line_id.session_id.seance_ids])],
            }
        }

    def close_cb(self, cr, uid, ids, context=None):
        return {'type' : 'ir.actions.act_window_close'}

    def apply_cb(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)

        if this.participation_id.seance_id == this.seance_id:
            raise osv.except_osv(_('Warning'),
                                 _('You have selected the same seance'))

        this.participation_id.write({'seance_id' : this.seance_id.id})

        return {'type' : 'ir.actions.act_window_close'}

training_participation_reassign_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
