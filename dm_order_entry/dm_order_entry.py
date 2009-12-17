# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields
from osv import osv
from tools.translate import _

class dm_order(osv.osv): # {{{
    _name = "dm.order"
    _rec_name = 'customer_code'
    _columns = {
        'raw_datas': fields.char('Raw Datas', size=128),
        'customer_code': fields.char('Customer Code', size=64),
        'title': fields.char('Title', size=32),
        'customer_firstname': fields.char('First Name', size=64),
        'customer_lastname': fields.char('Last Name', size=64),
        'customer_add1': fields.char('Address1', size=64),
        'customer_add2': fields.char('Address2', size=64),
        'customer_add3': fields.char('Address3', size=64),
        'customer_add4': fields.char('Address4', size=64),
        'country_id': fields.many2one('res.country','Country'),
        'zip': fields.char('Zip Code', size=12),
        'zip_summary': fields.char('Zip Summary', size=64),
        'distribution_office': fields.char('Distribution Office', size=64),
        'segment_id': fields.many2one('dm.campaign.proposition.segment','Segment Code'),
        'offer_step_id': fields.many2one('dm.offer.step','Offer Step Code'),
        'state': fields.selection([('draft', 'Draft'),('done', 'Done')],
                                   'Status', readonly=True),
    }
    _defaults = {
        'state': lambda *a: 'draft',
    }

    def set_confirm(self, cr, uid, ids, *args):
        return True

    def onchange_rawdatas(self, cr, uid, ids, raw_datas):
        if not raw_datas:
            return {}
        raw_datas = "2;US-OERP-0000;162220;MR;Shah;Harshit;W Sussex;;25 Oxford Road;;BE;BN;BN11 1XQ;WORTHING.LU.SX"
        value = raw_datas.split(';')
        key = ['datamatrix_type', 'segment_id', 'customer_code', 'title', 
               'customer_lastname', 'customer_firstname', 'customer_add1',
               'customer_add2', 'customer_add3', 'customer_add4', 'country_id', 
               'zip_summary', 'zip', 'distribution_office']
        value = dict(zip(key, value))
        field_check = {'res.country':('country_id','Country'),
                       'dm.campaign.proposition.segment' : ('segment_id','Segment')
                      # 'dm.offer_step' : ('offer_step_id','Offer Step')
                      }
        for m in field_check:
            field = field_check[m][0]
            if value.has_key(field) and value[field]:
                f_id = self.pool.get(m).search(cr,uid,[('code','=',value[field])])
                if f_id:
                    value[field]= f_id
                raise osv.except_osv(_('Error !'),
                    _('No %s found for the code '%field_check[m][1]))
            else:
                raise osv.except_osv(_('Error !'),
                    _('There is no code defined for %s'%field_check[m][1]))
        return {'value': value}

dm_order() # }}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
