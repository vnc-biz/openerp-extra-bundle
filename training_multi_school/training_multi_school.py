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


class training_school(osv.osv):
    _name = 'training.school'
    _description = 'Manage Training Multi Schools'

training_school()


class res_users(osv.osv):
    _name  =  "res.users"
    _inherit  =  "res.users"
    _columns  =  {
        'school_id': fields.many2one('training.school','School', help = 'The school related to the current user'),
    }

res_users()


class holiday_year(osv.osv):
    _name = 'training.holiday.year'
    _inherit = 'training.holiday.year'

    _columns = {
        'school_id': fields.many2one('training.school', 'School', help = 'The school related to this holiday period'),
    }

    _sql_constraints = [
        ('uniq_year', 'unique(year, school_id)', 'The year for the school must be unique!'),
    ]

holiday_year()


class training_session(osv.osv):
    _name = 'training.session'
    _inherit = 'training.session'

    _columns = {
        'school_id': fields.many2one('training.school', 'School', help = 'The school belongs to this session.'),
    }

training_session()


class training_group(osv.osv):
    _name = 'training.group'
    _inherit = 'training.group'

    _columns = {
#        'school_id': fields.many2one('training.school', 'School', help = 'The school belongs to this session.'),
        'school_id': fields.related('session_id','school_id', type='many2one', readonly=True, size=30, store=True, relation='training.school', string='School'),
    }

training_group()


class training_seance(osv.osv):
    _name = 'training.seance'
    _inherit = 'training.seance'

    _columns = {
        'school_id': fields.related('group_id','session_id','school_id', type='many2one', readonly=True, size=30, store=True, relation='training.school', string='School'),
    }

training_seance()


class training_school(osv.osv):
    _name = 'training.school'

    _columns = {
        'name': fields.char('Name', size = 30, required = True, select = 1),
        'partner_id': fields.many2one('res.partner', 'Partner', required = True, select = 1, help = 'Partner that is related to the current school.'),
        'user_ids': fields.one2many('res.users', 'school_id', 'Users', help = 'Users of this school.'),
        'holiday_ids': fields.one2many('training.holiday.year', 'school_id', string = 'Calendars', help = 'Calendars of this school.'),
        'session_ids': fields.one2many('training.session', 'school_id', string = 'Sessions', help = 'Sessions of this school.'),
        'group_ids': fields.one2many('training.group', 'school_id', string = 'Groups', help = 'Groups of this school.'),
    }

training_school()
