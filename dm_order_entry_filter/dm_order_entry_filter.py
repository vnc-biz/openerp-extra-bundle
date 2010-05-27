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

class dm_order_session(osv.osv): # {{{
    _inherit = "dm.order.session"
    
    _columns = {
        'country_id': fields.many2one('res.country', 'Country'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'dealer_id': fields.many2one('res.partner', 'Dealer'),
        'trademark_id': fields.many2one('dm.trademark', 'Trademark'),
        'payment_method_id': fields.many2one('dm.payment_method', 'Payment Method'),
    }
    
dm_order_session() # }}}

class dm_order(osv.osv): # {{{
    _inherit= "dm.order"
    
    def create(self, cr, uid, vals, context={}):
        so_vals = {}
        if 'order_session_id' in vals and vals['order_session_id']:
            session_id = self.pool.get('dm.order.session').browse(cr, uid, vals['order_session_id'])
            segment_id = self.pool.get('dm.campaign.proposition.segment').browse(cr, uid, vals['segment_id'])
            
            field_list = ['trademark_id', 'currency_id', 'dealer_id', 'journal_id']
            order_fields = dict(map(lambda x : (x,getattr(segment_id.campaign_id,x).name),field_list))
            order_fields['country_id'] = 'country_id' in vals and vals['country_id'] and \
                                    self.pool.get('res.country').browse(cr, uid, 
                                                vals['country_id']).name or \
                                    False
            field_list.pop()                
            field_list.extend(['country_id','payment_method_id'])

            filter_fields = dict(map(lambda x : (x,getattr(session_id,x) and \
                                getattr(session_id,x).name or False),field_list))
            message = ''            
            for field in field_list:
                if filter_fields[field] and order_fields[field] != filter_fields[field]:
                    msg = "%s does not match with filter value \n" % (field.replace('_id',' name'))
                    message = message + msg
            if message :
                vals.update({'state': 'error', 'state_msg': message})
                return super(dm_order, self).create(cr, uid, vals, context)
            else :
                field_list = ['so_confirm_do','invoice_create_do','invoice_pay_do',
                                                    'invoice_validate_do',]
                if session_id.payment_method_id:
                    so_vals = dict(map(lambda field : (field, \
                                getattr(session_id.payment_method_id,field) and \
                            getattr(session_id.payment_method_id,field) or \
                            False),field_list))
                    print so_vals
        order_id = super(dm_order, self).create(cr, uid, vals, context)
        order = self.browse(cr, uid, order_id, context)
        if order.sale_order_id and so_vals:
            self.pool.get('sale.order').write(cr, uid, order.sale_order_id.id, so_vals)
        return order_id
        
dm_order() # }}}

class dm_payment_method(osv.osv): # {{{
    _inherit = 'dm.payment_method'
    _columns = {
        'so_confirm_do': fields.boolean('Auto confirm sale order'),
        'invoice_create_do': fields.boolean('Auto create invoice'),
        'invoice_validate_do': fields.boolean('Auto validate invoice'),
        'invoice_pay_do': fields.boolean('Auto pay invoice'),
    }
dm_payment_method() # }}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
