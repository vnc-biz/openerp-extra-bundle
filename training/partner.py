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

from osv import osv, fields
import time
import tools
from tools.translate import _

class res_partner_contact_technical_skill(osv.osv):
    _name = 'res.partner.contact_technical_skill'

    _columns = {
        'name' : fields.char('Name', size=32, select=True, required=True,
                            help="The name of the technical skill"),
    }

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Unique name for the technical skill')
    ]

res_partner_contact_technical_skill()

class training_subscription_line(osv.osv):
    _name = 'training.subscription.line'

training_subscription_line()

class res_partner_address(osv.osv):
    _inherit = 'res.partner.address'
    _order = "(type != 'default')"      # default addresses first...
res_partner_address()

class res_partner_contact(osv.osv):
    _inherit = 'res.partner.contact'

    _columns = {
        'matricule' : fields.char('Matricule', size=32,
                                  help="The matricule of the contact"),
        'birthplace' : fields.char('BirthPlace', size=64,
                                   help="The birthplace of the contact"),
        'education_level' : fields.char('Education Level', size=128),
        'technical_skill_ids' : fields.many2many('res.partner.contact_technical_skill',
                                                 'res_partner_contact_technical_skill_rel',
                                                 'contact_id',
                                                 'skill_id',
                                                 'Technical Skill'),
        'linguistic_skill_ids': fields.many2many('res.lang',
                                                 'res_partner_contact_linguistic_skill_rel',
                                                 'contact_id',
                                                 'skill_id',
                                                 'Linguistic Skill'),
        #'subscription_ids' : fields.one2many('training.subscription.line', 'contact_id', 'Subscription Lines'),
    }

    _defaults = {
        'matricule' : lambda *a: '',
    }

    def _get_function_by_kind(self, cr, uid, kind, context=None):
        proxy = self.pool.get('training.config.contact.function')
        ids = proxy.search(cr, uid, [('kind', '=', kind)], context=context)
        res = [ obj.function for obj in proxy.browse(cr, uid, ids, context=context) ]
        if not len(res):
            raise osv.except_osv(_('Warning'),
                                 _("""Do not forget to configure the contact's function"""))
        return res

    def search(self, cr, uid, domain, offset = 0, limit = None, order = None, context = None, count = False):
        function = context and context.get('function', False) or False

        if function:
            proxy = self.pool.get('training.config.contact.function')
            ids = proxy.search(cr, uid, [('kind', '=', function)], context=context)
            if not ids:
                raise osv.except_osv(_('Warning'),
                                     _("Please, Could you configure the contact's function ?"))

            functions = [x.function for x in proxy.browse(cr, uid, ids, context=context)]

            cr.execute("SELECT distinct(contact_id) "
                       "FROM res_partner_job "
                       "WHERE function in (" + ','.join(['%s']*len(functions)) + ")"
                       "  AND state = 'current'", functions)
            contact_ids = set([x[0] for x in cr.fetchall()])

            if domain:
                ids = super(res_partner_contact, self).search(cr, uid, domain, offset=offset, limit=limit, order=order, context=context, count=count)
                contact_ids = contact_ids & set(ids)

            return list(contact_ids)

        return super(res_partner_contact, self).search(cr, uid, domain, offset=offset, limit=limit,
                                                   order=order, context=context, count=count)

res_partner_contact()

class res_partner_job(osv.osv):
    _inherit = 'res.partner.job'
    _columns = {
        'external_matricule' : fields.char('Matricule', size=32),
        'departments' : fields.text('Departments'),
        'orientation' : fields.text('Orientation'),
        'birthdate' : fields.related('contact_id', 'birthdate', type='date', readonly=True,
                                     store=True),
        'pricelist_id' : fields.related('name', 'property_product_pricelist', string='Pricelist', type='many2one', relation='product.pricelist', readonly=True, store=True),
        'contact_firstname' : fields.related('contact_id', 'first_name', string='Contact First Name', readonly=True),
        'contact_lastname' : fields.related('contact_id', 'name', string='Contact Last Name', readonly=True),
    }

    _sql_constraints = [
        ('uniq_cont_add_func', 'unique(contact_id, address_id, function, state)', "Unique Exception, You can only have one job per contact, address, function and state"),
    ]

    def onchange_address_id(self, cr, uid, ids, address_id):
        if not address_id:
            return {'value': {'name': False}}

        addr_pool = self.pool.get('res.partner.address')
        _name = addr_pool.browse(cr, uid, address_id).partner_id.id
        return {'value': {'name': _name}}

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
        partner_id = context and context.get('partner_id', False) or False
        job_search_context = 'ignore_past'
        if context and context.get('job_search_context', ''):
            job_search_context = context.get('job_search_context')

        domain = []
        if job_search_context == 'ignore_past':
            domain = [('state', '=', 'current')]

        if partner_id:
            domain.extend([('name', '=', partner_id)])

        if name:
            q = """
                SELECT t.id
                FROM (
                        SELECT rpc.id, (CASE WHEN rpc.first_name IS NOT NULL THEN rpc.first_name ELSE '' END)||' '||rpc.name as full_name
                        FROM res_partner_contact rpc
                        ORDER BY full_name
                    ) as t
                WHERE t.full_name ilike %s
                LIMIT %s

            """
            cr.execute(q, ('%' + '%'.join(name.replace("'",'').split(' ')) + '%', limit or 80))
            contact_ids = [ x[0] for x in cr.fetchall() ]
            domain.extend([('contact_id', 'in', contact_ids)])

        return self.name_get(cr, uid, self.search(cr, uid, domain, context=context, limit=limit), context=context)

    def search(self, cr, uid, domain, offset = 0, limit = None, order = None, context = None, count = False):
        partner_id = context and context.get('partner_id', False) or False
        if partner_id:
            domain.extend([('name','=', partner_id)])

        function = context and context.get('function', False) or False
        if function:
            proxy = self.pool.get('training.config.contact.function')
            ids = proxy.search(cr, uid, [('kind', '=', function)], context=context)
            if not ids:
                raise osv.except_osv(_('Warning'),
                                     _("Please, Could you configure the contact's function ?"))

            functions = [x.function for x in proxy.browse(cr, uid, ids, context=context)]

            proxy = self.pool.get('res.partner.job')
            job_ids = proxy.search(cr, uid,
                                   domain + [('function', 'in', functions),('state', '=', 'current')])

            if not job_ids:
                raise osv.except_osv(_('Warning'),
                                     _("Please, Could you check the functions because the system does not find any function with the status 'current'"))


            course_ids = []

            offer_id = context and context.get('offer_id', False) or False

            if offer_id:
                cr.execute("SELECT course_id FROM training_course_offer_rel WHERE offer_id = %s", (offer_id,))
                course_ids = [x[0] for x in cr.fetchall()]
            else:
                course_id = context and context.get('course_id', False) or False
                if course_id:
                    course_ids = [course_id]


            if course_ids:
                cr.execute("SELECT job_id "
                           "FROM training_course_job_rel "
                           "WHERE course_id in (" + ",".join(['%s'] * len(course_ids)) + ") "
                           "  AND job_id in " + '(' + ','.join(['%s'] * len(job_ids)) + ')', course_ids + job_ids)
                return [x[0] for x in cr.fetchall()]

            return job_ids

        res = super(res_partner_job, self).search(cr, uid, domain, offset=offset, limit=limit,
                                                   order=order, context=context, count=count)
        return res

res_partner_job()

class training_course_category(osv.osv):
    _name = 'training.course_category'
training_course_category()

class res_partner_team(osv.osv):
    _inherit = 'res.partner.team'
    _columns = {
        'specialisation_id' : fields.many2one('training.course_category', 'Specialisation',
                                              required=True,
                                              help="A Quality Team has a particularity")
    }

res_partner_team()

class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'notif_contact_id' : fields.many2one('res.partner.job',
                                             'Subscription Contact',
                                             domain="[('name', '=', active_id), ('state', '=', 'current')]",
                                             help="The person to contact if the the partner want to receive a notification for a subscription"),
        'notif_invoicing_id' : fields.many2one('res.partner.job',
                                             'Invoicing Contact',
                                             domain="[('name', '=', active_id), ('state', '=', 'current')]",
                                             help="The person to contact for things related to invoicing on partner side."),
        'notif_participant' : fields.boolean('Participant',
                                            help="Allows to know if the participant wants to receive a notification"),

        'no_penalties': fields.boolean('No Penalties', help='Allow to not invoice this partner in case of subscription cancellation'),

    }

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
