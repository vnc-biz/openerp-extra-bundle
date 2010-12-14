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

invoice_form = """<?xml version="1.0"?>
<form string="Create invoices">
    <separator colspan="4" string="Do you really want to create the invoices ?" />
</form>
"""

invoice_fields = {
}

def _makeInvoices(self, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)

    ids = pool.get('training.subscription.line').action_create_invoice(cr, uid, data['ids'], context=context)

    len_ids = len(ids)

    if not len_ids:
        return {}
    
    def get_view(name):
        ima = pool.get('ir.model.data')
        imaid = ima._get_id(cr, uid, 'training', name)
        if not imaid:
            return False
        return ima.read(cr, uid, [imaid], ['res_id'])[0]['res_id']

    if len_ids == 1:
        return {
            'res_id' : int(ids[0]),
            'name' : 'Invoice',
            'view_type' : 'form',
            'view_mode' : 'form,tree',
            'res_model' : 'account.invoice',
            'views': [(get_view('invoice_form'), 'form'), (get_view('invoice_list'), 'tree')],
            'type' : 'ir.actions.act_window',
        }
    else:
        return {
            'domain' : "[('id', 'in', [%s])]" % ','.join(map(str,ids)),
            'name' : 'Invoices',
            'view_type' : 'form',
            'view_mode' : 'tree,form',
            'res_model' : 'account.invoice',
            'views': [(get_view('invoice_list'), 'tree'), (get_view('invoice_form'), 'form')],
            'type' : 'ir.actions.act_window',
        }


class line_make_invoice(wizard.interface):
    states = {
        'init' : {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': invoice_form,
                'fields': invoice_fields,
                'state': [
                    ('end', 'Cancel'),
                    ('invoice', 'Create Invoices')
                ]
            }
        },
        'invoice' : {
            'result' : {
                'type' : 'action',
                'action' : _makeInvoices,
                'state' : 'end',
            }
        }
    }

line_make_invoice("training.subscription.line.make_invoice")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

