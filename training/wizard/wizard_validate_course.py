# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

import wizard
import pooler
import tools
import netsvc

class wizard_validate_courses(wizard.interface):
    first_screen_fields = {
    }

    first_screen_form = '''<?xml version="1.0"?>
    <form string="Create Offers" colspan="6">
        <label string="Do you want to validate the selected courses ?" />
    </form>'''

    def validate_courses(self, cr, uid, data, context=None):
        workflow = netsvc.LocalService('workflow')
        pool = pooler.get_pool(cr.dbname)
        proxy = pool.get('training.course')
        for course in proxy.browse(cr, uid, data['ids'], context=context):
            if course.state_course in ('pending','draft'):
                workflow.trg_validate(uid, 'training.course', course.id, 'signal_validate', cr)

        return {}

    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': first_screen_form,
                'fields': first_screen_fields,
                'state':[('end','Cancel', 'gtk-cancel'),('validate_courses', 'Validate Courses', 'gtk-apply')],
            }
        },
        'validate_courses' : {
            'result' : {
                'type' : 'action',
                'action' : validate_courses,
                'state' : 'end',
            }
        }
    }

wizard_validate_courses('training.course.validate')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
