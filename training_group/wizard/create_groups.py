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
import netsvc


class training_create_groups_wizard(osv.osv_memory):
    _name = 'training.create.groups.wizard'

    _columns = {
        'level1': fields.char('Level 1', size=32, required=True, help="You must enter the level 1 group name. Values separated with commas to construct the group name."),
        'level2': fields.char('Level 2', size=32, help="Enter the level 2 values separated with commas to construct the group name."),
        'level3': fields.char('Level 3', size=32, help="Enter the level 3 values separated with commas to construct the group name."),
        'level_generate_seances': fields.selection([('level1', 'Level 1'),('level2', 'Level 2'), ('level3', 'Level 3')], 'Generate Seances', required=False),
        'session_ids': fields.many2many('training.session', 'training_session_groups_rel', 'child_id', 'parent_id', 'Sessions', required=True, help="The session related with the groups."),
        'state': fields.selection([
            ('draft','Draft'),
            ('done','Done'),
        ],'State', required=True, readonly=True),
    }

    def _get_default_level1 (self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if context['active_model'] == 'training.session':
            for training_session in self.pool.get('training.session').browse(cr, uid, ids, context=context):
                return training_session.name
        return False

    _defaults = {
        'state' : lambda *a: 'draft',
        'session_ids': lambda cr, uid, ids, context: context['active_model'] != 'ir.ui.menu' and context['active_ids'] or [],
        'level1': lambda self, cr, uid, context: self._get_default_level1(cr, uid, context['active_ids'], context=context),
        'level_generate_seances': lambda *a: 'level1',
    }

    def generate_groups (self, cr, uid, ids, context=None):
        if not context:
            context = {}
        self.logger = netsvc.Logger()
        training_group_obj = self.pool.get('training.group')
        for data in self.browse(cr, uid, ids, context=context):
            for level1 in data.level1.split(','):
                for session_id in data.session_ids:
                    level1_id = training_group_obj.search(cr, uid, [('name', '=', level1), ('session_id', '=', session_id.id)], context=context)
                    level1_id = level1_id and level1_id[0] or False
                    if not level1_id:
                        values = {}
                        values['name'] = level1
                        values['session_id'] = session_id.id
                        if data.level_generate_seances == 'level1':
                            values['generate_seances'] = True
                        level1_id = training_group_obj.create(cr, uid, values, context = context)
                if data.level2:
                    for level2 in data.level2.split(','):
                        for session_id in data.session_ids:
                            level2_id = training_group_obj.search(cr, uid, [('name', '=', level1 + '-' + level2), ('session_id', '=', session_id.id)], context=context)
                            level2_id = level2_id and level2_id[0] or False
                            if not level2_id:
                                values = {}
                                values['name'] = level1 + '-' + level2
                                values['session_id'] = session_id.id
                                values['parent_id'] = level1_id
                                if data.level_generate_seances == 'level2':
                                    values['generate_seances'] = True
                                level2_id = training_group_obj.create(cr, uid, values, context = context)
                        if data.level3:
                            for level3 in data.level3.split(','):
                                for session_id in data.session_ids:
                                    if not training_group_obj.search(cr, uid, [('name', '=' , level1 + '-' + level2 + '-' + level3), ('session_id', '=', session_id.id)], context=context):
                                        values = {}
                                        values['name'] = level1 + '-' + level2 + '-' + level3
                                        values['session_id'] = session_id.id
                                        values['parent_id'] = level2_id
                                        if data.level_generate_seances == 'level3':
                                            values['generate_seances'] = True
                                        training_group_obj.create(cr, uid, values, context = context)
        return {'type': 'ir.actions.act_window_close'}

training_create_groups_wizard()
