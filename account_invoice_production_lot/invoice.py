# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Domsense s.r.l. (<http://www.domsense.com>).
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

from osv import fields,osv
from tools.translate import _

class account_invoice_line(osv.osv):

    def _get_prod_lots(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = []
            for order_line in line.order_lines:
                for move in order_line.move_ids:
                    if move.prodlot_id:
                        result[line.id].append(move.prodlot_id.id)
        return result

    _inherit = "account.invoice.line"

    _columns = {
        'order_lines': fields.many2many('sale.order.line', 'sale_order_line_invoice_rel', 'invoice_id', 'order_line_id', 'Order Lines', readonly=True),
        'prod_lot_ids': fields.function(_get_prod_lots, method=True, type='many2many', relation="stock.production.lot", string="Production Lots"),
        'displayed_lot_id': fields.many2one('stock.production.lot', 'Lot'),
        }

account_invoice_line()

class account_invoice(osv.osv):
     
    def load_lines_lots(self, cr, uid, ids, context):
        invoices = self.browse(cr, uid, ids, context)
        line_obj = self.pool.get('account.invoice.line')
        for invoice in invoices:
            line_list = []
            for line in invoice.abstract_line_ids:
                if not line.displayed_lot_id:
                    line_list.append((line.id, line.sequence))
                else:
                    line_obj.unlink(cr, uid, line.id)
            sorted_line_list = sorted(line_list, key=lambda inv_line: inv_line[1])
            counter = 0
            for line_tuple in sorted_line_list:
                counter += 1
                line = line_obj.browse(cr, uid, line_tuple[0])
                line_obj.write(cr, uid, line.id, {'sequence': counter * 10})
                added_lots = []
                for lot in line.prod_lot_ids:
                    if lot.id not in added_lots:
                        line_obj.create(cr, uid, {
                            'sequence': counter * 10 + 1,
                            'name': '> (' + _('lot') + ') ' + lot.name,
                            'state': 'text',
                            'displayed_lot_id': lot.id,
                            'invoice_id': line.invoice_id.id,
                            })
                        added_lots.append(lot.id)
        return True

    _inherit = "account.invoice"

account_invoice()

