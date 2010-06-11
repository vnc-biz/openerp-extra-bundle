# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import fields, osv

class mrp_reversed_bom(osv.osv_memory):
    _name = "mrp.reversed.bom"
    _description = "Reversed Bom"
    
    _columns = {
    }

    def do_reverse(self, cr, uid, ids, context={}):
        """ To check the product type
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one 
        @param context: A standard dictionary
        @return:  
        """               
        bom_obj = self.pool.get('mrp.bom')
        bom_ids = context['active_ids']
        bom_ids = bom_obj.browse(cr, uid, context['active_ids'])
        for bom_id in bom_ids:
            new_bom_id = bom_obj.copy(cr, uid, bom_id.id, {'name': 'Reversed ' + bom_id.name,
                                                        'product_qty':(-1)*bom_id.product_qty,
                                                        'bom_lines' : [],
                                                        'product_uos_qty':(-1)*bom_id.product_uos_qty
            })
            for b in bom_id.bom_lines:
                print b
                bom_obj.copy(cr, uid, b.id, {'name': 'reversed' + b.name, 
                                            'bom_id':new_bom_id ,
                                            'product_qty':(-1)*b.product_qty,
                                            'product_uos_qty':(-1)*b.product_uos_qty
                    })
        return {}

mrp_reversed_bom()


