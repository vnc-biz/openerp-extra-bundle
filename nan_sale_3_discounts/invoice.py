# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2011  NaN Projectes de Programari Lliure S.L.
#                   (http://www.nan-tic.com) All Rights Reserved.
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

from datetime import datetime
from osv import osv, fields
from tools.translate import _
import netsvc
import time
import tools

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    def _get_discount(self, cr, uid, ids, field_name, field_value, context):
        result = {}
        for line in self.browse(cr,uid,ids,context=context):
            value = 100*(1 - ( (100-line.discount1)/100 *(100-line.discount2)/100 * (100-line.discount3)/100 ))
            result[line.id] = value
        return result

    _columns = {
        'discount': fields.function(_get_discount, method=True, type="float", store={
            'sale.order.line': (lambda self, cr, uid, ids, context=None: ids, ['discount1','discount2','discount3'], 1),
        }, digits=(10,2), string='Calculated discount'),
        'discount1': fields.float('Discount 1', digits=(10,2)),
        'discount2': fields.float('Discount 2', digits=(10,2)),
        'discount3': fields.float('Discount 3', digits=(10,2)),
    }

account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
