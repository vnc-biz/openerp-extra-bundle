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

class training_participation_reassign_wizard(osv.osv_memory):
    _name = 'training.participation.reassign.wizard'

    _columns = {
        'participation_id' : fields.many2one('training.participation', 'Participation', required=True),
        'participation_seance_id' : fields.related('participation_id', 'seance_id', type='many2one', relation='training.seance', readonly=True, string='Seance'),
        'participation_seance_date' : fields.related('participation_id', 'seance_id', 'date', type='datetime', readonly=True, string='Date'),
        'participation_sl' : fields.related('participation_id', 'subscription_line_id', type='many2one', relation='training.subscription.line', readonly=True, string='Subscription Line'),
        'participation_session_id' : fields.related('participation_id', 'subscription_line_id', 'session_id', type='many2one', relation='training.session',
                                                    readonly=True,
                                                    string='Session'),
        'seance_id' : fields.many2one('training.seance', 'Seance',
                                      #domain="[('session_ids', 'in', [participation_session_id])]",
                                      required=True),
    }

    def on_change_seance(self, cr, uid, ids, seance_id, context=None):
        values = {
            'domain' : {
                'participation_id' : not seance_id and [] or [('seance_id', '=', seance_id)],
            }
        }

        return values

    def on_change_participation(self, cr, uid, ids, participation_id, context=None):
        if not participation_id:
            return {
                'value' : {
                    'seance_id' : 0,
                },
                'domain' : {
                    'seance_id' : [],
                },
            }

        p = self.pool.get('training.participation').browse(cr, uid, participation_id, context=context)
        return {
            'value' : {
                'participation_seance_id' : p.seance_id.id,
                'participation_seance_date' : p.seance_id.date,
                'participation_sl' : p.subscription_line_id.id,
                'participation_session_id' : p.subscription_line_id.session_id.id,
            },
            'domain' : {
                'seance_id' : [('id', 'in', [seance.id for seance in p.subscription_line_id.session_id.seance_ids])],
            }
        }

    def close_cb(self, cr, uid, ids, context=None):
        return {'type' : 'ir.actions.act_window_close'}

    def apply_cb(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)

        if this.participation_id.seance_id == this.seance_id:
            raise osv.except_osv(_('Warning'),
                                 _('You have selected the same seance'))

        this.participation_id.write({'seance_id' : this.seance_id.id})

        return {'type' : 'ir.actions.act_window_close'}

training_participation_reassign_wizard()

