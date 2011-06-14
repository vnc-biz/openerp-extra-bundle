# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu>). All Rights Reserved
#    Copyright (C) 2010 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
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
############################################################################################

from osv import osv, fields
from tools.translate import _

class training_offer_purchase_line_update_wizard(osv.osv_memory):
    _name = 'training.offer.purchase.line.update.wizard'
    _columns = {
        'name': fields.char('Summary', size=256),
        'log': fields.text('Log Text'),
        'date': fields.datetime('Date'),
        'state': fields.selection([('confirm','Confirm'),('update','Update')]),
    }

    _defaults = {
        'state': lambda *a: 'confirm',
    }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close' }

    def action_close(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close' }

    def action_confirm(self, cr, uid, ids, context=None):
        offer_proxy = self.pool.get('training.offer')
        offer_id = context.get('active_id', False)
        val = offer_proxy.action_update_seance_procurements(cr, uid, offer_id, context=context)
        if val:
            val['state'] = 'update'
        else:
            val = { 'name': _('FAILED')}
        return self.write(cr, uid, ids, val, context=context)

training_offer_purchase_line_update_wizard()

