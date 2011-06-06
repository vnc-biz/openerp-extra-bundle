# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Raimon Esteve <resteve@zikzakmedia.com>
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

from osv import fields, osv
from tools.translate import _

class create_partner_wizard(osv.osv_memory):
    _inherit = "base.contact.create.partner.wizard"

    def create_partner(self, cr, uid, ids, data, context={}):
        partner_id, partner_address_id, partner_contact_id, partner_job_id = super(create_partner_wizard,self).create_partner(cr, uid, ids, data, context)
        
        values = {}
        values['notif_contact_id'] = partner_job_id
        values['notif_invoicing_id'] = partner_job_id
        
        self.pool.get('res.partner').write(cr, uid, [partner_id], values)
            
        return partner_id, partner_address_id, partner_contact_id, partner_job_id

create_partner_wizard()
