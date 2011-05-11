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

import netsvc

class training_payment(osv.osv):
    _name = 'training.payment'
    _description = 'Training Payment'

    """
    values
		"reference" => array($reference, "string"),
		"payment" => array($payment, "string"),
        "payment_amount" => array($_SESSION['total'], "string"),
    """
    def check_payment(self, cr, uid, values, context):
        ids = self.search(cr, uid, [('name','=',values['payment'])])

        if len(ids):
            training_payment = self.browse(cr, uid, ids[0])
            subscription_ids = self.pool.get('training.subscription').search(cr, uid, [('name','=',values['reference'])])

            if len(subscription_ids) > 0:
                values = {
                    'payment_id':training_payment.payment_id.id,
                    'esale_payment':float(values['payment_amount']),
                    'payment_term_id':training_payment.payment_term_id.id,
                }

                self.pool.get('training.subscription').write(cr, uid, subscription_ids, values)

                #change state subscription. NOT subscription.lines
                subscription =  self.pool.get('training.subscription').browse(cr, uid, subscription_ids[0])
                if training_payment.state == 'confirmed':
                    self.pool.get('training.subscription').action_workflow_confirm(cr, uid, subscription_ids, context)
                return True
            else:
                return False
        else:
            return False
    
    _columns = {
        'name': fields.char('Code', size=64, required=True),
        'payment_id': fields.many2one('payment.type', 'Payment', required=True),
        'payment_term_id' : fields.many2one('account.payment.term', 'Payment Term', required=True),
        'state' : fields.selection([('draft', 'Draft'),('confirmed','Confirmed')], 'State', required=True, help='Workfow to change the Subscription with this payment.'),
    }

    _defaults = {
        'state' : lambda *a: 'draft',
    }

training_payment()
