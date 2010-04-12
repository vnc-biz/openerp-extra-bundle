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
    
    _columns = {
            'state': fields.selection([('draft', 'Draft'),('done', 'Done'),('error', 'Error')], 'Status', readonly=True),
            'state_msg': fields.text('State Message', readonly=True)
        }
    
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
    
dm_order() # }}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
