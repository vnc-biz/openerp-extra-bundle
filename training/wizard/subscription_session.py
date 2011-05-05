# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jesús Martín <jmartin@zikzakmedia.com>
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

from osv import osv
from osv import fields

class training_subscription_session(osv.osv_memory):
    _name = 'training.subscription.session'
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner',  required=True),
        'job_ids': fields.many2many('res.partner.job', 'res_partner_job_rel', 'training_id', 'partner_id', 'Contacts'),
        'line_ids': fields.many2many('training.session', 'training_session_rel', 'training_id', 'session_id', 'Sessions'),
    }

    def make_subscription(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        form = self.read(cr, uid, ids, [], context=context)[0]
        subscription_obj = self.pool.get('training.subscription')
        subscription_line_obj = self.pool.get('training.subscription.line')
        partner_obj = self.pool.get('res.partner')
        partner_id = form['partner_id']
        values = subscription_obj.on_change_partner(cr, uid, [], partner_id)['value']
        values.update({
                'partner_id' : partner_id,
            })
        subscription_id = subscription_obj.create(cr, uid, values, context=context)
        partner = partner_obj.browse(cr, uid, form['partner_id'], context=context)
        def_pricelist_id = partner.property_product_pricelist.id
        masslines = self.pool.get('training.subscription.mass.line')
        if form['job_ids']:
            for job_id in form['job_ids']:
                for line in form['line_ids']:
                    val={'session_id':line, 'wizard_id':False}
                    mlid = masslines.create(cr, uid, val)
                    massline = masslines.browse(cr, uid, mlid, context=context)
                    job = self.pool.get('res.partner.job').browse(cr, uid, job_id, context=context)
                    values = subscription_line_obj._get_values_from_wizard(cr, uid, subscription_id, job, massline, context=context)
                    sl_id = subscription_line_obj.create(cr, uid, values, context=context)
        return {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'training.subscription',
            'view_id': self.pool.get('ir.ui.view').search(cr, uid, [('name','=','training.subscription.form')], context=context),
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id' : int(subscription_id)
        }

training_subscription_session()
