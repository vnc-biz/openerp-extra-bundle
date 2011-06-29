# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jesús Martín <jmartin@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
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
##############################################################################


from osv import fields, osv
from tools.translate import _
from datetime import date
        
def strToDate(dt):
    return date(int(dt[0:4]),int(dt[5:7]),int(dt[8:10]))

class dining_hall_subscription(osv.osv_memory):

    _name = "dining.hall.subscription"
    _rec_name = 'vat'

    def _bank_type_get(self, cr, uid, context=None):
        bank_type_obj = self.pool.get('res.partner.bank.type')

        result = []
        type_ids = bank_type_obj.search(cr, uid, [])
        bank_types = bank_type_obj.browse(cr, uid, type_ids, context=context)
        for bank_type in bank_types:
            result.append((bank_type.code, bank_type.name))
        return result
        
    _columns = {
        # res.partner -> Family's data
        'partner_id': fields.many2one('res.partner', 'Family'),
        'name': fields.char('Family Name', size=128),
        'vat': fields.char('Bank Owner VAT', size=32, required=True, help="You must input the VAT of the bank account owner for its search."),

        # res.partner.bank -> Family's account bank data
        'bank_id': fields.many2one('res.partner.bank', 'Bank Account'),
        'acc_number': fields.char('Account Number', size=64),
        'bank': fields.many2one('res.bank', 'Bank'),
        'owner_name': fields.char('Account Owner', size=64),
        'bank_state': fields.selection(_bank_type_get, 'Bank Type', change_default=True),

        # res.partner.address -> Family's address
        'address_id': fields.many2one('res.partner.address', 'Address'),
        'street': fields.char('Street', size=128),
        'zip': fields.char('Zip', change_default=True, size=24),
        'city': fields.char('City', size=128),
        'state_id': fields.many2one("res.country.state", 'Fed. State'),
        'country_id': fields.many2one('res.country', 'Country'),
        'email': fields.char('E-Mail', size=240),

        # res.partner.contact -> First_parent's data
        'first_parent_id': fields.many2one('res.partner.contact', 'First Parent'),
        'first_parent_name': fields.char('Last Name', size=64),
        'first_parent_first_name': fields.char('First Name', size=64),
        'first_parent_vat': fields.char('VAT', size=32, help="VAT"),

        # res.partner.job -> First_parent's data
        'first_parent_job_id': fields.many2one('res.partner.job', 'First Parent Main Function and Address'),
        'first_parent_phone': fields.char('Phone', size=64, help="Job Phone no."),

        # res.partner.contact -> Second_parent's data
        'second_parent_id': fields.many2one('res.partner.contact', 'Second Parent'),
        'second_parent_name': fields.char('Last Name', size=64),
        'second_parent_first_name': fields.char('First Name', size=64),
        'second_parent_vat': fields.char('VAT', size=32, help="VAT"),

        # res.partner.job -> Second_parent's data
        'second_parent_job_id': fields.many2one('res.partner.job', 'Second Parent Main Function and Address'),
        'second_parent_phone': fields.char('Phone', size=64, help="Job Phone no."),

        # res.partner.contact -> Student's data
        'student_id': fields.many2one('res.partner.contact', 'Student'),
        'job_id': fields.many2one('res.partner.job', 'Student Main Function and Address'),
        'student_name': fields.char('Last Name', size=64),
        'student_first_name': fields.char('First Name', size=64),
        'group_id': fields.many2one('training.group', 'Group', help='The group that owns this contact.'),

        #~ 'training.group'
        'session_id' : fields.many2one('training.session', 'Session'),

        # training.dining_hall.weekdays -> Student weekdays' data
        'weekdays_id': fields.many2one('training.dining_hall.weekdays', 'Weekdays'),
        'date_from': fields.date('Date from', help="The start date of period."),
        'date_to': fields.date('Date to', help="The end date of period."),
        'sunday': fields.boolean('Sunday', help="Select it if the contact goes to the dining hall on Sunday."),
        'monday': fields.boolean('Monday', help="Select it if the contact goes to the dining hall on Monday."),
        'tuesday': fields.boolean('Tuesday', help="Select it if the contact goes to the dining hall on Tuesday."),
        'wednesday': fields.boolean('Wednesday', help="Select it if the contact goes to the dining hall on Wednesday."),
        'thursday': fields.boolean('Thursday', help="Select it if the contact goes to the dining hall on Thursday."),
        'friday': fields.boolean('Friday', help="Select it if the contact goes to the dining hall on Friday."),
        'saturday': fields.boolean('Saturday', help="Select it if the contact goes to the dining hall on Saturday."),

        'state': fields.selection([
            ('first','First'),
            ('second', 'Second'),
            ('third', 'Third'),
            ('done','Done'),
        ],'State', readonly=True),
    }

    _defaults = {
        'state': lambda *a: 'first',
    }

    def _get_parents(self, cr, uid, partner, context=None):
        if context is None:
            context = {}
        result = {}
        if partner.address:
            for address in partner.address:
                result['address_id'] = address.id
                result['street'] = address.street
                result['zip'] = address.zip
                result['city'] = address.city
                result['state_id'] = address.state_id.id
                result['country_id'] = address.country_id.id
                result['email'] = address.email
                if address.job_ids:
                    for job in address.job_ids:
                        contact = job.contact_id
                        if job.function == _('Parent') and 'first_parent_name' not in result:
                            result['first_parent_job_id'] = job.id
                            result['first_parent_name'] = contact.name
                            result['first_parent_first_name'] = contact.first_name
                            result['first_parent_vat'] = contact.vat
                            result['first_parent_id'] = contact.id
                            result['first_parent_phone'] = job.phone
                        elif job.function == _('Parent'):
                            result['second_parent_job_id'] = job.id
                            result['second_parent_name'] = contact.name
                            result['second_parent_first_name'] = contact.first_name
                            result['second_parent_vat'] = contact.vat
                            result['second_parent_id'] = contact.id
                            result['second_parent_phone'] = job.phone
        return result

    def _get_partner_bank(self, cr, uid, partner, context=None):
        if context is None:
            context = {}
        result = {}
        if partner.bank_ids:
            result['vat'] = partner.vat
            for bank in partner.bank_ids:
                if bank.default_bank:
                    result['bank_id'] = bank.id
                    result['acc_number'] = bank.acc_number
                    result['bank'] = bank.bank.id
                    result['bank_state'] = bank.state
                    result['owner_name'] = bank.owner_name
        return result        

    def confirm_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        result = {}         
        data = self.browse(cr, uid, ids[0], context=context)
        result['vat'] = data.vat.upper()
        contact_obj = self.pool.get('res.partner.contact')
        contact_ids = contact_obj.search(cr, uid, [('vat', 'ilike', '%' + data.vat)], context = context)
        for contact in contact_obj.browse(cr, uid, contact_ids, context = context):
            jobs = contact.job_ids
            # If the contact have only one family:
            if len(jobs) == 1:
                for job in jobs:
                    partner = job.name
                    result.update(self._get_parents(cr, uid, partner, context = context))
                    result.update(self._get_partner_bank(cr, uid, partner, context = context))
                    result['partner_id'] = partner.id
                    result['name'] = partner.name
            # If the contact have more than one family:    
            elif len(jobs) > 1:
                raise osv.except_osv(_('Alert!'), _('This parent has more than one family! Enter the data manually.'))
            elif len(contact_ids) == 1:
                result['first_parent_name'] = contact.name
                result['first_parent_first_name'] = contact.first_name
                result['first_parent_vat'] = contact.vat
                result['first_parent_id'] = contact.id
                if contact.partner_id:
                    result['partner_id'] = partner.id
                    result['name'] = partner.name 
        result['state'] = 'second'
        return self.write(cr, uid, ids, result, context=context)

    def confirm_contact(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        result = {}
        data = self.browse(cr, uid, ids[0], context=context)
        weekdays_obj = self.pool.get('training.dining_hall.weekdays')
        #~ contact_obj = self.pool.get('res.partner.contact')
        #~ contact_ids = contact_obj.search(cr, uid, [('partner_id','=',data.partner_id'), ('job_id', '=', data.job_id), ('first_name', '=', data.student_first_name)], context = context)
        #~ contacts = contact_obj.browse(cr, uid, contact_ids, context = context)
        job_obj = self.pool.get('res.partner.job')
        job_ids = job_obj.search(cr, uid, [('address_id', '=', data.address_id.id), ('contact_id.first_name','=',data.student_first_name)], context = context)
        jobs = job_obj.browse(cr, uid, job_ids, context = context)
        if len(jobs) == 1:
            for job in jobs:
                contact = job.contact_id
                result['job_id'] = job.id
                #~ result['contact_id'] = contact.id
                result['student_name'] = contact.name
                result['student_first_name'] = contact.first_name
                result['student_id'] = contact.id
                if contact.group_id and contact.group_id.session_id:
                    result['group_id'] = contact.group_id.id
                    result['session_id'] = contact.group_id.session_id.id
                    last_line = date.min
                    last_weekdays = None
                    if contact.weekdays_ids:
                        today = date.today()
                        for weekdays in contact.weekdays_ids:
                            if strToDate(weekdays.date_from) > last_line:
                                last_line = strToDate(weekdays.date_from)
                                last_weekdays = weekdays
                        if strToDate(last_weekdays.date_to) >= today:
                            result['weekdays_id'] = last_weekdays.id
                            result['date_from'] = last_weekdays.date_from
                        else:
                            result['date_from'] = date.today().strftime('%Y-%m-%d')
                        result['sunday'] = last_weekdays.sunday
                        result['monday'] = last_weekdays.monday
                        result['tuesday'] = last_weekdays.tuesday
                        result['wednesday'] = last_weekdays.wednesday
                        result['thursday'] = last_weekdays.thursday
                        result['friday'] = last_weekdays.friday
                        result['saturday'] = last_weekdays.saturday
                        result['date_to'] = contact.group_id.session_id.date_end
        result['state'] = 'third'

        return self.write(cr, uid, ids, result, context=context)

    def done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        result = True
        data = self.browse(cr, uid, ids[0], context = context)

        # Save partner data
        partner_obj = self.pool.get('res.partner')
        partner_ids = partner_obj.search(cr, uid, [('id', '=', data.partner_id.id)], context = context)
        partner_values = {
            'name': data.name,
            'vat': data.vat,
        }
        if len(partner_ids) == 1:
            result = result and partner_obj.write(cr, uid, partner_ids, partner_values, context = context)
            partner_id = data.partner_id.id
        else:
            partner_id = partner_obj.create(cr, uid, partner_values, context = context)

        # Save address data
        address_obj = self.pool.get('res.partner.address')
        address_ids = address_obj.search(cr, uid, [('id', '=', data.address_id.id)], context = context)
        address_values = {
            'street': data.street,
            'zip': data.zip,
            'city': data.city,
            'state_id': data.state_id.id,
            'country_id': data.country_id.id,
            'email': data.email,
            'partner_id': partner_id,
            'dafeult_bank': True,
        }
        if len(address_ids) == 1:
            result = result and address_obj.write(cr, uid, address_ids, address_values, context = context)
            address_id = data.address_id.id
        else:
            address_values['partner_id'] = partner_id
            address_id = address_obj.create(cr, uid, address_values, context = context)

        # Safe bank data
        bank_obj = self.pool.get('res.partner.bank')
        bank_ids = bank_obj.search(cr, uid, [('id', '=', data.bank_id.id)], context = context)
        bank_values = {
            'bank': data.bank.id,
            'owner_name': data.owner_name,
            'street': data.street,
            'zip': data.zip,
            'city': data.city,
            'state': data.bank_state,
            'state_id': data.state_id.id,
            'country_id': data.country_id.id,
            'partner_id': partner_id,
            'default_bank' : True,
        }
        bank_type_obj = self.pool.get('res.partner.bank.type')
        type_ids = bank_type_obj.search(cr, uid, [('code','=',data.bank_state)], context = context)
        types = bank_type_obj.browse(cr, uid, type_ids, context = context)
        cr.execute("SELECT name from res_partner_bank_type_field where bank_type_id='"+str(type_ids[0])+"' and required='t'")
        acc_field = cr.fetchall()
        if len(acc_field[0]) == 1:
            bank_values[acc_field[0][0]] = data.acc_number
        #~ else:
            #~ raise osv.except_osv(_('TODO!'), _('IBAN Account Bank not implemented yet! Please, select Account Bank.'))
        module_obj = self.pool.get('ir.module.module')
        module_ids = module_obj.search(cr, uid, [('state','like','installed'), ('name','like','l10n_es_partner')], context = context)
        if len(module_ids) == 1:
            bank_values['acc_country_id'] = data.country_id.id
        if len(bank_ids) == 1:
            result = result and bank_obj.write(cr, uid, bank_ids, bank_values, context = context)
            bank_id = data.bank_id.id
        else:
            bank_id = bank_obj.create(cr, uid, bank_values, context = context)

        contact_obj = self.pool.get('res.partner.contact')

        # Safe first parent contact data
        first_parent_ids = contact_obj.search(cr, uid, [('id', '=', data.first_parent_id.id)], context = context)
        first_parent_values = {
            'name': data.first_parent_name,
            'first_name': data.first_parent_first_name,
            'vat': data.first_parent_vat,
        }
        if len(first_parent_ids) == 1:
            result = result and contact_obj.write(cr, uid, first_parent_ids, first_parent_values, context = context)
            first_parent_id = data.first_parent_id.id
        else:
            first_parent_id = contact_obj.create(cr, uid, first_parent_values, context = context)

        job_obj = self.pool.get('res.partner.job')

        # Save first parent job data
        first_parent_job_ids = job_obj.search(cr, uid, [('id', '=', data.first_parent_job_id.id)], context = context)
        first_parent_job_values = {
            'phone': data.first_parent_phone,
            'contact_id': first_parent_id,
            'function': _('Parent'),
            'address_id': address_id,
        }
        if len(first_parent_job_ids) == 1:
            result = result and job_obj.write(cr, uid, first_parent_job_ids, first_parent_job_values, context = context)
            first_parent_job_id = data.first_parent_job_id.id
        else:
            first_parent_job_id = job_obj.create(cr, uid, first_parent_job_values, context = context)

        # Safe second parent contact data
        if data.second_parent_name:
            second_parent_ids = contact_obj.search(cr, uid, [('id', '=', data.second_parent_id.id)], context = context)
            second_parent_values = {
                'name': data.second_parent_name,
                'first_name': data.second_parent_first_name,
                'vat': data.second_parent_vat,
            }
            if len(second_parent_ids) == 1:
                result = result and contact_obj.write(cr, uid, second_parent_ids, second_parent_values, context = context)
                second_parent_id = data.second_parent_id.id
            else:
                second_parent_id = contact_obj.create(cr, uid, second_parent_values, context = context)

            # Save second parent job data
            job_obj = self.pool.get('res.partner.job')
            second_parent_job_ids = job_obj.search(cr, uid, [('id', '=', data.second_parent_job_id.id)], context = context)
            second_parent_job_values = {
                'phone': data.second_parent_phone,
                'contact_id': second_parent_id,
                'function': _('Parent'),
                'name': partner_id,
            }
            if len(second_parent_job_ids) == 1:
                result = result and job_obj.write(cr, uid, second_parent_job_ids, second_parent_job_values, context = context)
                second_parent_job_id = data.second_parent_job_id.id
            else:
                second_parent_job_values['address_id'] = address_id
                second_parent_job_values['contact_id'] = second_parent_id
                second_parent_job_id = job_obj.create(cr, uid, second_parent_job_values, context = context)

        # Safe student contact data
        student_ids = contact_obj.search(cr, uid, [('id', '=', data.student_id.id)], context = context)
        student_values = {
            'name': data.student_name,
            'first_name': data.student_first_name,
            'group_id': data.group_id.id,
        }
        if len(student_ids) == 1:
            result = result and contact_obj.write(cr, uid, student_ids, student_values, context = context)
            student_id = data.student_id.id
        else:
            student_id = contact_obj.create(cr, uid, student_values, context = context)

        # Save student job data
        student_job_ids = job_obj.search(cr, uid, [('id', '=', data.job_id.id)], context = context)
        student_job_values = {}
        if len(student_job_ids) == 1:
            student_job_id = data.job_id.id
        else:
            student_job_values['address_id'] = address_id
            student_job_values['contact_id'] = student_id
            student_job_values['function'] = _('Student')
            student_job_id = job_obj.create(cr, uid, student_job_values, context = context)

        # Save weekdays data
        weekdays_obj = self.pool.get('training.dining_hall.weekdays')
        weekdays_ids = weekdays_obj.search(cr, uid, [('id', '=', data.weekdays_id.id)], context = context)
        weekdays_values = {
            'date_from': data.date_from,
            'date_to': data.date_to,
            'sunday': data.sunday,
            'monday': data.monday,
            'tuesday': data.tuesday,
            'wednesday': data.wednesday,
            'thursday': data.thursday,
            'friday': data.friday,
            'saturday': data.saturday,
        }
        if len(weekdays_ids) == 1:
            result = result and weekdays_obj.write(cr, uid, weekdays_ids, weekdays_values, context = context)
            weekdays_id = data.weekdays_id.id
        else:
            weekdays_values['contact_id'] = student_id
            weekdays_id = weekdays_obj.create(cr, uid, weekdays_values, context = context)

        participation_generator = self.pool.get('training.participation.generator')
        student = contact_obj.browse(cr, uid, student_id, context = context)
        res = participation_generator.generate(cr, uid, student, context = context)

        return {
            'name': '',
            'first_name': '',
            'group_id': None,
            'name':_("Contact"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'res.partner.contact',
            'res_id': student_id,
            'type': 'ir.actions.act_window',
            'nodestroy': False,
            'target': 'current',
            'domain': '[]',
            'context': context,
        }
        
    def to_first(self, cr, uid, ids, context=None):
        values = {
            'partner_id': None,
            'name': '',
            'bank_id': None,
            'acc_number': '',
            'bank': None,
            'owner_name': '',
            'bank_state': '',
            'address_id': None,
            'street': '',
            'zip': '',
            'city': '',
            'state_id': None,
            'country_id': None,
            'email': '',
            'first_parent_id': None,
            'first_parent_name': '',
            'first_parent_first_name': '',
            'first_parent_vat': '',
            'first_parent_job_id': None,
            'first_parent_phone': '',
            'second_parent_id': None,
            'second_parent_name': '',
            'second_parent_first_name': '',
            'second_parent_vat': '',
            'second_parent_job_id': None,
            'second_parent_phone': '',
            'student_id': None,
            'job_id': None,
            'student_first_name': '',
            'state': 'first',
        }
        return self.write(cr, uid, ids, values, context=context)

    def to_second(self, cr, uid, ids, context=None):
        value = {
            'weekdays_id': None,
            'date_from': None,
            'date_to': None,
            'sunday': '',
            'monday': '',
            'tuesday': '',
            'wednesday': '',
            'thursday': '',
            'friday': '',
            'saturday': '',
            'student_name': '',
            'group_id': None,
            'session_id': None,
            'state': 'second',
        }
        return self.write(cr, uid, ids, value, context=context)
        
dining_hall_subscription()
