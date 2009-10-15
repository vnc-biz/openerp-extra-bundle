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
from osv import fields, osv

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _description = 'Account Invoice'
    _columns = {
        'domiciled' : fields.boolean('Domiciled'), 
        'domiciled_send_date' : fields.date('Domiciliation Sending Date'), 
        }
    
    def on_change_partner_id(self, cr, uid, id, partner):
        if not partner:
            return {'value' : {'domiciled' : False}}
        partner_obj = self.pool.get('res.partner').browse(cr, uid, partner)
        domiciled = partner_obj.domiciliation_bool
        return {'value' : {'domiciled' : domiciled} }

account_invoice()

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _description = 'Partner'
    _columns = {
        'domiciliation_bool':fields.boolean('Domiciliation'), 
        'domiciliation' : fields.char('Domiciliation Number', size=32)
        }
res_partner()

class res_partner_bank(osv.osv):
    _inherit = "res.partner.bank"
    _columns = {
                'institution_code':fields.char('Institution Code', size=3, help="Code of the financial institution used for Dom80 Export"), 
    }

class res_company(osv.osv):
    _inherit = 'res.company'
    _description = 'Company'
    _columns = {
        'id_sender' : fields.char('Identification number of the Sender' , size=11, help="Sender Id for Dom80 export header"), 
        'id_creditor' : fields.char('Identification number of the Creditor' , size=11, help="Creditor Id for Dom80 export header")
        }
res_company()


class invoice_export_log(osv.osv):
    _name = "invoice.export.log"
    _description = "Invoice Export History"
    _rec_name = 'invoice_id'
    _columns = {
        'state': fields.selection([('failed', 'Failed'), ('succeeded', 'Succeeded')], 'Status', readonly=True), 
        'file': fields.binary('Saved File', readonly=True), 
        'note': fields.text('Creation Log', readonly=True), 
        'create_date': fields.datetime('Creation Date', required=True, readonly=True), 
        'create_uid': fields.many2one('res.users', 'Creation User', required=True, readonly=True), 
    }
invoice_export_log()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

