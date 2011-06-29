# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
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
from osv import osv, fields
from tools.translate import _

class res_partner_contact(osv.osv):
    _inherit = "res.partner.contact"
    
    def _offers_contact(self, cr, uid, ids, name, args, context=None):
        result = {}
        for contact in ids:
            src = []
            lines = []
            subscription_lines = self.pool.get('training.subscription.line').search(cr, uid, [('contact_id','=',contact)])
            if len(subscription_lines) > 0:
                for subscription_line in self.pool.get('training.subscription.line').browse(cr, uid, subscription_lines):
                    lines.append(subscription_line.session_id.offer_id.id)
            result[contact] = lines
        return result


    _columns = {
        'dj_username':fields.char('Username ID', size=100, readonly=True),
        'dj_email':fields.char('Email ID', size=100, readonly=True),
        'offer_ids': fields.function(_offers_contact, method=True, type='many2many', relation='training.offer', string='Offers'),
    }

res_partner_contact()
