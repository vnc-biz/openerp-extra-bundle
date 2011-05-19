# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu>). All Rights Reserved
#    Copyright (C) 2010-2011 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
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


class training_session_duplicate_wizard(osv.osv_memory):
    _name = 'training.session.duplicate.wizard'

    _columns = {
        'session_id': fields.many2one('training.session', 'Session',
                                      required=True,
                                      readonly=True,
                                      domain=[('state', 'in', ['opened', 'opened_confirmed'])]),
        'group_id' : fields.many2one('training.group', 'Group',
                                     domain="[('session_id', '=', session_id)]"),
        'subscription_line_ids' : fields.many2many('training.subscription.line',
                                                   'training_sdw_participation_rel',
                                                   'wizard_id',
                                                   'participation_id',
                                                   'Participations',
                                                   domain="[('session_id', '=', session_id),('state', '=', 'confirmed')]"),
    }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type' : 'ir.actions.act_window_close'}

    def action_apply(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)

        if len(this.subscription_line_ids) == 0:
            raise osv.except_osv(_('Error'),
                                 _('You have not selected a participant of this session'))

        seances = []

        if any(len(seance.session_ids) > 1 for seance in this.session_id.seance_ids):
            raise osv.except_osv(_('Error'),
                                 _('You have selected a session with a shared seance'))

        #if not all(seance.state == 'opened' for seance in this.session_id.seance_ids):
        #    raise osv.except_osv(_('Error'),
        #                         _('You have to open all seances in this session'))

        lengths = [len(group.seance_ids)
                   for group in this.session_id.group_ids
                   if group != this.group_id]

        if len(lengths) == 0:
            raise osv.except_osv(_('Error'),
                                 _('There is no group in this session !'))

        minimum, maximum = min(lengths), max(lengths)

        if minimum != maximum:
            raise osv.except_osv(_('Error'),
                                 _('The defined groups for this session does not have the same number of seances !'))

        group_id = this.session_id.group_ids[0]

        seance_sisters = {}
        for group in this.session_id.group_ids:
            for seance in group.seance_ids:
                seance_sisters.setdefault((seance.date, seance.duration, seance.course_id, seance.kind,), {})[seance.id] = None

        seance_ids = []

        if len(this.group_id.seance_ids) == 0:
            proxy_seance = self.pool.get('training.seance')

            for seance in group_id.seance_ids:
                values = {
                    'group_id' : this.group_id.id,
                    'presence_form' : 'no',
                    'manual' : 0,
                    'participant_count_manual' : 0,
                    'contact_ids' : [(6, 0, [])],
                    'participant_ids' : [],
                    'duplicata' : 1,
                    'duplicated' : 1,
                    'is_first_seance' : seance.is_first_seance,
                }

                seance_ids.append( proxy_seance.copy(cr, uid, seance.id, values, context=context) )
        else:
            # If the there are some seances in this group
            seance_ids = [seance.id for seance in this.group_id.seance_ids]

        for seance in self.pool.get('training.seance').browse(cr, uid, seance_ids, context=context):
            key = (seance.date, seance.duration, seance.course_id, seance.kind,)
            if key in seance_sisters:
                for k, v in seance_sisters[key].items():
                    seance_sisters[key][k] = seance.id
            else:
                seance_sisters[key][seance.id] = seance.id

        final_mapping = {}
        for key, values in seance_sisters.iteritems():
            for old_seance_id, new_seance_id in values.iteritems():
                final_mapping[old_seance_id] = new_seance_id

        for sl in this.subscription_line_ids:
            for part in sl.participation_ids:
                part.write({'seance_id' : final_mapping[part.seance_id.id]})

        return {'type' : 'ir.actions.act_window_close'}

    def default_get(self, cr, uid, fields, context=None):
        record_id = context and context.get('record_id', False) or False

        res = super(training_session_duplicate_wizard, self).default_get(cr, uid, fields, context=context)

        if record_id:
            res['session_id'] = record_id

        return res

training_session_duplicate_wizard()

