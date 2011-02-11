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
import pooler
import time
import locale
from tools.translate import _

class make_invoice(wizard.interface):
    invoice_form = """<?xml version="1.0"?>
    <form string="Create invoices">
        <separator colspan="4" string="Select product do you create invoice lines:" />
        <field name="product_id" />
        <field name="price" />
        <field name="account_id" />
    </form>
    """

    invoice_fields = {
        'product_id': {
            'string': 'Product',
            'type': 'many2one',
            'relation': 'product.product',
            'required': True
        },
        'price': {
            'string': 'Price',
            'type': 'float',
        },
        'account_id': {
            'string': 'Analytic Account',
            'type': 'many2one',
            'relation': 'account.analytic.account',
        },
    }

    def _makeInvoices(self, cr, uid, data, context):
        renewal_obj = pooler.get_pool(cr.dbname).get('internetdomain.renewal')
        product_obj = pooler.get_pool(cr.dbname).get('product.product')
        account_payment_term_obj = pooler.get_pool(cr.dbname).get('account.payment.term')

        renewals = renewal_obj.browse(cr, uid, data['ids'])
        product = product_obj.browse(cr, uid, data['form']['product_id'])

        for renewal in renewals:
            partner = renewal.domain_id.partner_id.id

            pool = pooler.get_pool(cr.dbname)
            analytic_account_obj = pool.get('account.analytic.account')
            res_partner_obj = pool.get('res.partner')
            account_payment_term_obj = pool.get('account.payment.term')
            lang_obj = pool.get('res.lang')

            invoices = []

            date_due = ""
            if renewal.domain_id.partner_id.property_payment_term:
                pterm_list= account_payment_term_obj.compute(cr, uid,
                    renewal.domain_id.partner_id.property_payment_term.id, value=1,
                    date_ref=time.strftime('%Y-%m-%d'))
                if pterm_list:
                    pterm_list = [line[0] for line in pterm_list]
                    pterm_list.sort()
                    date_due = pterm_list[-1]
                    print "Aquí está el date_due: " + date_due

            curr_invoice = {
                'name': renewal.domain_id.name+' ('+renewal.date_renewal+' / '+renewal.date_expire+')',
                'partner_id': renewal.domain_id.partner_id.id,
                'date_due': date_due,
            }
            values = pool.get('account.invoice').onchange_partner_id(cr, uid, [], 'out_invoice', renewal.domain_id.partner_id.id)
            curr_invoice.update(values['value'])

            last_invoice = pool.get('account.invoice').create(cr, uid, curr_invoice)
            invoices.append(last_invoice)

            taxes = product.taxes_id
            tax = pool.get('account.fiscal.position').map_tax(cr, uid, renewal.domain_id.partner_id.property_account_position, taxes)
            account_id = product.product_tmpl_id.property_account_income.id or product.categ_id.property_account_income_categ.id

            curr_line = {
                'price_unit': data['form']['price'] or product.lst_price,
                'quantity': 1,
                'invoice_line_tax_id': [(6,0,tax)],
                'invoice_id': last_invoice,
                'name': product.name,
                'product_id': product.id,
                'uos_id': product.uom_id.id,
                'account_id': account_id,
                'account_analytic_id': data['form']['account_id'],
            }

            pool.get('account.invoice.line').create(cr, uid, curr_line)

        mod_obj = pooler.get_pool(cr.dbname).get('ir.model.data')
        act_obj = pooler.get_pool(cr.dbname).get('ir.actions.act_window')
            
        mod_id = mod_obj.search(cr, uid, [('name', '=', 'action_invoice_tree1')])[0]
        res_id = mod_obj.read(cr, uid, mod_id, ['res_id'])['res_id']
        act_win = act_obj.read(cr, uid, res_id, [])
        act_win['domain'] = [('id','in',invoices),('type','=','out_invoice')]
        act_win['name'] = _('Invoices')
        return act_win

    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : invoice_form,
                    'fields' : invoice_fields,
                    'state' : [('end', 'Cancel'),('invoice', 'Create invoices') ]}
        },
        'invoice' : {
            'actions' : [],
            'result' : {'type' : 'action',
                    'action' : _makeInvoices,
                    'state' : 'end'}
        },
    }
make_invoice("internetdomain.renewal.make_invoice")
