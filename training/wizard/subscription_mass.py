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

#from addons.training.training import training_offer_kind_compute

class training_subscription_mass_wizard(osv.osv_memory):
    _name = 'training.subscription.mass.wizard'
    _description = 'Mass Subscription Wizard'

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close'}

    def action_apply(self, cr, uid, ids, context=None):
        subscription_form_view = context and context.get('subscription_form_view', False) or False
        record_id = context and context.get('record_id', False) or False

        this = self.browse(cr, uid, ids)[0]

        subscription_proxy = self.pool.get('training.subscription')
        subscription_line_proxy = self.pool.get('training.subscription.line')
        subscription_line_second_proxy = self.pool.get('training.subscription.line.second')

        subscriptions = {}

        if record_id:
            for job in this.job_ids:
                for subscription_mass_line in this.session_ids:
                    sl_id = subscription_line_proxy._create_from_wizard(cr, uid, this, record_id, job, subscription_mass_line, context=context)

            return {
                'type' : 'ir.actions.act_window_close',
            }

        for job in this.job_ids:
            # if the job hasn't a partner, we put this subscription in waiting mode
            if not job.name:
                for subscription_mass_line in this.session_ids:
                    subscription_line_second_proxy._create_from_wizard(cr, uid, this, job, subscription_mass_line, context=context)

            else:
                for subscription_mass_line in this.session_ids:
                    subscriptions.setdefault(job.name.id, []).append((job, subscription_mass_line,))

        subscription_ids = []

        # We create all subscription where there is a partner associated to the job
        for partner_id, lines in subscriptions.iteritems():
            values = subscription_proxy.on_change_partner(cr, uid, [], partner_id)['value']
            values.update({
                'partner_id' : partner_id,
            })

            subscription_id = subscription_proxy.create(cr, uid, values, context=context)

            for job, subscription_mass_line in lines:
                subscription_line_proxy._create_from_wizard(cr, uid, this, subscription_id, job, subscription_mass_line, context=context)

            subscription_ids.append(subscription_id)
            
        mod_id = self.pool.get('ir.model.data').search(cr, uid, [('name', '=', 'training_subscription_all_act')])[0]
        res_id = self.pool.get('ir.model.data').read(cr, uid, mod_id, ['res_id'])['res_id']
        act_win = self.pool.get('ir.actions.act_window').read(cr, uid, res_id, [])
        act_win['domain'] = [('id','in',subscription_ids)]
        act_win['name'] = _('Subscriptions')

        return act_win

    _columns = {
        'partner_id' : fields.many2one('res.partner', 'Partner'),
        'job_ids' : fields.many2many('res.partner.job',
                                     'tms_contact_job_rel',
                                     'ms_id',
                                     'job_id',
                                     'Contacts',
                                    ),
        'session_ids' : fields.one2many('training.subscription.mass.line', 'wizard_id', 'Sessions'),
    }

    def default_get(self, cr, uid, fields, context=None):
        record_id = context and context.get('record_id', False) or False

        res = super(training_subscription_mass_wizard, self).default_get(cr, uid, fields, context=context)

        if record_id:
            partner_id = self.pool.get('training.subscription').browse(cr, uid, record_id, context=context).partner_id.id
            res['partner_id'] = partner_id

        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        record_id = context and context.get('record_id', False) or False

        res = super(training_subscription_mass_wizard, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if record_id:
            if 'fields' in res and 'partner_id' in res['fields']:
                res['fields']['partner_id']['readonly'] = True

        return res

training_subscription_mass_wizard()


def training_offer_kind_compute(obj, cr, uid, context=None):
    proxy = obj.pool.get('training.offer.kind')
    return [(kind.code, kind.name) for kind in proxy.browse(cr, uid, proxy.search(cr, uid, []))] or []

class mass_subscription_line(osv.osv_memory):
    _name = 'training.subscription.mass.line'

    _columns = {
        'wizard_id' : fields.many2one('training.subscription.mass.wizard', 'Wizard'),
        'session_id' : fields.many2one('training.session', 'Session',
                                       domain="[('state', 'in', ('opened','opened_confirmed', 'closed_confirmed', 'inprogress'))]", required=True),
        'allow_closed_session': fields.boolean('Allow Closed Session'),
        'kind' : fields.related('session_id', 'offer_id', 'kind',
                                type = 'selection',
                                selection = training_offer_kind_compute,
                                string = 'Kind',
                                readonly = True),
    }

    def on_change_allow_closed_session(self, cr, uid, ids, new_allow, context=None):
        if new_allow:
            return {
                'domain': {'session_id': []}
            }
        else:
            return {
                'domain': {'session_id': [('state', 'in', ('opened','opened_confirmed', 'closed_confirmed', 'inprogress'))]}
            }


    def on_change_session(self, cr, uid, ids, context=None):
        return {}

mass_subscription_line()
