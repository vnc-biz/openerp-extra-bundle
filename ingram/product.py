# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jesús Martín <jmartin@zikzakmedia.com>
#                       Raimon Esteve <resteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from osv import osv, fields
from tools.translate import _

from osv import osv
from osv import fields

class product_category(osv.osv):
    _inherit = 'product.category'
    
    _columns = {
        'ingram_code':fields.char('Ingram Code', size=64, readonly=True),
    }

product_category()

class product_product(osv.osv):
    _inherit = 'product.product'
    
    _columns = {
        'ingram_sku':fields.char('Ingram SKU', size=64, readonly=True), #need this field when search product.product = product.template
        'ean13_upc':fields.char('Ingram EAN/UPC', size=64, readonly=True),
    }

product_product()
