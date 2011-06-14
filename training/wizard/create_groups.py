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


class training_create_groups_wizard(osv.osv_memory):
    _name = 'training.create.groups.wizard'

    _columns = {
        'prefix': fields.char('Prefix', size=32, required=True, help="Prefix values separated with commas to construct the group name."),
        'suffix': fields.char('Suffix', size=32, help="Suffix values separated with commas to construct the group name."),
        'session_ids': fields.many2many('training.session', 'training_session_groups_rel', 'child_id', 'parent_id', 'Sessions', required=True, help="The session related with the groups."),
        'state':fields.selection([
            ('draft','Draft'),
            ('done','Done'),
        ],'State', required=True, readonly=True),
    }
    
    _defaults = {
        'state' : lambda *a: 'draft',
        'session_ids': lambda cr, uid, ids, context: context['active_model'] != 'ir.ui.menu' and context['active_ids'] or []
    }
    
    def generate_groups (self, cr, uid, ids, context=None):
        if not context:
            context = {}
        training_group = self.pool.get('training.group')
        for group_id in self.browse(cr, uid, ids, context=context):
            for prefix in group_id.prefix.split(','):
                if not group_id.suffix:
                    for session_id in group_id.session_ids:
                        if not training_group.search(cr, uid, [('name', '=' , prefix), ('session_id', '=', session_id.id)], context=context):
                            values =  {
                                'name': prefix,
                                'session_id': session_id.id
                            }
                            training_group.create(cr, uid, values, context = context)
                else:
                    for suffix in group_id.suffix.split(','):
                        for session_id in group_id.session_ids:
                            if not training_group.search(cr, uid, [('name', '=' , prefix + suffix), ('session_id', '=', session_id.id)], context=context):
                                values =  {
                                    'name': prefix + suffix,
                                    'session_id': session_id.id
                                }
                                training_group.create(cr, uid, values, context = context)
        return {'type': 'ir.actions.act_window_close'}

training_create_groups_wizard()

