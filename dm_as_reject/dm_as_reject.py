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

class dm_as_reject_type(osv.osv):#{{{
    _name = "dm.as.reject.type"
    _columns = {
        'name': fields.char('Description', size=64, required=True),
        'code': fields.char('Code', size=32, required=True),
    }
dm_as_reject_type()#}}}

class dm_as_reject(osv.osv):#{{{
    _name = "dm.as.reject"
    _columns = {
                
        'date': fields.datetime('Date', required=True),
        'name': fields.char('Description', size=128, required=True),
        'origin':fields.char('Origin', size=64),
        'type_od': fields.many2one('dm.as.reject.type', 'Type', required=True),
        'reject_type': fields.char('Type', size=64),
   
    }
    def on_change_reject_type(self, cr, uid, ids, type_od):
        res = {'value': {}}
        if type_od:
            reject_type = self.pool.get('dm.as.reject.type').read(cr, uid, [type_od])[0]
            res['value'] = {'reject_type': reject_type['code']}
        return res
    
dm_as_reject() #}}}

class dm_address_segmentation(osv.osv): # {{{
    _name = "dm.address.segmentation"
    _description = "Segmentation"
    _inherit = "dm.address.segmentation"
    
    _columns = {
        'ignore_rejects': fields.boolean('Ignore Rejects'),
        }
    
dm_address_segmentation() # }}}

class dm_as_reject_incident(osv.osv): # {{{
    _name = "dm.as.reject.incident"
    _description = "Reject Incidents"
    
    _columns = {
        'date': fields.datetime('Date', required=True),
        'user_id': fields.many2one('res.users', 'User', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'partner_address_id': fields.many2one('res.partner.address', 'Partner Address'),
        'reject_ids': fields.many2many('dm.as.reject', 'incident_reject_rel', 'incident_id', 'reject_id', 'Rejects'),
        'origin': fields.char('Origin', size=64),
        'note': fields.text('Description')
        }
    
dm_as_reject_incident() # }}}

class res_partner(osv.osv): # {{{
    _inherit = "res.partner"
    
    _columns = {
        'reject_ids': fields.one2many('dm.as.reject.incident', 'partner_id', 'Rejects')      
        }
    
res_partner() # }}}

class res_partner_address(osv.osv): # {{{
    _inherit = "res.partner.address"
    
    _columns = {
        'reject_ids': fields.one2many('dm.as.reject.incident', 'partner_address_id', 'Rejects')      
        }
    
res_partner_address() # }}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
