# -*- encoding: utf-8 -*-
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

import wizard
import netsvc
import ir
import pooler

confirm_form = """<?xml version="1.0"?>
<form string="Assign to a new course">
    <field name="course_id" />
</form>
"""

confirm_fields = {
    'course_id' : {
        'type' : 'many2one',
        'relation' : 'training.course',
        'domain' : "[('state_course', '=', 'validated')]",
        'string' : 'Course',
        'required' : True,
    }
}

def _confirm(self, cr, uid, data, context):

    proxy = pooler.get_pool(cr.dbname).get('training.exam.question')
    for question in proxy.browse(cr, uid, data['ids'], context=context):
        # Assign the course to the question
        course_ids = set([data['form']['course_id']] + [course.id for course in question.course_ids])

        question.write({'course_ids' : [(6, 0, list(course_ids))]})

    return {}

class training_exam_question_assign_course(wizard.interface):
    states = {
        'init' : {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': confirm_form,
                'fields': confirm_fields,
                'state': [
                    ('end', 'Cancel', 'gtk-cancel'),
                    ('confirm', 'Confirm', 'gtk-apply')
                ]
            }
        },
        'confirm' : {
            'actions' : [_confirm],
            'result' : {'type': 'state', 'state': 'end'}
        },
    }

training_exam_question_assign_course("training.exam.question.assign.course")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

