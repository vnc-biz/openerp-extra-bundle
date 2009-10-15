##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

# openacademy/wizard/wizard_spam.py

import wizard
import pooler
import tools

class wizard_not_implemented(wizard.interface):

    first_screen_fields = { }

    first_screen_form = '''<?xml version="1.0"?>
    <form string="Not Implemented" colspan="4">
        <label string="This wizard is not implented !" />
    </form>'''

    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': first_screen_form,
                'fields': first_screen_fields,
                'state':[('end','Ok', 'gtk-close')],
            }
        },
    }


wizard_not_implemented('wizard_not_implemented')
