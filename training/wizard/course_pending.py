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

#from addons.training.training import training_course_pending_reason_compute

import netsvc

def training_course_pending_reason_compute(obj, cr, uid, context=None):
    proxy = obj.pool.get('training.course.pending.reason')
    return [(reason.code, reason.name) for reason in proxy.browse(cr, uid, proxy.search(cr, uid, []))] or []


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
