# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Raimon Esteve <resteve@zikzakmedia.com>
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

import decimal_precision as dp

class training_subscription(osv.osv):
    _inherit = 'training.subscription'

    def onchange_payment_id(self, cr, uid, ids, payment_id, context=None):
        res = False
        payment_term_id = False

        if payment_id:
            training_payment_ids = self.pool.get('training.payment').search(cr, uid, [('payment_id','=',payment_id)])
            if len(training_payment_ids) > 0:
                training_payment = self.pool.get('training.payment').browse(cr, uid, training_payment_ids[0])
                payment_term_id = training_payment.payment_term_id.id

        result = {'value': {
            'payment_term_id': payment_term_id,
            }
        }
        return result

    _columns = {
        'payment_id': fields.many2one('payment.type', 'Payment', required=True),
        'esale_payment': fields.float('e-sale Payment', digits_compute=dp.get_precision('Sale Price'), readonly=True),
    }

training_subscription()
