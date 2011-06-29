# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jesús Martín <jmartin@zikzakmedia.com>
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


class training_create_seances_wizard(osv.osv_memory):
    _name = 'training.create.seances.wizard'

    _columns = {
        'session_ids': fields.many2many('training.session', 'training_session_seances_rel', 'child_id', 'parent_id', 'Sessions', required=True, help="The session related with the seances."),
        'state':fields.selection([
            ('draft','Draft'),
            ('done','Done'),
        ],'State', required=True, readonly=True),
    }
    
    _defaults = {
        'state' : lambda *a: 'draft',
        'session_ids': lambda cr, uid, ids, context: context['active_model'] != 'ir.ui.menu' and context['active_ids'] or []
    }

    def dining_hall_generate_seances (self, cr, uid, ids, context=None):
        if not context:
            context = {}
        self.pool.get('training.session').dining_hall_create_seances(cr, uid, context['session_ids'][0][2], context=context)
        return {'type': 'ir.actions.act_window_close'}

#    def dining_hall_generate_seances (self, cr, uid, ids, context=None):
#        if not context:
#            context = {}
#        for session_ids in context['session_ids']:
#            self.pool.get('training.session').dining_hall_create_seances(cr, uid, session_ids[2], context=context)
#        return {'type': 'ir.actions.act_window_close'}

training_create_seances_wizard()

