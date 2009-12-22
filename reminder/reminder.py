#!/usr/bin/env python
#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
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

from osv import osv
from osv import fields

class reminder_reminder(osv.osv):
    '''
    Reminder
    '''
    _name = 'reminder.reminder'
    _description = 'Reminder'
    
    _columns = {
        'name':fields.char('Name', size=256, required=True, readonly=False),
        'model_id':fields.many2one('ir.model', 'Model', required=True),
        'field_id':fields.many2one('ir.model.fields', 'Field Name', required=False),
        'domain':fields.char('Domain', size=1024, required=False, readonly=False),
        'start_date': fields.datetime('Start Date', required=True),
        'end_date': fields.date('End Date'),
        'action_id':fields.many2one('ir.actions.server', 'Action', required=True),
        'note': fields.text('Description'),
        'match':fields.selection([
            ('one','Any One'),
            ('all','All'),
            ('maxone','Maximim Priority One'),
        ],'Match', select=True, readonly=False, required=True),
        'line_ids':fields.one2many('reminder.reminder.line', 'reminder_id', 'Conditions', required=False),
        'state':fields.selection([
            ('draft','Stop'),
            ('done','Running'),
        ],'State', select=True, readonly=True),
        'running':fields.selection([
            ('hour','Hourly'),
            ('day','Daily'),
            ('month','Monthly'),
        ],'Execute Mode', select=True, readonly=False),
        'process_id': fields.many2one('ir.cron', 'MTA Process', readonly=True, help="Process"),
    }
    _defaults = {
        'domain': lambda *a: "[]",
        'state': lambda *a: "draft",
        'running': lambda *a: "hour",
    }
    
    def _call(self, cr, uid, ids, context={}):
        return True
    
reminder_reminder()

class reminder_reminder(osv.osv):
    '''
    Reminder
    '''
    _name = 'reminder.reminder.line'
    _description = 'Reminder Conditions'
    
    _columns = {
        'reminder_id':fields.many2one('reminder.reminder', 'Model', required=False),
        'field_id':fields.many2one('ir.model.fields', 'Field Name', required=False),
        'operator':fields.selection([
            ('eq','Equal'),
            ('neq','Not Equal'),
            ('in','In'),
            ('gt','Grater than'),
            ('lt','Less than'),
            ('gt','Grater than Equal'),
            ('lt','Less than Equal'),
        ],'Operator', select=True, readonly=False),
        'name':fields.char('Condition', size=256, required=True, readonly=False),
        'sequence': fields.integer('Sequence'),
    }
    
reminder_reminder()
