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

from osv import osv
from osv import fields
import netsvc
from tools.translate import _

class training_subscription_cancellation_wizard(osv.osv_memory):
    _name = 'training.subscription.cancellation.wizard'

    _description = 'Training Subscription Cancellation Wizard'

    _columns = {
        'subscription_line_id' : fields.many2one('training.subscription.line', 'Subscription Line',
             domain="[('state', 'in', ['draft', 'confirmed']),('session_id.state', 'in', ('opened', 'opened_confirmed', 'closed_confirmed'))]",
             required=True),
        'subscription_id': fields.related('subscription_line_id', 'subscription_id',
                                           type='many2one',
                                           relation='training.subscription',
                                           string='Subscription',
                                           readonly=True),
        'partner_subscription_id': fields.related('subscription_line_id', 'subscription_id', 'partner_id',
                                      type='many2one',
                                      relation='res.partner',
                                      string='Partner',
                                      readonly=True),
        'participant_id': fields.related('subscription_line_id', 'job_id',
                                          type='many2one',
                                          relation='res.partner.job',
                                          string='Participant',
                                          readonly=True),
        'session_id': fields.related('subscription_line_id', 'session_id',
                                      type='many2one',
                                      relation='training.session',
                                      string='Session',
                                      readonly=True),
        'session_offer_id': fields.related('subscription_line_id', 'session_id', 'offer_id',
                                            type='many2one',
                                            relation='training.session',
                                            string='Session Offer',
                                            readonly=True),
        'session_date': fields.related('subscription_line_id', 'session_id', 'date',
                                        type='datetime',
                                        string='Session Date',
                                        readonly=True),
        'session_state': fields.related('subscription_line_id', 'session_id', 'state',
                                         type='selection',
                                         selection=[
                                             ('draft', 'Draft'),
                                             ('opened', 'Opened'),
                                             ('opened_confirmed', 'Confirmed'),
                                             ('closed_confirmed', 'Closed Subscriptions'),
                                             ('inprogress', 'In Progress'),
                                             ('closed', 'Closed'),
                                             ('cancelled', 'Cancelled')
                                         ],
                                         string='Session State',
                                         readonly=True),
        'new_participant_id': fields.many2one('res.partner.job', 'Participant',
                                               domain="[('name', '=', partner_id),('id', '!=', participant_id),('state', '=', 'current')]"),
        'new_participant_email': fields.char('Email', size=128),
        'new_session_id': fields.many2one('training.session', 'Session',
                                           domain="[('state', 'in', ('opened', 'opened_confirmed')),('date', '>', time.strftime('%Y-%m-%d')),('date', '>', session_date),('offer_id', '=', session_offer_id)]"
                                          ),
        'new_session_date': fields.related('new_session_id', 'date', type='datetime', string='Session Date', readonly=True),
        'cancellation_reason': fields.text('Reason'),
        'cancellation_medical_certificate_toggle': fields.boolean('Has Justification'),
        'cancellation_medical_certificate_name': fields.char('Filename', size=128),
        'cancellation_medical_certificate': fields.binary('Justification'),
        'state': fields.selection([('init', 'Init'),
                                    ('replacement', 'Replacement'),
                                    ('postponement', 'Postponement'),
                                    ('cancellation', 'Cancellation'),
                                    ('end', 'End')],
                                   'State',
                                   required=True,
                                   readonly=True
                                  ),
    }

    _defaults = {
        'subscription_line_id': lambda obj, cr, uid, context: context['active_id'],
        'state': lambda *a: 'init',
    }

    def on_change_subscription_line(self, cr, uid, ids, subscription_line_id, context=None):
        if not subscription_line_id:
            return {}
        subscription_line = self.pool.get('training.subscription.line').browse(cr, uid, subscription_line_id, context=context)
        return {
            'value' : {
                'subscription_id' : subscription_line.subscription_id.id,
                'subscription_line_id' : subscription_line.id,
                'session_id' : subscription_line.session_id.id,
                'session_date' : subscription_line.session_id.date,
                'session_state' : subscription_line.session_id.state,
                'partner_subscription_id' : subscription_line.subscription_id.partner_id.id,
                'participant_id' : subscription_line.job_id.id,
                'session_offer_id' : subscription_line.session_id.offer_id.id,
            }
        }

    def on_change_new_participant(self, cr, uid, ids, new_participant_id, context=None):
        if not new_participant_id:
            return {}
        job = self.pool.get('res.partner.job').browse(cr, uid, new_participant_id, context=context)
        return {'value' : {'new_participant_email' : job.email }}

    def on_change_new_session(self, cr, uid, ids, new_session_id, context=None):
        if not new_session_id:
            return {}
        session = self.pool.get('training.session').browse(cr, uid, new_session_id, context=context)
        return {
            'value' : {
                'new_session_date' : session.date,
            }
        }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close'}

    def action_cancellation(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'cancellation'}, context=context)

    def action_replacement(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'replacement'}, context=context)

    def action_postponement(self, cr, uid, ids, context=None):
        # Assign a new session to the subscription line
        return self.write(cr, uid, ids, {'state' : 'postponement'}, context=context)

    def action_apply(self, cr, uid, ids, context=None):
        if not ids:
            return False
        this = self.browse(cr, uid, ids[0], context=context)
        old_participant_id = this.participant_id
        workflow = netsvc.LocalService('workflow')
        context2 = context.copy()
        if 'default_state' in context2:
            del context2['default_state']
        if this.state == 'cancellation':
            if this.cancellation_medical_certificate:
                values = {
                    'name' : 'Medical Certificate',
                    'datas' : this.cancellation_medical_certificate,
                    'datas_fname' : this.cancellation_medical_certificate_name,
                    'description' : 'Medical Certificate',
                    'res_model' : 'training.subscription.line',
                    'res_id' : this.subscription_line_id.id,
                }
                self.pool.get('ir.attachment').create(cr, uid, values, context=context2)
            this.subscription_line_id.write(
                {
                    'has_certificate' : this.cancellation_medical_certificate_toggle,
                    'reason_cancellation' : this.cancellation_reason,
                },
                context=context2
            )
            workflow.trg_validate(uid, 'training.subscription.line', this.subscription_line_id.id, 'signal_cancel', cr)
        elif this.state == 'replacement':
            objects = {
                'new_participant_id' : this.new_participant_id,
                'old_participant_id' : old_participant_id,
            }
            this.subscription_line_id.write( { 'job_id' : this.new_participant_id.id, 'job_email' : this.new_participant_email, })
            internal_note = []
            if this.subscription_line_id.internal_note:
                internal_note.append(this.subscription_line_id.internal_note)
            internal_note.append(_("Replacement: %s %s -> %s %s") % (old_participant_id.contact_id.first_name,
                                                                     old_participant_id.contact_id.name,
                                                                     this.new_participant_id.contact_id.first_name,
                                                                     this.new_participant_id.contact_id.name))
            this.subscription_line_id.write({'internal_note' : "\n----\n".join(internal_note)})
        elif this.state == 'postponement':
            values = {
                'session_id' : this.new_session_id.id,
            }
            sl_proxy = self.pool.get('training.subscription.line')
            new_sl_id = sl_proxy.copy(cr, uid, this.subscription_line_id.id, values, context = context2 or {})
            new_sl = sl_proxy.browse(cr, uid, new_sl_id, context=context2)
            new_sl.write({'internal_note' : _("Created by Postponement of %s") % this.subscription_line_id.name})
            this.subscription_line_id.write({'reason_cancellation' : _("Cancelled by Postponement: %s") % new_sl.name })
            if this.subscription_line_id.state == 'confirmed':
                workflow.trg_validate(uid, 'training.subscription.line', new_sl_id, 'signal_confirm', cr)
            workflow.trg_validate(uid, 'training.subscription.line', this.subscription_line_id.id, 'signal_cancel', cr)
        return self.write(cr, uid, ids, {'state' : 'end'}, context=context)

    def action_done(self, cr, uid, ids, context=None):
        return {'type' : 'ir.actions.act_window_close'}

training_subscription_cancellation_wizard()
