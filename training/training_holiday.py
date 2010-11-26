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

class holiday_year(osv.osv):
    _name = 'training.holiday.year'

    _rec_name = 'year'

    _columns = {
        'year' : fields.integer('Year', select=1, required=True),

        'period_ids' : fields.one2many('training.holiday.period',
                                       'year_id',
                                       'Holiday Periods',
                                      ),
    }

    _defaults = {
        'year' : lambda *a: int(time.strftime('%Y')),
    }

    _sql_constraints = [
        ('uniq_year', 'unique(year)', 'The year must be unique !'),
    ]

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
        return self.name_get(cr, uid,
                             self.search(cr, uid,
                                         [('year', '=', name)]+args,
                                         limit=limit),
                             context=context)


holiday_year()

class holiday_period(osv.osv):
    _name = 'training.holiday.period'

    _columns = {
        'year_id' : fields.many2one('training.holiday.year',
                                    'Year',
                                    required=True,
                                    select=1,
                                    ondelete='cascade'),

        'name' : fields.char('Name', size=64, required=True),
        'date_start' : fields.date('Date Start', required=True, select=1),
        'date_stop' : fields.date('Date Stop', required=True, select=1),
        'active' : fields.boolean('Active'),
        'contact_id' : fields.many2one('res.partner.contact', 'Contact'),
    }

    _defaults = {
        'active' : lambda *a: 1,
        'date_start' : lambda *a: time.strftime('%Y-%m-%d'),
        'date_stop' : lambda *a: time.strftime('%Y-%m-%d'),
    }

    def _check_date_start_stop(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        return obj.date_start <= obj.date_stop


    def is_in_period(self, cr, date):
        if not date:
            raise osv.except_osv(_('Warning'),
                                 _('Can you give a right date ?'))

        cr.execute("SELECT id "
                   "FROM training_holiday_period "
                   "WHERE %s BETWEEN date_start AND date_stop AND active='1'",
                   (date,))
        return len([x[0] for x in cr.fetchall()]) != 0

    _constraints = [
        (_check_date_start_stop, "Please, check the start date !", ['date_start', 'date_stop']),
    ]

holiday_period()

class holiday_year_wizard(osv.osv):
    _name = 'training.holiday.year.wizard'

    _columns = {
        'year' : fields.integer('Year', required=True),
    }

    _defaults = {
        'year' : lambda *a: int(time.strftime('%Y')),
    }

    def _check_date(self, cr, uid, ids, context=None):
        return self.browse(cr, uid, ids[0], context=context).year >= int(time.strftime('%Y'))

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def action_apply(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)

        first_day = mx.DateTime.strptime('%04s-01-01' % (this.year,), '%Y-%m-%d')
        last_day = mx.DateTime.strptime('%04s-12-31' % (this.year,), '%Y-%m-%d')

        tmp_day = first_day

        proxy = self.pool.get('training.holiday.year')
        year_id = proxy.create(cr, uid, {'year' : this.year}, context=context)

        proxy = self.pool.get('training.holiday.period')

        counter = 1
        while tmp_day <= last_day:
            tmp_day = tmp_day + mx.DateTime.RelativeDate(days=1)

            if tmp_day.day_of_week == mx.DateTime.Saturday:
                saturday = tmp_day.strftime('%Y-%m-%d')
                tmp_day = tmp_day + mx.DateTime.RelativeDate(days=1)
                sunday = tmp_day.strftime('%Y-%m-%d')

                proxy.create(cr, uid, {
                    'year_id' : year_id,
                    'date_start' : saturday,
                    'date_stop' : sunday,
                    'name' : 'Week-End %02d' % (counter,)
                }, context=context),

                counter = counter + 1

            else:
                continue

        return {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'training.holiday.year',
            'view_id':self.pool.get('ir.ui.view').search(cr,uid,[('name','=','training.holiday.year.form')]),
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id' : year_id,
        }

    _constraints = [
        (_check_date, "Can you check the year", ['year']),
    ]

holiday_year_wizard()

