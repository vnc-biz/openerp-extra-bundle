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

from osv import osv
from osv import fields
from tools.translate import _
import netsvc

class training_create_offer(osv.osv_memory):
    _name = 'training.create.offer'
    _columns = {
        'format_id' : fields.many2one('training.offer.format', 'Format', required=True,),
        'product_id' : fields.many2one('product.product', 'Product'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        if context.get('active_id',False):
            course = self.pool.get('training.course').browse(cr, uid, context.get('active_id',[]), context=context)
            if course.state_course != 'validated':
                raise osv.except_osv(_('Warning'),_("Please, you can create an offer with a validated course"))

        return {}

    def create_offers(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        workflow = netsvc.LocalService('workflow')
        proxy = self.pool.get('training.offer')
        offer_ids = []
        form = self.read(cr, uid, ids, [], context=context)[0]
        for course in self.pool.get('training.course').browse(cr, uid, context.get('active_ids',[]), context):
            if course.state_course == 'validated':
                offer_id = proxy.create(cr, uid,
                    {
                        'name' : course.name,
                        'lang_id' : course.lang_id.id,
                        'type_id' : course.course_type_id.id,
                        'product_line_id': course.category_id.id,
                        'format_id' : form['format_id'],
                        'product_id' : form['product_id'],
                    },
                    context=context)
                self.pool.get('training.course.offer.rel').create(cr, uid, {'offer_id' : offer_id, 'course_id' : course.id}, context=context)
                #workflow.trg_validate(uid, 'training.offer', offer_id, 'signal_validate', cr)
                offer_ids.append(offer_id)
        number_of_offers = len(offer_ids)
        if not number_of_offers:
            return {}
        elif number_of_offers == 1:
            return {
                'res_id' : int(offer_ids[0]),
                'name' : 'Offers',
                'view_type' : 'form',
                'view_mode' : 'form,tree',
                'res_model' : 'training.offer',
                'view_id' : False,
                'type' : 'ir.actions.act_window',
            }
        else:
            return {
                'domain' : "[('id', 'in', [%s])]" % ','.join(map(str,offer_ids)),
                'name' : 'Offers',
                'view_type' : 'form',
                'view_mode' : 'tree,form',
                'res_model' : 'training.offer',
                'view_id' : False,
                'type' : 'ir.actions.act_window',
            }

training_create_offer()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
