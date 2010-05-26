# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time

from osv import osv, fields
from tools.translate import _

class account_partner_reconcile_process(osv.osv_memory):
    _name = 'account.partner.reconcile.process'
    _description = 'Reconcilation Process partner by partner'

    def _get_to_reconcile(self, cr, uid, context=None):
        cr.execute(
                "SELECT l.partner_id " \
                "FROM account_move_line as l join res_partner p on p.id=l.partner_id " \
                "WHERE l.reconcile_id IS NULL " \
                "AND (%s >  to_char(p.last_reconciliation_date, 'YYYY-MM-DD') " \
                "OR  p.last_reconciliation_date IS NULL ) " \
                "AND l.state <> 'draft' " \
                "GROUP BY l.partner_id, p.last_reconciliation_date " \
                "ORDER BY p.last_reconciliation_date",(time.strftime('%Y-%m-%d'),)
                  )
        return len(map(lambda x: x[0], cr.fetchall()))

    def _get_today_reconciled(self, cr, uid, context=None):
        cr.execute(
                "SELECT l.partner_id " \
                "FROM account_move_line as l join res_partner p on p.id=l.partner_id " \
                "WHERE l.reconcile_id IS NULL " \
                "AND %s =  to_char(p.last_reconciliation_date, 'YYYY-MM-DD') " \
                "AND l.state <> 'draft' " \
                "GROUP BY l.partner_id, p.last_reconciliation_date " \
                "ORDER BY p.last_reconciliation_date",(time.strftime('%Y-%m-%d'),)
                  )
        return len(map(lambda x: x[0], cr.fetchall()))

    def _get_partner(self, cr, uid, context=None):
        cr.execute(
                "SELECT l.partner_id " \
                "FROM account_move_line as l join res_partner p on p.id=l.partner_id " \
                "WHERE l.reconcile_id IS NULL " \
                "AND (l.date_created >  p.last_reconciliation_date " \
                "OR p.last_reconciliation_date IS NULL )" \
                "AND l.state <> 'draft' " \
                "GROUP BY l.partner_id, p.last_reconciliation_date " \
                "ORDER BY p.last_reconciliation_date"
                 )
        partner = cr.fetchone()
        if not partner:
            return False
        return partner[0]

    def data_get(self, cr, uid, to_reconcile, today_reconciled, context=None):
        return {'progress': (100 / float(to_reconcile + today_reconciled)) * today_reconciled}

    def default_get(self, cr, uid, fields, context=None):
        res = super(account_partner_reconcile_process, self).default_get(cr, uid, fields, context=context)
        if 'to_reconcile' in res and 'today_reconciled' in res:
            data = self.data_get(cr, uid, res['to_reconcile'], res['today_reconciled'], context)
            res.update(data)
        return res

    def do_reconcile(self, cr, uid, ids, context):
        if self.read(cr, uid, ids, ['stop_reconcile'], context=context)[0]['stop_reconcile']:
            context.update({'stop_reconcile': True})
        return self.pool.get('account.move.line.reconcile').partial_check(cr, uid, ids, context)
#        move_line_obj = self.pool.get('account.move.line')
#        data_old = self.read(cr, uid, ids, ['partner_id', 'to_reconcile', 'today_reconciled'], context=context)
#        data = self.read(cr, uid, ids, ['journal_id', 'writeoff_acc_id', 'analytic_id', 'comment', 'date_p'], context=context)
#        args = [('account_id.reconcile', '=', True), ('partner_id', '=', data_old[0]['partner_id']), ('reconcile_id', '=', False)]
#        line_ids = move_line_obj.search(cr, uid, args, context=context)
#        ids_p = self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'), context=context)
#        if len(ids_p):
#            period_id = ids_p[0]
#
#        context.update({'date_p': data[0]['date_p']})
#        data_old = self.read(cr, uid, ids, ['partner_id', 'to_reconcile', 'today_reconciled', 'progress'], context=context)
#        move_line_obj.reconcile(cr, uid, line_ids, 'manual', data[0]['writeoff_acc_id'], period_id, data[0]['journal_id'], context=context)
#        progress = self.data_get(cr, uid, data_old[0]['to_reconcile']-1, data_old[0]['today_reconciled']+1, context)
#        partner = self._get_partner(cr, uid, context)
#        vals = {'progress': progress['progress'], 'today_reconciled': int(data_old[0]['today_reconciled'])+1, 'to_reconcile': int(data_old[0]['to_reconcile'])-1, 'partner_id': partner}
#        self.write(cr, uid, context['ids'], vals)
#        return {}
#
#    def reconcile(self, cr, uid, ids, context=None):
#        mod_obj = self.pool.get('ir.model.data')
#        data = self.read(cr, uid, ids, ['partner_id', 'to_reconcile', 'today_reconciled', 'progress'], context=context)
#        if not data[0]['partner_id']:
#            return True
#        context.update({'partner_id': data[0]['partner_id'], 'ids':ids})
#        model_data_ids = mod_obj.search(cr,uid,[('model','=','ir.ui.view'),('name','=','account_partner_reconcile_view_writeoff')], context=context)
#        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
#        return {
#            'name': _('Write off entry'),
#            'context': context,
#            'view_type': 'form',
#            'view_mode': 'form',
#            'res_model': 'account.partner.reconcile.process',
#            'views': [(resource_id, 'form')],
#            'type': 'ir.actions.act_window',
#            'target': 'new',
#            'nodestroy': True
#        }

    _columns = {
        'to_reconcile': fields.float('Remaining Partners to Reconcile', readonly=True),
        'today_reconciled': fields.float('Partners Reconciled Today', readonly=True),
        'progress': fields.float('Progress', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Next Partner to Reconcile', readonly=True),
        #write off fields
        'stop_reconcile': fields.boolean('Go to next partner'),
                }
    _defaults = {
         'to_reconcile': _get_to_reconcile,
         'today_reconciled': _get_today_reconciled,
         'partner_id': _get_partner,
                 }

account_partner_reconcile_process()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
