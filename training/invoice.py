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

import tools
import netsvc
import tempfile
import os
import time

class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    _columns = {
        'send_to': fields.char('Email', size=128),
        'sent_by_mail': fields.boolean('Sent By Mail', readonly=True, select=2),
        'sent_by_mail_at': fields.datetime('Sent At', readonly=True),
        'send_manually': fields.boolean('Send Manually', helps='Activate this field to indicated that the invoice will be send manually, i.e. not automatically by cron'),
        'invoice_line': fields.one2many('account.invoice.line', 'invoice_id', 'Invoice Lines', readonly=True, states={'draft':[('readonly',False)]}, select=1),
    }

    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        values = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id,
                                                                   date_invoice,
                                                                   payment_term,
                                                                   partner_bank_id,
                                                                   company_id)

        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)

            invoice_email = False
            default_email = False

            for address in partner.address:
                if address.type == 'default' and address.email:
                    default_email = address.email
                if address.type == 'invoice' and address.email:
                    invoice_email = address.email

            if invoice_email or default_email:
                values.setdefault('value', {})['send_to'] = invoice_email and invoice_email or default_email
        else:
            values.setdefault('value', {})['send_to'] = False

        return values

    def action_workflow_send_email(self, cr, uid, ids, context=None):
        srv = netsvc.LocalService('report.account.invoice')
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.send_to and invoice.type == 'out_invoice':
                pdf, _ = srv.create(cr, uid, [invoice.id], {}, context=context)
                if pdf:
                    filename = "Invoice_%s.pdf" % (invoice.name.replace('/', '_'))
                    sent = self.pool.get('training.email').send_email(cr, uid, 'invoice', 'a', to=invoice.send_to, attachments=[(filename, pdf),], context=context, invoice=invoice)
                    invoice.write({'sent_by_mail': sent,
                                   'sent_by_mail_at': time.strftime('%Y-%m-%d %H%M%S'),
                                  }, context=context)
        return True

account_invoice()


class purchase_order_analytic_distribution(osv.osv):
    _inherit = 'purchase.order'
    
    def inv_line_create(self, cr, uid, a, ol):
        proxy_journal = self.pool.get('account.journal')
        proxy_adist = self.pool.get('account.analytic.plan.instance')
        proxy_adistline = self.pool.get('account.analytic.plan.instance.line')

        # Look for purchase journal, and corresponding analytic journal
        a_journal_id = ''
        journal_list = proxy_journal.search(cr, uid, [('type','=','purchase'),('refund_journal','=',False)])
        if journal_list:
            a_journal_id = proxy_journal.read(cr, uid, [ journal_list[0] ], ['analytic_journal_id'])[0]['analytic_journal_id'][0]

        # Look for fiscal position
        fpos_obj = self.pool.get('account.fiscal.position')
        fpos = ol.order_id.fiscal_position or False

        # Create analytic distribution instance, and it's distribution line!
        adist_id = proxy_adist.create(cr, uid, {
            'journal_id': a_journal_id,
        })
        if ol.account_analytic_id:
            adistline_id = proxy_adistline.create(cr, uid, {
                'plan_id': adist_id,
                'analytic_account_id': ol.account_analytic_id.id,
                'rate': 100.0,
            })
        else:
            adistline_id = ''
        
        return (0, False, {
            'name': ol.name,
            'account_id': a,
            'price_unit': ol.price_unit or 0.0,
            'quantity': ol.product_qty,
            'product_id': ol.product_id.id or False,
            'uos_id': ol.product_uom.id or False,
            'invoice_line_tax_id': [(6, 0, fpos_obj.map_tax(cr, uid, fpos, ol.taxes_id))],
#            'account_analytic_id': ol.account_analytic_id.id,
            'analytics_id': adist_id or '',  # Analytic Distribution
        })
purchase_order_analytic_distribution()
