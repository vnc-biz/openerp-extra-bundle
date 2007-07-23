##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: mrp.py 1292 2005-09-08 03:26:33Z pinky $
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields
from osv import osv
import ir

import netsvc
import time
from mx import DateTime
from tools.misc import currency


import account
from account import invoice

class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def amount_payed(self, cr, uid, ids, name, arg, context):
        cr.execute("select invoice_id,sum(l.amount) from payment_line l inner join payment_order o on l.order_id=o.id and o.state='done' and l.invoice_id in (%s) group by invoice_id;"% (",".join(map(str,ids))))
        res3=cr.fetchall()
        amt_paid=dict(res3)
        return amt_paid

    def amount_to_pay(self, cr, uid, ids, name, arg, context):
        total=self._amount_total(cr, uid, ids, name, arg, context)
        cr.execute("SELECT invoice_id, sum(amount) from payment_line l inner join payment_order o on l.order_id=o.id and l.invoice_id in (%s)group by invoice_id;"% (",".join(map(str,ids))))
        res=cr.fetchall()
        res1=dict(res)
        for i in res1:
            total[i] -= res1[i]
        return total
    _columns = {
        'amount_pay' : fields.function(amount_payed, method=True, type='float', string='Amount paid'),
        'amount_to_pay' : fields.function(amount_to_pay, method=True, type='float', string='Amount to pay'),
                }
account_invoice()

class payment_type(osv.osv):
    _name = 'payment.type'
    _description = 'Payment type'
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('code', size=64, required=True),
                }
payment_type()

class payment_order(osv.osv):
    _name = 'payment.order'
    _description = 'Payment Order'

    def type_get(self, cr, uid, context={}):
        pay_type_obj = self.pool.get('payment.type')
        ids = pay_type_obj.search(cr, uid, [])
        res = pay_type_obj.read(cr, uid, ids, ['code','name'], context)
        return [(r['code'],r['name']) for r in res]
    _defaults = {
             'state': lambda *a: 'draft',
       }

    _columns = {
        'name': fields.char('payment Name',size=64),
        'type': fields.selection(type_get, 'Payment Type',required=True),
        'state': fields.selection([('draft', 'Draft'),('done','Done')], 'State'),
        'payment_line': fields.one2many('payment.line','order_id','Payment Lines')

    }

payment_order()

class payment_line(osv.osv):
    _name = 'payment.line'
    _description = 'Payment Line'
    _columns = {
        'order_id': fields.many2one('payment.order','Order', ondelete='cascade', select=True),
        'name': fields.char('Payment Name', size=64),
        'invoice_id': fields.many2one('account.invoice','Payment Invoice',required=True),
        'amount': fields.float('Payment Amount', digits=(16,4)),
     }
payment_line()
