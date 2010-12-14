# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

import wizard
import netsvc
import ir
import pooler
import tools

form = """<?xml version="1.0"?>
<form string="Confirm Subscription Lines">
    <separator string="Subscription" colspan="4" />
    <field name="subscription_id" />
    <field name="subscription_line_id" />
    <separator string="Session" colspan="4" />
    <field name="session_id" />
    <field name="session_date" />
    <separator string="Participant" colspan="4" />
    <field name="partner_id" />
    <field name="old_job_id" />
    <separator string="New Participant" colspan="4" />
    <field name="new_job_id" context="{'partner_id' : partner_id}" domain="[('name', '=', partner_id),('id', '!=', old_job_id)]" on_change="on_change_job(new_job_id)" />
    <field name="new_job_email" />
</form>
"""

fields = {
    'subscription_id' : {
        'string' : 'Subscription',
        'type' : 'many2one',
        'relation' : 'training.subscription',
        'readonly' : True,
    },
    'subscription_line_id' : {
        'string' : 'Subscription Line',
        'type' : 'many2one',
        'relation' : 'training.subscription.line',
        'readonly' : True,
    },
    'session_id' : {
        'string' : 'Session',
        'type' : 'many2one',
        'relation' : 'training.session',
        'readonly' : True,
    },
    'session_date' : {
        'string' : 'Session Date',
        'type' : 'datetime',
        'readonly' : True,
    },
    'partner_id' : {
        'string' : 'Partner',
        'type' : 'many2one',
        'relation' : 'res.partner',
        'readonly' : True,
    },
    'old_job_id' : {
        'string' : 'Participant',
        'type' : 'many2one',
        'relation' : 'res.partner.job',
        'readonly' : True,
    },
    'new_job_id' : {
        'string' : 'Participant',
        'type' : 'many2one',
        'relation' : 'res.partner.job',
        'required' : True,
    },
    'new_job_email' : {
        'string' : 'Participant Email',
        'type' : 'char',
        'size' : 64,
    }
}

class change_participant(wizard.interface):
    def init(self, cr, uid, data, context=None):
        if data['id']:
            subscription_line = pooler.get_pool(cr.dbname).get(data['model']).browse(cr, uid, data['id'], context=context)
            if subscription_line:
                if subscription_line.state in ('done', 'cancelled'):
                    raise wizard.except_wizard(_('Warning'),
                                               _("You can not select a subscription with the following state: Done or Cancelled"))
                return {
                    'subscription_id' : subscription_line.subscription_id.id,
                    'subscription_line_id' : subscription_line.id,
                    'session_id' : subscription_line.session_id.id,
                    'session_date' : subscription_line.session_id.date,
                    'partner_id' : subscription_line.subscription_id.partner_id.id,
                    'old_job_id' : subscription_line.job_id.id,
                }
        return {}

    def _confirm(self, cr, uid, data, context=None):
        old_job_id = data['form']['old_job_id']
        new_job_id = data['form']['new_job_id']
        if old_job_id == new_job_id:
            return {}

        sl = pooler.get_pool(cr.dbname).get('training.subscription.line').browse(cr, uid, data['id'], context=context)
        if sl.state in ('done', 'cancelled'):
            raise wizard.except_wizard(_('Warning'),
                                       _("You can not select a subscription with the following state: Done or Cancelled"))

        sl.write({'job_id' : new_job_id, 'job_email' : data['form']['new_job_email']})

        return {}

    states = {
        'init' : {
            'actions': [init],
            'result': {
                'type': 'form',
                'arch': form,
                'fields': fields,
                'state': [
                    ('end', 'Cancel', 'gtk-cancel', True),
                    ('confirm', 'Confirm', 'gtk-apply')
                ]
            }
        },
        'confirm' : {
            'actions' : [_confirm],
            'result' : {'type': 'state', 'state': 'end'}
        },
    }

change_participant("training.subscription.line.change.participant")

from osv import osv

class workaround(osv.osv_memory):
    _name = 'wizard.training.subscription.line.change.participant'

    def on_change_job(self, cr, uid, ids, job_id, context=None):
        if job_id:
            values = {
                'new_job_email' : self.pool.get('res.partner.job').browse(cr, uid, job_id, context=context).email
            }

        return {'value' : values}

workaround()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

