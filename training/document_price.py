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

import tools
import netsvc
import decimal_precision as dp
from tools import config
from tools.translate import _

class document_price_component(osv.osv):
    _name = 'document.price.component'

    def price_by_product(self, cr, uid, ids, pricelist, product_id, qty=0, partner_id=False):
        if not product_id:
            return 0.0
        if not pricelist:
            raise osv.except_osv(_('No Pricelist !'),
                _('You have to select a pricelist in the sale form !\n' \
                'Please set one before choosing a product.'))

        price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], product_id, qty or 1.0, partner_id)[pricelist]
        if price is False:
            raise osv.except_osv(_('No valid pricelist line found !'),
                _("Couldn't find a pricelist line matching this product" \
                " and quantity.\nYou have to change either the product," \
                " the quantity or the pricelist."))
        return price

    def _price_compute(self, cr, uid, ids, fieldnames, args, context=None):
        user_proxy = self.pool.get('res.users')
        user = user_proxy.browse(cr, uid, uid, context=context)
        try:
            price_list = user.company_id.partner_id.property_product_pricelist_purchase.id
        except:
            ids = self.pool.get('product.pricelist').search(cr, uid, [('key', '=', 'purchase')])
            price_list = ids[0]

        prices = dict.fromkeys(ids, 0.0)
        product_proxy = self.pool.get('product.product')
        for component in self.browse(cr, uid, ids, context=context):
            prices[component.id] += (
                self.price_by_product(cr, uid, [],
                                      price_list,
                                      component.product_id.id,
                                      component.product_qty,
                                      user.company_id.partner_id.id) * component.product_qty
            )

        return prices

    _columns = {
        'attach_id' : fields.many2one('ir.attachment', 'Document', required=True, ondelete="cascade"),
        'product_qty' : fields.integer('Quantity', required=True),
        'product_id' : fields.many2one('product.product', 'Product', required=True),
        'unit_price' : fields.related('product_id', 'standard_price', type='float', string='Unit Price', digits_compute=dp.get_precision('Account')),
        'price' : fields.function(_price_compute, method=True, type='float', string='Price',
                                  digits_compute=dp.get_precision('Account')
                                 ),
    }

    _defaults = {
        'product_qty' : lambda *a: 1,
    }

document_price_component()


class document_price(osv.osv):
    _inherit = 'ir.attachment'

    def _price_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0.0)

        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = reduce(lambda acc, component: acc + component.price,
                                 obj.component_ids,
                                 0.0)

        return res

    _columns = {
        'component_ids' : fields.one2many('document.price.component', 'attach_id'),

        'price' : fields.function(_price_compute, method=True,
                                  digits_compute=dp.get_precision('Account'),
                                  string='Price',
                                  type='float'),
        'is_support' : fields.boolean('Support'),
        'state' : fields.selection( [ ('draft', 'Draft'), ('validated', 'Validated'), ('pending', 'Pending') ], 'State', select=1, readonly=True),
        'support_note' : fields.text('Note'),
    }

    _defaults = {
        'is_support' : lambda *a: 0,
        'state' : lambda *a: 'draft',
    }

    def search(self, cr, uid, domain, offset=0, limit=None, order=None, context=None, count=False):
        link_course_ids = context and context.get('course_ids', False) or False

        if link_course_ids:
            course_ids = [course[2]['course_id'] for course in link_course_ids]
            return super(document_price, self).search(cr, uid, [('is_support', '=', 1),
                                                                ('res_model', '=', 'training.course'),
                                                                ('res_id', 'in', course_ids)])

        return super(document_price, self).search(cr, uid, domain, offset=offset,
                                                  limit=limit, order=order, context=context, count=count)

document_price()

