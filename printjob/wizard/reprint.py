# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Ferran Pegueroles <ferran@pegueroles.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
#
# Reprint
#
import os, base64
import time
import wizard
import pooler 
from tempfile import mkstemp

print_form = '''<?xml version="1.0"?>
<form string="Printing">
    <field name="printer" />
</form>'''
print_fields = {
    'printer' : {'string':'Printer', 'type':'many2one', 'relation':'printjob.printer','required':True},
}

class wizard_reprint(wizard.interface):

    def _get_default_printer(self, cr, uid, data, context):

        pool = pooler.get_pool(cr.dbname)
        printer_ids = pool.get('printjob.printer').search(cr, uid,[('is_default','=',True)])
        if printer_ids:
           data['form']['printer'] = printer_ids[0]
        return data['form']

    def _print(self, cr, uid, data, context):
        pool= pooler.get_pool(cr.dbname)
        printer_obj = pool.get('printjob.printer')
        printer_reg = printer_obj.read(cr, uid, [data['form']['printer']])[0]
        job_obj = pool.get('printjob.job')
        job_reg = job_obj.read(cr, uid, data['ids'])[0]
        tmpfile=mkstemp()
        os.write(tmpfile[0],base64.decodestring(job_reg['result']))
        os.system("lpr -P %s %s" % (printer_reg['system_name'],tmpfile[1]))
        return {}

    states = {
        'init': {
            'actions': [_get_default_printer],
            'result': {'type':'form', 'arch':print_form, 'fields':print_fields, 'state':[('end','Cancelar'),('print','Imprimir')]}
        },
        'print': {
            'actions': [_print],
            'result': {'type':'state', 'state':'end'}
        }
    }

wizard_reprint('printjob.job.reprint')

class wizard_preview(wizard.interface):

    def _get_id(self, cr, uid, data, context):
        
        data['form']['ids'] = [ data['id'] ]
        return data['form']

    states = {
        'init': {
            'actions': [_get_id],
            'result': {'type':'print', 'report':'printjob.reprint', 'get_id_from_action':True ,'state':'end'}
        }
    }

wizard_preview('printjob.job.preview')
