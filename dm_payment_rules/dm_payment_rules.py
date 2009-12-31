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

class dm_payment_rule(osv.osv): # {{{
    _name = 'dm.payment_rule'
    _columns = {
                
        'name': fields.char('Name', size=64, required=True),
        'dealer_id': fields.many2one('res.partner','Dealer', domain="[('category','=','dealer')]"),
        'trademark_id': fields.many2one('dm.trademark', 'Trademark'),
        'country_id': fields.many2one('res.country', 'Country'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'payment_method_id': fields.many2one('dm.payment_method', 'Payment Method'),
        'journal_id': fields.many2one('account.journal', 'Journal'),

    }
dm_payment_rule() # }}}

class dm_campaign_payment_rule(osv.osv): # {{{
    _name = 'dm.campaign.payment_rule'
    _columns = {
      
        'name': fields.char('Name', size=64, required=True),
        'dealer_id': fields.many2one('res.partner','Dealer', domain="[('category','=','dealer')]"),
        'trademark_id': fields.many2one('dm.trademark', 'Trademark'),
        'country_id': fields.many2one('res.country', 'Country'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'payment_method_id': fields.many2one('dm.payment_method', 'Payment Method'),
        'journal_id': fields.many2one('account.journal', 'Journal'),
        'campaign_id': fields.many2one('dm.campaign', 'Campaign'),

    }
dm_campaign_payment_rule() # }}}

class dm_campaign(osv.osv): # {{{
    _inherit = "dm.campaign"
    _columns = {
                
        'payment_rule_ids': fields.one2many('dm.campaign.payment_rule', 'campaign_id',
                                            'Payment Rules'), 
    }    
dm_campaign() # }}}

class dm_campaign_proposition_payment_rule(osv.osv): # {{{
    _name = 'dm.campaign.proposition.payment_rule'
    _columns = {
      
        'name': fields.char('Name', size=64, required=True),
        'dealer_id': fields.many2one('res.partner','Dealer', domain="[('category','=','dealer')]"),
        'trademark_id': fields.many2one('dm.trademark', 'Trademark'),
        'country_id': fields.many2one('res.country', 'Country'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'payment_method_id': fields.many2one('dm.payment_method', 'Payment Method'),
        'journal_id': fields.many2one('account.journal', 'Journal'),
        'proposition_id': fields.many2one('dm.campaign.proposition', 'Campaign Proposition'),

    }
dm_campaign_proposition_payment_rule() # }}}

class dm_campaign_proposition(osv.osv): # {{{
    _inherit = "dm.campaign.proposition"
    _columns = {
                
        'payment_rule_ids': fields.one2many('dm.campaign.proposition.payment_rule', 'proposition_id',
                                            'Payment Rules'), 
    }  
      
dm_campaign_proposition() # }}}

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
