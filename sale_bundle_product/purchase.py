# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
#    sale_bundle_product for OpenERP                                            #
#    Copyright (C) 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>   #
#                                                                               #
#    This program is free software: you can redistribute it and/or modify       #
#    it under the terms of the GNU Affero General Public License as             #
#    published by the Free Software Foundation, either version 3 of the         #
#    License, or (at your option) any later version.                            #
#                                                                               #
#    This program is distributed in the hope that it will be useful,            #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              #
#    GNU Affero General Public License for more details.                        #
#                                                                               #
#    You should have received a copy of the GNU Affero General Public License   #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                               #
#################################################################################

from osv import osv, fields
import netsvc


class purchase_order_line(osv.osv):
    
    _inherit = "purchase.order.line"
    

    _columns = {
        'so_line_item_set_ids':fields.many2many('sale.order.line.item.set','po_line_so_item_set_rel','purchase_line_id', 'so_item_set_id','Choosen configurtion'),

    }

purchase_order_line()

class purchase_order(osv.osv):
    
    _inherit = "purchase.order"
    
    #TODO propose to OpenERP SA a hook in the module purchase, it will be cleaner
    def create(self, cr, uid, vals, context=None):
        if not context:
            context={}
        if context.get('purchase_order_from_procurement', False):
            procurement_obj = self.pool.get('procurement.order')
            procurement_id = procurement_obj.search(cr, uid, [['origin', '=', vals['origin']], ['id', 'in', context['purchase_order_from_procurement']]], context=context)
            if procurement_id:
                procurement = procurement_obj.browse(cr, uid, procurement_id[0], context=context)
                if procurement.so_line_item_set_ids:
                    print 'get item line'
                    line = list(vals['order_line'][0])[2]
                    line['so_line_item_set_ids'] = [(6,0, [x.id for x in procurement.so_line_item_set_ids])]
                    vals['order_line'] = [(0,0,line)]
        return super(purchase_order, self).create(cr, uid, vals, context=context)
            
    

purchase_order()

