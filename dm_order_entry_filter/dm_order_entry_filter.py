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
        message = ''
        if vals.has_key('order_session_id') and vals['order_session_id']:
            session_id = self.pool.get('dm.order.session').browse(cr, uid, vals['order_session_id'])
            if session_id.country_id and session_id.currency_id and session_id.dealer_id \
                and session_id.trademark_id and session_id.payment_method_id and vals['segment_id'] and vals['country_id']:
                country_name = self.pool.get('res.country').browse(cr, uid, vals['country_id']).name
                segment_id = self.pool.get('dm.campaign.proposition.segment').browse(cr, uid, vals['segment_id'])
                trademark_name = segment_id.campaign_id and segment_id.campaign_id.trademark_id.name
                currency_name = segment_id.campaign_id and segment_id.campaign_id.currency_id.name
                dealer_name = segment_id.campaign_id and segment_id.campaign_id.dealer_id.name
                payment_method_name = segment_id.campaign_id and segment_id.campaign_id.journal_id.name
                filter_country_name = session_id.country_id.name
                filter_trademark_name = session_id.trademark_id.name
                filter_currency_name = session_id.currency_id.name
                filter_dealer_name = session_id.dealer_id.name
                filter_payment_method_name = session_id.payment_method_id.name
                simple_list = [country_name, trademark_name, currency_name, dealer_name, payment_method_name]
                filter_list = [filter_country_name, filter_trademark_name, filter_currency_name, filter_dealer_name, filter_payment_method_name]
                field_list = ['country', 'trademark', 'currency', 'dealer', 'payment method']
                for j in range(0, len(field_list)):
                    if simple_list[j] != filter_list[j]:
                        msg = "%s order does not match \n" % (field_list[j])
                        message = message + msg
                vals.update({'state': 'error', 'state_msg': message})
        return super(dm_order, self).create(cr, uid, vals, context)
        
    def set_confirm(self, cr, uid, ids, *args):
        print "IN new confirm"
        so_id = self._create_sale_order(cr, uid, ids)
        order = self.browse(cr, uid, ids[0])
        field_list = ['so_confirm_do','invoice_create_do','invoice_validate_do',
                    'invoice_pay_do']
        if order.order_session_id and order.order_session_id.payment_method_id:
            print "23444444444",order.order_session_id.payment_method_id
            so_vals = {}
            for field in field_list: 
                if getattr(order.order_session_id.payment_method_id,field):
                    so_vals[field]  = getattr(order.order_session_id.payment_method_id,field)
            print "=====================",so_vals
            if so_vals:
                self.pool.get('sale.order').write(cr, uid, so_id, so_vals)  
        self._create_workitem(cr, uid, so_id)                       
        return True        
    
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
