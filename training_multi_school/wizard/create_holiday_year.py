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
from tools.translate import _

import time
import mx.DateTime

class training_calendar_school_year(osv.osv_memory):
    _name = 'training.calendar.school.year'

    _columns = {
        'year_id': fields.many2one('training.holiday.year', 'Calendar School Year', help = 'Base calendar school year to duplicate or update.'),
        'school_ids': fields.many2many('training.school', 'calendar_school_year_rel', 'school_id', 'year_id', 'School', help = 'The schools that will be create or update theirs calendars.'),
    }

    def _check_date(self, cr, uid, ids, context=None):
        return self.browse(cr, uid, ids[0], context=context).year_id.year >= int(time.strftime('%Y'))

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def action_apply(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        holiday_year_obj = self.pool.get('training.holiday.year')
        holiday_period_obj = self.pool.get('training.holiday.period')
        year_ids = []
        this = self.browse(cr, uid, ids[0], context=context)
        for school in this.school_ids:
            values = []
            year_values = {
                'year': this.year_id.year,
                'school_id': school.id,
            }
            year_id = holiday_year_obj.search(cr, uid, [('year','=',year_values['year']),('school_id','=',year_values['school_id'])], context=context)
            year_id = year_id and year_id[0] or False
            if not year_id:
                year_id = holiday_year_obj.create(cr, uid, year_values, context=context)
            year_ids.append(year_id)
            for period in this.year_id.period_ids:
                period_values = {
                    'year_id': year_id,
                    'name': period.name,
                    'date_start': period.date_start,
                    'date_stop': period.date_stop,
                    'active': period.active,
                    'contact_id': period.contact_id.id,
                }
                holiday_period_id = holiday_period_obj.search(cr, uid, [('year_id','=',period_values['year_id']),('name','=',period_values['name'])], context=context)
                if not len(holiday_period_id):
                    holiday_period_id = holiday_period_obj.create(cr, uid, period_values, context=context)
                else:
                    holiday_period_obj.write(cr, uid, holiday_period_id, period_values, context=context)

        return {
            'view_type': 'form',
            "view_mode": 'tree,form',
            'res_model': 'training.holiday.year',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain' : "[('id', 'in', [%s])]" % ','.join(map(str, year_ids)),
        }

    _constraints = [
        (_check_date, "Can you check the year, it's before than current year.", ['year']),
    ]

training_calendar_school_year()

