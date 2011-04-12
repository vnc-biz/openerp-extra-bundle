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

from osv import fields
from osv import osv
import time
import netsvc

import ir
from mx import DateTime
import pooler

class purchase_order_line(osv.osv):
    _name = "purchase.order.line"
    _inherit = "purchase.order.line"

    def _amount_line(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        res = {}
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, line.price_unit * line.product_qty * (1 - (line.discount or 0.0) /100.0))
        return res

    _columns = {
        'discount': fields.float('Discount (%)', digits=(16,2)),
        'price_subtotal': fields.function(_amount_line, method=True, string='Subtotal'),
    }
    _defaults = {
        'discount': lambda *a: 0.0,
    }
purchase_order_line()

class purchase_order(osv.osv):
    _name = "purchase.order"
    _inherit = "purchase.order"
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context):
        res = {}
        cur_obj = self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                for c in self.pool.get('account.tax').compute(cr, uid, line.taxes_id, line.price_unit * (1-(line.discount or 0.0)/100.0), line.product_qty, order.partner_address_id.id, line.product_id, order.partner_id):
                    val += c['amount']
                val1 += line.price_subtotal
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res
    
    def inv_line_create(self, cr, uid, a, ol):
        return (0, False, {
            'name': ol.name,
            'account_id': a,
            'price_unit': ol.price_unit or 0.0,
            'quantity': ol.product_qty,
            'product_id': ol.product_id.id or False,
            'uos_id': ol.product_uom.id or False,
            'discount': ol.discount or 0.0,
            'invoice_line_tax_id': [(6, 0, [x.id for x in ol.taxes_id])],
            'account_analytic_id': ol.account_analytic_id.id or False,
        })

purchase_order()


class stock_picking( osv.osv ):
    _inherit =  'stock.picking'

    def _invoice_line_hook(self, cr, uid, move_line, invoice_line_id):
        if move_line.purchase_line_id:
            self.pool.get('account.invoice.line').write( cr, uid, [invoice_line_id], {        
                'discount':move_line.purchase_line_id.discount, 
                } )
        return super( stock_picking, self)._invoice_line_hook( cr, uid, move_line,invoice_line_id )

stock_picking()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

