# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
#    sale_bundle_product for OpenERP                                          #
# Copyright (c) 2011 CamptoCamp. All rights reserved. @author Joel Grand-Guillaume #
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

class product_item_set_line(osv.osv):
    
    _name = "product.item.set.line"
    _description = "Product Item Set Line"
    _rec_name = "product_id"
    
    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'item_set_id': fields.many2one('product.item.set', 'Item Set'),
        'uom_id': fields.many2one('product.uom', 'Product UoM', required=True),
        'is_default': fields.boolean('Is default ?'),
        'allow_chg_qty': fields.boolean('Allow change quantity ?', help="Allow the user to change the quantity."),
        'sequence': fields.integer('Sequence'),
        'qty_uom': fields.integer('Quantity', required=True),
    }

    _defaults = {
        'is_default' : lambda *a: False,
        'allow_chg_qty' : lambda *a: False,
    }

product_item_set_line()

class product_item_set(osv.osv):
    
    _name = "product.item.set"
    _description = "Product Item Set"

    _columns = {
        'item_set_line_ids':fields.one2many('product.item.set.line', 'item_set_id', 'Item Set Lines'),
        'multi_select': fields.boolean('Allow multi-select ?'),
        'required': fields.boolean('Requiered ?'),
        'name' : fields.char('Name', size=128, required=True),
        'sequence': fields.integer('Sequence'),
    }

    _defaults = {
        'multi_select' : lambda *a: False,
        'required' : lambda *a: True,
    }

product_item_set()

class sale_order_line_item_set(osv.osv):
    
    _name = "sale.order.line.item.set"
    _description = "sale order line item set"
    _rec_name = "product_id"
    

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True, select=True),
        'uom_id': fields.many2one('product.uom', 'UoM', required=True, select=True),
        'qty_uom': fields.integer('Quantity', required=True),
    }

    _defaults = {

    }

sale_order_line_item_set()

