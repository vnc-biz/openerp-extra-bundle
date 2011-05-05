# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

class change_participant(osv.osv_memory):
    _name = 'change.participant'
    _columns = {
        'subscription_id': fields.many2one('training.subscription', 'Subscription', readonly=True),
        'subscription_line_id': fields.many2one('training.subscription.line', 'Subscription Line', readonly=True),
        'session_id': fields.many2one('training.session', 'Session', readonly=True),
        'session_date': fields.datetime('Session Date', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'old_job_id': fields.many2one('res.partner.job', 'Participant', readonly=True),
        'new_job_id': fields.many2one('res.partner.job','Participant', required=True),
        'new_job_email': fields.char('Participant Email', size=64),
    }

    def default_get(self, cr, uid, data, context=None):
        if data['id']:
            subscription_line = self.pool.get('training.subscription_line').browse(cr, uid, data['id'], context=context)
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

    def confirm(self, cr, uid, data, context=None):
        old_job_id = data['form']['old_job_id']
        new_job_id = data['form']['new_job_id']
        if old_job_id == new_job_id:
            return {}
        subscription_line = self.pool.get('training.subscription_line').browse(cr, uid, data['id'], context=context)
        if subscription_line.state in ('done', 'cancelled'):
            raise wizard.except_wizard(_('Warning'),
                                       _("You can not select a subscription with the following state: Done or Cancelled"))
        subscription_line.write({'job_id' : new_job_id, 'job_email' : data['form']['new_job_email']})
        return {}

change_participant()

class workaround(osv.osv_memory):
    _name = 'wizard.training.subscription.line.change.participant'

    def on_change_job(self, cr, uid, ids, job_id, context=None):
        if job_id:
            values = {
                'new_job_email' : self.pool.get('res.partner.job').browse(cr, uid, job_id, context=context).email
            }
        return {'value' : values}

workaround()
