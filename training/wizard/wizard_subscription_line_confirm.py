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
import netsvc
import ir
import pooler

confirm_form = """<?xml version="1.0"?>
<form string="Confirm Subscription Lines">
    <label string="Do you want to confirm all subscription lines ?" />
</form>
"""

confirm_fields = {
}

def _confirm(self, cr, uid, data, context):
    wf_service = netsvc.LocalService("workflow")

    for obj_id in data['ids']:
        wf_service.trg_validate(uid, 'training.subscription.line', obj_id, 'signal_confirm', cr)

    return {}

class line_confirm_them(wizard.interface):
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

line_confirm_them("training.subscription.line.confirm")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

