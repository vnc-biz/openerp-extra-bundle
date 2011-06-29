# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jesús Martín <jmartin@zikzakmedia.com>
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
##############################################################################

from osv import osv, fields
import decimal_precision as dp
from tools.translate import _
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta

weekdays = {
    0: 'monday',
    1: 'tuesday',
    2: 'wednesday',
    3: 'thursday',
    4: 'friday',
    5: 'saturday',
    6: 'sunday',
}
        
def strToDate(dt):
    return date(int(dt[0:4]),int(dt[5:7]),int(dt[8:10]))

#class training_dining_hall_scholarship(osv.osv):
#    _name = 'training_dining_hall.scholarship'
#    _columns = {
#        'name': fields.char('Scholarship', size=32, required=True, help='Scholarship identifier.'),
#        'type': fields.char('Type', size=32, help='pending.'),
#        'mask': fields.char('Mask', size=32, help='pending.'),
#        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account'), help='Amount of the scholarship.'),
#        'return_type': fields.char('Return Type', size=32, help='pending.'),
#        'num_intervals': fields.integer('Number of Intervals', help='Number of intervals in the invoiced period.'),
#        'unit_intervals': fields.selection([
#            ('daily', 'Daily'),
#            ('weekly', 'Weekly'),
#            ('monthly', 'Monthly')
#        ], 'Frequency', help='Units of the invoiced period.'),
#        'student_id': fields.many2one('res.partner.contact', 'Student', required=True, help='The student related with the scholarship.'),
#        'partner_id': fields.many2one('res.partner', 'Partner', required=True, help='The Partner related with the scholarship.'),
#    }
#    _defaults = {
#        'unit_intervals': 'monthly',
#    }
#    
#training_dining_hall_scholarship()


class training_dining_hall_rule_line(osv.osv):
    _name='training.dining_hall.rule.line'

training_dining_hall_rule_line()


class training_dining_hall_rule(osv.osv):
    _name='training.dining_hall.rule'

training_dining_hall_rule()


class training_group_special_day(osv.osv):
    _name = 'training.group.special_day'

training_group_special_day()


class training_dining_hall_special_day_type(osv.osv):
    _name = 'training.dining_hall.special_day.type'

    _columns = {
        'name':fields.char('Special Day Type', size=32, required = True, help="The name of the special day type."),
    }

training_dining_hall_special_day_type()


class training_dining_hall_menu_type(osv.osv):

    _name='training.dining_hall.menu_type'
    _description = 'Define a type of dining hall menu.'

    _columns = {
        'name':fields.char('Menu Type', size=32, required=True, help="The name of the type of the menu."),
    }
    _order = 'name'
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name of the Menu Type must be unique!')
    ]

training_dining_hall_menu_type()


class training_dining_hall_rule_line_product(osv.osv):
    _name = 'training.dining_hall.rule.line.product'

    _columns = {
        'dining_rule_line_id': fields.many2one('training.dining_hall.rule.line', 'Rule Line', help = 'The rule line related with this product.'),
        'product_id': fields.many2one('product.product', 'Product', required = True, help = 'The product related with this rule line.'),
        'price': fields.float('Price', digits_compute = dp.get_precision('Account')),
        'type':fields.selection([
            ('stable','Stable'),
            ('eventual','Eventual'),
            ('picnic','Picnic'),
            ('absent','Absent'),
        ],'Type'),
    }

training_dining_hall_rule_line_product()


class training_dining_hall_rule_line(osv.osv):
    _name='training.dining_hall.rule.line'

    def _compute(self, cr, uid, rule_line, rule_line_product, rule_line_price):
        if rule_line_price == 0.0:
            pricelist = rule_line.dining_rule_id.school_id.partner_id.property_product_pricelist.id
            if pricelist:
                amount_total = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], rule_line_product.id, 1.0)[pricelist]
            else:
                amount_total = rule_line_product.lst_price
        else:
            amount_total = rule_line_price
        return amount_total

    def onchange_rule_line_product_ids(self, cr, uid, ids, line_products=False, context=None):
        res = {'value': {}}
        res['value']["stable_price"] = 0.0
        res['value']["eventual_price"] = 0.0
        res['value']["picnic_price"] = 0.0
        res['value']["absent_price"] = 0.0
        for line_product in line_products:
            if line_product[2]['dining_rule_line_id'] and line_product[2]['product_id']:
                rule_line = self.browse(cr, uid, line_product[2]['dining_rule_line_id'], context=context)
                rule_line_product = self.pool.get('product.product').browse(cr, uid, line_product[2]['product_id'], context=context)
                if line_product[2]['type'] == "stable":
                    res['value']["stable_price"] += self._compute(cr, uid, rule_line, rule_line_product, line_product[2]['price'])
                if line_product[2]['type'] == "eventual":
                    res['value']["eventual_price"] += self._compute(cr, uid, rule_line, rule_line_product, line_product[2]['price'])
                if line_product[2]['type'] == "picnic":
                    res['value']["picnic_price"] += self._compute(cr, uid, rule_line, rule_line_product, line_product[2]['price'])
                if line_product[2]['type'] == "absent":
                    res['value']["absent_price"] += self._compute(cr, uid, rule_line, rule_line_product, line_product[2]['price'])
        return res

    def _total(self, cr, uid, ids, name, args, context=None):
        """ Calculates Sub total
        @param name: Names of fields.
        @param arg: User defined arguments
        @return: Dictionary of values.
        """
        if not ids or not name:
            return {}
        res = {}
        for rule_line in self.browse(cr, uid, ids, context=context):
            res[rule_line.id] = {
                'stable_price': 0.0,
                'eventual_price': 0.0,
                'picnic_price': 0.0,
                'absent_price':0.0,
            }
            for rule_line_product in rule_line.stable_ids:
                res[rule_line.id]['stable_price'] += self._compute(cr, uid, rule_line, rule_line_product.product_id, rule_line_product.price)
            for rule_line_product in rule_line.eventual_ids:
                res[rule_line.id]['eventual_price'] += self._compute(cr, uid, rule_line, rule_line_product.product_id, rule_line_product.price)
            for rule_line_product in rule_line.picnic_ids:
                res[rule_line.id]['picnic_price'] += self._compute(cr, uid, rule_line, rule_line_product.product_id, rule_line_product.price)
            for rule_line_product in rule_line.absent_ids:
                res[rule_line.id]['absent_price'] += self._compute(cr, uid, rule_line, rule_line_product.product_id, rule_line_product.price)
        return res

    _columns = {
        'name':fields.char('Rule Line', size=32, help="The name of the rule line."),
        'dining_rule_id': fields.many2one('training.dining_hall.rule', 'Rule', required = True, help = 'The rule related with this rule line.'),
        'menu_type_ids': fields.many2many('training.dining_hall.menu_type', 'menu_type_rule_line_rel', 'rule_line_id', 'menu_type_id', string = 'Menu Types', required = True, help = 'The menu types related with this rule line.'),
        'stable_ids': fields.one2many('training.dining_hall.rule.line.product', 'dining_rule_line_id', string = 'Stable rule lines', domain = [('type','=','stable')]),
        'eventual_ids': fields.one2many('training.dining_hall.rule.line.product', 'dining_rule_line_id', string = 'Eventual rule lines', domain = [('type','=','eventual')]),
        'picnic_ids': fields.one2many('training.dining_hall.rule.line.product', 'dining_rule_line_id', string = 'Picnic rule lines', domain = [('type','=','picnic')]),
        'absent_ids': fields.one2many('training.dining_hall.rule.line.product', 'dining_rule_line_id', string = 'Absent rule lines', domain = [('type','=','absent')]),
        'stable_price': fields.function(_total, method=True, string = 'Total Stable', type = 'float',  digits_compute = dp.get_precision('Account'), multi='price'),
        'eventual_price': fields.function(_total, method=True, string = 'Total Eventual', type = 'float',  digits_compute = dp.get_precision('Account'), multi='price'),
        'picnic_price': fields.function(_total, method=True, string = 'Total Picnic', type = 'float',  digits_compute = dp.get_precision('Account'), multi='price'),
        'absent_price': fields.function(_total, method=True, string = 'Total Absent', type = 'float',  digits_compute = dp.get_precision('Account'), multi='price'),
    }
    
    def _check_lines(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        lines = self.browse(cr, uid, ids, context=context)
        for line in lines:
            for menu_type in line.menu_type_ids:
                # Search dining rule lines with the same menu type and belonging to the same rule (and different from the current line)
                ids = self.search(cr, uid, [('dining_rule_id', '=', line.dining_rule_id.id), ('menu_type_ids', 'in', [menu_type.id]), ('id', '!=', line.id)], context=context)
                if len(ids):
                    return False
        return True
        
    _constraints = [
        (_check_lines, 'Configuration Error! \nYou can\'t define more than one rule line for the same menu types!', ['dining_rule_id']),
    ]

training_dining_hall_rule_line()


class training_dining_hall_special_day_rule(osv.osv):
    _name = 'training.dining_hall.special_day.rule'
    _rec_name = 'special_day_type_id'

    _columns = {
        'dining_rule_id': fields.many2one('training.dining_hall.rule', 'Rule', help = 'Determine the rule of the special day.'),
        'special_day_type_id': fields.many2one('training.dining_hall.special_day.type', 'Special Day Type', required = True, help = 'The type of this special day.'),
        'policy_not_used' : fields.selection([('stable', 'Stable'), ('eventually', 'Eventually'), ('picnic', 'Picnic'), ('absent', 'Absent'), ('not_invoiced', 'Not Invoiced')], 'Policy Not Used'),
    }

training_dining_hall_special_day_rule()


class training_group(osv.osv):
    _name = 'training.group'
    _inherit  =  "training.group"

    _columns = {
        'dining_rule_id': fields.many2one('training.dining_hall.rule', 'Rule', help = 'Determine the rule of the group.'),
        'special_days_ids': fields.one2many('training.group.special_day', 'group_id', string = 'Special Days', help = 'The special days related with this group.'),
    }

training_group()


class training_group_special_day(osv.osv):
    _name = 'training.group.special_day'

    _columns = {
        'group_id': fields.many2one('training.group', 'Group', required = True, help = 'The group related with this special day.'),
        'special_day_type_id': fields.many2one('training.dining_hall.special_day.type', 'Special Day Type', required = True, help = 'The type of this special day.'),
        'date_from': fields.date('Date from', required = True, help="The start date of the special day."),
        'date_to': fields.date('Date to', help="The end date of the special day."),
    }

training_group_special_day()


class training_multi_school(osv.osv):
    _name = 'training.multi.school'
    _inherit  =  "training.multi.school"

    _columns = {
        'rule_ids': fields.one2many('training.dining_hall.rule', 'school_id', string = 'Rules', help = 'Determine the rules of the dining hall.'),
    }

training_multi_school()


class training_dining_hall_rule(osv.osv):
    _name='training.dining_hall.rule'

    _columns = {
        'name':fields.char('Rule', size=64, help="The name of the rule."),
        'active' : fields.boolean('Active'),
        'school_id': fields.many2one('training.multi.school', 'School', required = True, help = 'The school related with this rule.'),
        'group_ids': fields.one2many('training.group', 'dining_rule_id', string = 'Groups', required = True, help = 'The groups related with this dining hall rule.'),
        'min_days' : fields.integer('Minimum Threshold', help="The minimum threshold for this rule."),
        'num_unit_time' : fields.integer('Unit Time Number', help="The unit time number for the minimum threshold rule."),
        'unit_time' : fields.selection([('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'),], 'Unit Time', help='The unit time for the minimum threshold rule'),
        'special_day_ids': fields.one2many('training.dining_hall.special_day.rule', 'dining_rule_id', string = 'Special Day', help = 'The special days related with this dining hall rule.'),
        'line_ids': fields.one2many('training.dining_hall.rule.line', 'dining_rule_id', string = 'Rule Lines', help = 'The rule lines related with  this dining hall rule.'),
    }

    _defaults = {
        'active': True,
    }

training_dining_hall_rule()


class training_dining_hall_weekdays(osv.osv):

    _name='training.dining_hall.weekdays'
    _description = 'Define the weekdays that the contact goes to the dining hall.'
    _rec_name = 'contact_id'
    _columns = {
        'contact_id': fields.many2one('res.partner.contact','Contact'),
        'date_from': fields.date('Date from', required = True, help="The start date of period."),
        'date_to': fields.date('Date to', required = True, help="The end date of period."),
        'sunday': fields.boolean('Sunday', help="Select it if the contact goes to the dining hall on Sunday."),
        'monday': fields.boolean('Monday', help="Select it if the contact goes to the dining hall on Monday."),
        'tuesday': fields.boolean('Tuesday', help="Select it if the contact goes to the dining hall on Tuesday."),
        'wednesday': fields.boolean('Wednesday', help="Select it if the contact goes to the dining hall on Wednesday."),
        'thursday': fields.boolean('Thursday', help="Select it if the contact goes to the dining hall on Thursday."),
        'friday': fields.boolean('Friday', help="Select it if the contact goes to the dining hall on Friday."),
        'saturday': fields.boolean('Saturday', help="Select it if the contact goes to the dining hall on Saturday.")
    }

    def _parent_group(self, cr, uid, parent_group, context=None):
        """ Climbs the ``group.parent_id``
            until it finds the group.seance_ids or
            until it can't find any more parent(s)
        Returns:   parent_group: if find a parent_group with any seance_ids,
                   False: if not find any seance_ids
        """
        if not parent_group.id:
            return False
        elif len(parent_group.seance_ids) != 0:
            return parent_group
        else:
            return self._parent_group(cr, uid, parent_group.parent_id, context=context)

    def _find_group(self, cr, uid, group, context=None):
        """ Search a group or parent_group with any seance_ids
            until it finds the group.seance_ids or
            until it can't find any more parent(s)
        Input:      groups: browse object of training.group
        Returns:    parent_group: if find a parent_group with any seance_ids,
                    False: if not find any seance_ids
        """
        if context is None:
            context = {}
        if len(group.seance_ids) != 0:
            return group
        else:
            return self._parent_group(cr, uid, group.parent_id, context=context)
        return False
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}

        today = date.today()
        date_from = strToDate(vals['date_from'])
        date_to = strToDate(vals['date_to'])

        if date_to < date_from:
            raise osv.except_osv(_('User Error'), _('The end date is before to the start date!'))

        if date_from < today:
            raise osv.except_osv(_('User Error'), _('The start date is before today!'))

        # Check if there are any period line overlapping with another one
        weekdays_ids = self.search(cr, uid, [
            ('contact_id', '=', vals['contact_id']),
            '|', '|',
            '&', ('date_from', '>=', vals['date_from']),
            ('date_from', '<=', vals['date_to']),
            '&', ('date_to', '>=', vals['date_from']),
            ('date_to', '<=', vals['date_to']),
            '&', ('date_from', '<=', vals['date_from']),
            ('date_to', '>=', vals['date_to'])
        ])

        if len(weekdays_ids) > 0:
            raise osv.except_osv(_('User Error'), _('A weekdays line already exists with a period that overlaps with the current one!'))

        participation_obj = self.pool.get('training.participation')
        group_obj = self.pool.get('training.group')
        subscription_line_obj = self.pool.get('training.subscription.line')
        weekday_ids = self.search(cr, uid, [('contact_id', '=', vals['contact_id'])], context = context)
        contact = self.pool.get('res.partner.contact').browse(cr, uid, vals['contact_id'], context = context)
        group = self._find_group(cr, uid, contact.group_id, context = context)
        if not group:
            raise osv.except_osv(_('Error!'), _('The group %s or its parents haven\'t got any seance defined. You must choose another one.') % contact.group_id.name)
        kind = group.seance_ids[0].kind
        session = group.session_id
        subscription_line_ids = subscription_line_obj.search(cr, uid, [('session_id', '=', session.id), ('contact_id', '=', contact.id)], context = context)
        subscription_lines = subscription_line_obj.browse(cr, uid, subscription_line_ids, context = context)

        for subscription_line in subscription_lines:
            # Update expected_present to False/True in the participations of this contact depending on the day of the week
            participation_ids = participation_obj.search(cr, uid, [
                ('seance_id.kind', '=', kind),
                ('subscription_line_id', '=', subscription_line.id),
                ('seance_date', '>=', str(date_from) + ' 00:00:00'),
                ('seance_date', '<=', str(date_to) + ' 23:59:59')
            ])
            for participation in participation_obj.browse(cr, uid, participation_ids):
                weekday = strToDate(participation.seance_date).weekday()
                values = {
                    'expected_present' : vals[weekdays[weekday]],
                    'contact_id': contact.id,
                }
                participation_obj.write(cr, uid, [participation.id], values, context=context)
        return super(training_dining_hall_weekdays, self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        participations_generator_obj = self.pool.get('training.participation.generator')
        participation_obj = self.pool.get('training.participation')
        subscription_line_obj = self.pool.get('training.subscription.line')
        today = date.today()
        result = True

        for dh_weekdays in self.browse(cr, uid, ids, context):
            contact = dh_weekdays.contact_id
            group = self._find_group(cr, uid, contact.group_id, context = context)
            if not group:
                raise osv.except_osv(_('Error!'), _('The group %s or its parents haven\'t got any seance defined. You must choose another one.') % contact.group_id.name)
            kind = group.seance_ids[0].kind
            subscription_line_ids = subscription_line_obj.search(cr, uid, [('job_id.contact_id', '=', contact.id), ('kind', '=', kind)], context = context)
            for subscription_line_id in subscription_line_ids:
                date_from = strToDate(dh_weekdays.date_from)
                date_to = strToDate(dh_weekdays.date_to)
                if date_to < today:
                    raise osv.except_osv(_('User Error'), _('You cannot delete weekday lines before today.'))
                if date_from < today:
                    date_from = today
                    vals = {'date_to': today-relativedelta(days=1)}
                    result = super(training_dining_hall_weekdays, self).write(cr, uid, [dh_weekdays.contact_id.id], vals, context)
                    participation_ids = participation_obj.search(cr, uid, [
                        ('seance_id.kind', '=', kind),
                        ('subscription_line_id', '=', subscription_line_id),
                        ('subscription_line_id.job_id.contact_id', '=', contact.id),
#                        ('contact_id', '=', contact.id),
                        ('seance_date', '>=', str(date_from)+' 00:00:00'),
                        ('seance_date','<=', str(date_to)+' 23:59:59'),
#                        ('expected_present', '=', True),
                    ])
                    participation_obj.write(cr, uid, participation_ids, {'expected_present': False}, context)
                else:
                    participation_ids = participation_obj.search(cr, uid, [
                        ('seance_id.kind', '=', kind),
                        ('subscription_line_id', '=', subscription_line_id),
                        ('subscription_line_id.job_id.contact_id', '=', contact.id),
#                        ('contact_id', '=', contact.id),
                        ('seance_date', '>=', str(date_from) + ' 00:00:00'),
                        ('seance_date', '<=', str(date_to) + ' 23:59:59'),
#                        ('expected_present', '=', True),
                    ])
                    result = result and super(training_dining_hall_weekdays, self).unlink(cr, uid, ids, context)
                    participation_obj.write(cr, uid, participation_ids, {'expected_present': False}, context)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        participation_obj = self.pool.get('training.participation')
        subscription_line_obj = self.pool.get('training.subscription.line')
        today = date.today()
        date_from = strToDate(vals['date_from'])
        date_to = strToDate(vals['date_to'])
        result = True
        for dh_weekdays in self.browse(cr, uid, ids, context):
            contact = dh_weekdays.contact_id
            group = self._find_group(cr, uid, contact.group_id, context = context)
            if not group:
                raise osv.except_osv(_('Error!'), _('The group %s or its parents haven\'t got any seance defined. You must choose another one.') % contact.group_id.name)
            session = group.session_id
            kind = group.seance_ids[0].kind
            subscription_line_ids = subscription_line_obj.search(cr, uid, [('session_id', '=', session.id), ('contact_id', '=', contact.id)], context = context)
            if len(subscription_line_ids) == 0:
                raise osv.except_osv(_('Error!'), _('There aren\'t any subscription line for the contact %s %s in the session %s! Please, execute the Generate Participations wizard first.') % (contact.first_name, contact.name, session.name))
            subscription_lines = subscription_line_obj.browse(cr, uid, subscription_line_ids, context = context)
            for subscription_line in subscription_lines:
                if vals['date_to'] < vals['date_from']:
                    raise osv.except_osv(_('Error!'), _('The end date is prior to the start date!'))

                if strToDate(vals['date_to']) < today or strToDate(dh_weekdays.date_to) < today:
                    raise osv.except_osv(_('Error!'), _('You cannot modify weekday lines before today!'))

                if strToDate(dh_weekdays.date_from) < today and strToDate(dh_weekdays.date_from) != strToDate(vals['date_from']):
                    raise osv.except_osv(_('Error!'), _('You cannot modify the begining date of a weekday line when this is prior to today!'))

                # Check if there are any period line overlapping with another one
                dh_weekdays_ids = self.search(cr, uid, [
                    ('id', '!=', dh_weekdays.id),
                    ('contact_id', '=', contact.id),
                    '|', '|',
                    '&', ('date_from', '>=', vals['date_from']),
                    ('date_from', '<=', vals['date_to']),
                    '&', ('date_to', '>=', vals['date_from']),
                    ('date_to', '<=', vals['date_to']),
                    '&', ('date_from', '<=', vals['date_from']),
                    ('date_to', '>=', vals['date_to'])
                ])
                if len(dh_weekdays_ids) > 0:
                    repeated_field = self.browse(cr, uid, dh_weekdays_ids[0], context = context)
                    raise osv.except_osv(_('User Error'), _('A dh_weekdays line already exists with a period that overlaps with the current one!'))

                # Check if the actual period line is modified, save the old one with date_to = yesterday, and create new one from today with the new values.
                if strToDate(dh_weekdays.date_from) < today:
                    values = {
                        'date_from': dh_weekdays.date_from,
                        'date_to': str(today - relativedelta(days=1)),
                    }
                    result = result and super(training_dining_hall_weekdays, self).write(cr, uid, [dh_weekdays.id], values, context)
                    values = {
                        'contact_id': contact.id,
                        'date_from': str(today),
                        'date_to': vals['date_to'],
                        'sunday': vals['sunday'],
                        'monday': vals['monday'],
                        'tuesday': vals['tuesday'],
                        'wednesday': vals['wednesday'],
                        'thursday': vals['thursday'],
                        'friday': vals['friday'],
                        'saturday': vals['saturday'],
                    }
                    new_weekday = self.create(cr, uid, values, context = context)
                    if strToDate(vals['date_to']) < strToDate(dh_weekdays.date_to):
                        # Update expected_present to False in the participations with seance_date = [date_to+1, weekdays.date_to]
                        participation_ids = participation_obj.search(cr, uid, [
                            ('seance_id.kind', '=', kind),
                            ('subscription_line_id', '=', subscription_line.id),
                            ('seance_date', '>=', str(date_to + relativedelta(days=1)) + ' 00:00:00'),
                            ('seance_date', '<=', str(dh_weekdays.date_to) + ' 23:59:59'),
                        ])
                        result = result and participation_obj.write(cr, uid, participation_ids, {'expected_present': False}, context)
#                    date_from = today
                else:
                    if strToDate(vals['date_from']) > strToDate(dh_weekdays.date_from):
                        # Update expected_present to False in the participations with seance_date = [dh_weekdays.date_from, date_from-1]
                        participation_ids = participation_obj.search(cr, uid, [
                            ('seance_id.kind', '=', kind),
                            ('subscription_line_id', '=', subscription_line.id),
                            ('seance_date', '>=', str(dh_weekdays.date_from) + ' 00:00:00'),
                            #~ ('seance_date', '<', vals['date_from']),
                            ('seance_date', '<=', str(date_from-relativedelta(days=1)) + ' 23:59:59'),
                        ])
                        result = result and participation_obj.write(cr, uid, participation_ids, {'expected_present': False}, context)
                    if strToDate(vals['date_to']) < strToDate(dh_weekdays.date_to):
                        # Update expected_present to False in the participations with seance_date = [date_to+1, dh_weekdays.date_to]
                        participation_ids = participation_obj.search(cr, uid, [
                            ('seance_id.kind', '=', kind),
                            ('subscription_line_id' , '=', subscription_line.id),
                            ('seance_date', '>=', str(date_to+relativedelta(days=1)) + ' 00:00:00'),
                            ('seance_date', '<=', str(dh_weekdays.date_to) + ' 23:59:59'),
                        ])
                        result = result and participation_obj.write(cr, uid, participation_ids, {'expected_present': False}, context)
                    # Update expected_present to False/True in the participations of this contact depending on the day of the week
                    participation_ids = participation_obj.search(cr, uid, [
                        ('seance_id.kind', '=', kind),
                        ('subscription_line_id', '=', subscription_line.id),
                        ('seance_date', '>=', str(date_from) + ' 00:00:00'),
                        ('seance_date', '<=', str(date_to) + ' 23:59:59'),
                    ])
                    for participation in participation_obj.browse(cr, uid, participation_ids):
                        weekday = strToDate(participation.seance_date).weekday()
                        values = {
                            'expected_present' : vals[weekdays[weekday]]
                        }
                        result = result and participation_obj.write(cr, uid, [participation.id], values, context=context)
                    result = result and super(training_dining_hall_weekdays, self).write(cr, uid, [dh_weekdays.id], vals, context)
        return result

training_dining_hall_weekdays()


class res_partner_job(osv.osv):
    _name  =  "res.partner.job"
    _inherit = "res.partner.job"
    _columns  =  {
        'function': fields.char('Partner Function', size=64, translate=True, help="Function of this contact with this partner"),
    }
    
res_partner_job()


class res_partner_contact(osv.osv):
    _name = "res.partner.contact"
    _inherit = "res.partner.contact"

    _columns = {
        'menu_type_id': fields.many2one('training.dining_hall.menu_type', 'Menu Type', help='The menu type related with this contact.'),
        'picnic': fields.boolean('Picnic', help="If checked, the contact menu when go out for an excursion is payed as a picnic."),
        'weekdays_ids': fields.one2many('training.dining_hall.weekdays','contact_id', 'Weekdays'),
        'group_id': fields.many2one('training.group', 'Group', help='The group that owns this contact.'),
    }

res_partner_contact()


class training_session(osv.osv):
    _name = 'training.session'
    _inherit = 'training.session'

    def dining_hall_create_seances (self, cr, uid, ids, context=None):
        """Creates one seance for each day between the start date and end date of the session
            (the holidays of the school calendar will be excluded)."""
        if not context:
            context = {}
        seance_obj = self.pool.get('training.seance')
        holiday_year_obj = self.pool.get('training.holiday.year')
        holiday_period_obj = self.pool.get('training.holiday.period')
        for session in self.browse(cr, uid, ids, context = context):
            school = session.school_id.id
            course_id = session.offer_id.course_ids and session.offer_id.course_ids[0].course_id.id or False
            duration = session.offer_id.course_ids and session.offer_id.course_ids[0].course_id.duration or 0.0
            if not session.date_end:
                raise osv.except_osv(_('User Error'),
                     _('In order to create seances, you must first enter a session end date for the %s school.') % session.school_id.name)
            date = date2 = datetime.strptime(session.date, '%Y-%m-%d %H:%M:%S')
            date_end = datetime.strptime(session.date_end, '%Y-%m-%d %H:%M:%S')
            if date_end < date:
                raise osv.except_osv(_('User Error'),
                     _('The session end date is before to the start date for the %s school.') % session.school_id.name)
            calendars = {}
            while date2 <= date_end+relativedelta(years=1):
                holiday_year_ids = holiday_year_obj.search(cr, uid, [('school_id','=',school),('year','=',int(date2.year))])
                if len(holiday_year_ids) == 0:
                    raise osv.except_osv(_('User Error'),
                     _('In order to create seances, you must create the %s holiday year for the %s school first.') % (date2.year, session.school_id.name))
                calendars[date2.year] = holiday_year_ids[0]
                date2 += relativedelta(years=1)

            while date <= date_end:
                holiday_period_ids = holiday_period_obj.search(cr, uid, [('year_id','=', calendars[date.year]),('date_start','<=',date),('date_stop','>=',date)])
                if not len(holiday_period_ids):
                    for group_id in session.group_ids:
                        if group_id.generate_seances:
                            already_exist = seance_obj.search(cr, uid, [('group_id','=',group_id.id),('date','=',str(date)),('school_id','=',session.school_id.id)])
                            if not already_exist:
                                values =  {
                                    'name': str(date.year) + '-' + str(date.month) + '-' + str(date.day),
                                    'session_ids': [(6,0,[session.id])],
                                    'group_id': group_id.id,
                                    'kind': session.kind,
                                    'school_id': session.school_id.id,
                                    'date': date,
                                    'course_id': course_id,
                                    'duration': duration,
                                }
                                seance_obj.create(cr, uid, values, context = context)
                date += relativedelta(days=1)
        return True
            
training_session()


class training_seance(osv.osv):
    _inherit = 'training.seance'

    # training.seance
    def _create_participation(self, cr, uid, seance, subscription_line, context=None):
        if context == None:
            context = {}
        weekdays_obj = self.pool.get('training.dining_hall.weekdays')
        participation_obj = self.pool.get('training.participation')
        part_id = super(training_seance, self)._create_participation(cr, uid, seance, subscription_line, context=context)
        part = participation_obj.browse(cr, uid, part_id, context=context)

        if part.subscription_line_id:
            if part.subscription_line_id.job_id:
                if part.subscription_line_id.job_id.contact_id:
                    weekdays_ids = weekdays_obj.search(cr ,uid, [
                        ('contact_id','=',part.subscription_line_id.job_id.contact_id.id),
                        ('date_from','<=',part.seance_date),
                        ('date_to','>=',part.seance_date)
                    ], context=context)
                    if weekdays_ids:
                        dining_hall_weekdays = weekdays_obj.read(cr, uid, weekdays_ids, [
                            'sunday','monday','tuesday','wednesday','thursday','friday','saturday'
                        ], context=context)[0]
                        weekday = strToDate(part.seance_date).weekday()
                        participation_obj.write(cr, uid, [part_id], {'expected_present' : dining_hall_weekdays[weekdays[weekday]]}, context=context)
                else:
                    raise osv.except_osv(_('Error!'),
                        _("The contact for the job %s not correctly defined!") % part.subscription_line_id.job_id.name)
            else:
                raise osv.except_osv(_('Error!'),
                    _("The job for the subscription line %s not correctly defined!") % part.subscription_line_id.name)
        else:
            raise osv.except_osv(_('Error!'),
                _("The subscription line for the participation not correctly defined!"))
        return part_id

training_seance()


class training_participation(osv.osv):
    _name = 'training.participation'
    _inherit = 'training.participation'
    
    _columns = {
        'expected_present':fields.boolean('Expected Present'),
    }

training_participation()
