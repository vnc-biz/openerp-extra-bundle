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

class partner(osv.osv):
    _inherit = 'res.partner'
    _description = 'Partner with Last Reconcile Date'
    _columns = {
        'last_reconciliation_date': fields.datetime('Last Reconcilation Date', help='Date on which partner account entries reconciled last time')
                }

partner()

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    _description = 'Account Move Line'

    def reconcile(self, cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context={}):
        res = super(account_move_line, self).reconcile(cr, uid, ids, type, writeoff_acc_id, writeoff_period_id, writeoff_journal_id, context=context)
        lines = self.browse(cr, uid, ids, context=context)
        if lines and lines[0]:
            partner_id = lines[0].partner_id.id
            if context and context.get('stop_reconcile', False):
                self.pool.get('res.partner').write(cr, uid, [partner_id], {'last_reconciliation_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return res

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context and context.get('next_partner_only', False):
            cr.execute(
                    """
SELECT p.id
FROM res_partner p
RIGHT JOIN (
         SELECT l.partner_id as partner_id, SUM(l.debit) as debit, SUM(l.credit) as credit
         FROM account_move_line l
          LEFT JOIN account_account a ON (a.id = l.account_id)
          LEFT JOIN res_partner p ON (l.partner_id = p.id)
         WHERE a.reconcile IS TRUE
          AND l.reconcile_id IS NULL
          AND (p.last_reconciliation_date IS NULL OR l.date > p.last_reconciliation_date)
          AND l.state <> 'draft'
         GROUP BY l.partner_id
) AS s ON (p.id = s.partner_id)
ORDER BY p.last_reconciliation_date LIMIT 1"""
                     )
            partner = cr.fetchone()
            if not partner:
                return []
            args.append(('partner_id', '=', partner[0]))
        return super(account_move_line, self).search(cr, user, args, offset, limit, order, context, count)

account_move_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
