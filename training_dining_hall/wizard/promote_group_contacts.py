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
#~ import netsvc

class promote_group_contacts_wizard(osv.osv_memory):
    _name = 'promote.group.contacts.wizard'
    _rec_name = 'to_session_id'

    _columns = {
        'from_session_id': fields.many2one('training.session', 'Origin Session', help="Select the sessions from you want to Promote."),
        'to_session_id': fields.many2one('training.session', 'Destination Session', help="Select the sessions to you want to Promote."),
        'from_group_id': fields.many2one('training.group', 'Main Origin Group', help="Select the main group from you want to Promote."),
        'to_group_id': fields.many2one('training.group', 'Main Destination Group', help="Select the main group to you want to Promote."),
        'line_ids': fields.one2many('promote.line.group.contacts.wizard', 'parent_id', 'Child Destination Groups'),
        'create_participations': fields.boolean('Create Participations', help="Select if you want to create the participations for each contact promoted. Alert! This could take much long."),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        values = {}
        if context['active_model'] == 'training.session':
            session = self.pool.get('training.session').browse(cr, uid, context['active_id'], context = context)
            values['to_session_id'] = session.id
            group_obj = self.pool.get('training.group')
            group_ids = group_obj.search(cr, uid, [('parent_id', '=', False), ('session_id', '=', session.id)], context = context)
            group = group_obj.browse(cr, uid, group_ids, context = context)[0]
            values['to_group_id'] = group.id
        values['create_participations'] = False
        return values

    def search_from_group_childs(self, cr, uid, ids, context=None):
        ''' Fills the origin group lines to be promoted '''
        if context is None:
            context = {}
        from_group_id = self.browse(cr, uid, ids[0], context = context).from_group_id.id
        contact_obj = self.pool.get('res.partner.contact')
        line_group_contacts_obj = self.pool.get('promote.line.group.contacts.wizard')
        group_obj = self.pool.get('training.group')
        child_group_ids = group_obj.search(cr, uid, [('parent_id', '=', from_group_id)], context = context)
        child_groups = group_obj.browse(cr, uid, child_group_ids, context = context)
        for child_group in child_groups:
            values = {}
            if contact_obj.search(cr, uid, [('group_id', '=', child_group.id)], context = context):
                values['from_group_id'] = child_group.id
                values['parent_id'] = ids[0]
                line_group_contacts_obj.create(cr, uid, values, context = context)
            else:
                grand_child_group_ids = group_obj.search(cr, uid, [('parent_id', '=', child_group.id)], context = context)
                grand_child_groups = group_obj.browse(cr, uid, grand_child_group_ids, context = context)
                for grand_child_group in grand_child_groups:
                    if contact_obj.search(cr, uid, [('group_id', '=', grand_child_group.id)], context = context):
                        values['from_group_id'] = grand_child_group.id
                        values['parent_id'] = ids[0]
                        line_group_contacts_obj.create(cr, uid, values, context = context)
        return True

    def promote_contacts(self, cr, uid, ids, context=None):
        ''' Change the group of the contacts of a mapped groups
            and create the subscription, subscription_line and
            participations for each of them.
        '''
        if context is None:
            context = {}
        group_contacts = self.browse(cr, uid, ids[0], context = context)
        line_groups = group_contacts.line_ids
        contact_obj = self.pool.get('res.partner.contact')
        participation_generate_obj = self.pool.get('training.participation.generator')
        result = True
        for line_group in line_groups:
            if line_group.from_group_id and line_group.to_group_id:
                from_group = line_group.from_group_id
                to_group = line_group.to_group_id
                contact_ids = contact_obj.search(cr, uid, [('group_id', '=', from_group.id)], context = context)
                result = result and contact_obj.write(cr, uid, contact_ids, {'group_id': to_group.id}, context = context)
                contacts = contact_obj.browse(cr, uid, contact_ids, context = context)
                if group_contacts.create_participations:
                    for contact in contacts:
                        if contact.active:
                            result = result and participation_generate_obj.generate(cr, uid, contact, context=None)
        if result:
            return {'type': 'ir.actions.act_window_close'}
        return result
        
promote_group_contacts_wizard()


class promote_line_group_contacts_wizard(osv.osv_memory):
    _name = 'promote.line.group.contacts.wizard'
    _rec_name = 'parent_id'

    _columns = {
        'parent_id': fields.many2one('promote.group.contacts.wizard', 'Parent Group'),
        'from_group_id': fields.many2one('training.group', 'Origin Group', help="Select the origin group of the students."),
        'to_group_id': fields.many2one('training.group', 'Destination Group', help="Select the destination group of the students."),
    }    
        
promote_line_group_contacts_wizard()
