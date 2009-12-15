# -*- encoding: utf-8 -*-
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

class dm_order_entry_filter(osv.osv): # {{{
    _name = "dm.order.entry.filter"
    _description = "Order Entry Filter"
    
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=64, required=True),
        'country_id': fields.many2one('res.country', 'Country'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'dealer_id': fields.many2one('res.partner', 'Dealer'),
        'trademark_id': fields.many2one('dm.trademark', 'Trademark')
    }
    
dm_order_entry_filter() # }}}

class dm_order_session(osv.osv): # {{{
    _inherit = "dm.order.session"
    
    _columns = {
        'filter_id': fields.many2one('dm.order.entry.filter', 'Order Entry Filter') 
    }
    
dm_order_session() # }}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
