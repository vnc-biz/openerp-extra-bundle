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

from osv import osv
from osv import fields
from tools.translate import _

class training_create_block_offer(osv.osv_memory):
    _name = 'training.create.block.offer'
    _columns = {
        'name' : fields.char('Name', size=64, required=True),
        'type_id' : fields.many2one('training.course_type', 'Type', required=True,),
        'lang_id' : fields.many2one('res.lang', 'Language', required=True,),
        'format_id' : fields.many2one('training.offer.format', 'Format', required=True,),
        'product_line_id' : fields.many2one('training.course_category', 'Product Line', required=True),
        'product_id' : fields.many2one('product.product', 'Product'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        if not context.get('active_model'):
            return {}
        proxy = self.pool.get(context.get('active_model'))
        languages = set()
        result = {'name': None}
        for course in proxy.browse(cr, uid, context.get('active_ids', []), context=context):
            if course.state_course != 'validated':
                raise osv.except_osv(_('Warning'), _("Please, The state of all courses must be 'validated'"))
            if result.get('name',None) is None:
                result.update({'name': course.name})
            result.update({
                           'product_line_id': course.category_id and course.category_id.id or False,
                           'type_id': course.course_type_id and course.course_type_id.id or False,
                           })
            languages.add(course.lang_id.id)
        if len(languages) > 1:
            raise osv.except_osv(_('Warning'), _('You have selected a course with a different language'))
        result.update({'lang_id': list(languages)[0]})
        return result

    def create_block_offer(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        proxy_offer = self.pool.get('training.offer')
        proxy_course_offer_rel = self.pool.get('training.course.offer.rel')
        active_model = context.get('active_model', False)
        if not active_model:
            return {}
        proxy_course = self.pool.get(active_model)
        form = self.read(cr, uid, ids, [], context=context)[0]
        offer_id = proxy_offer.create(cr, uid,
            {
                'name' : form['name'],
                'lang_id' : form['lang_id'],
                'type_id' : form['type_id'],
                'format_id' : form['format_id'],
                'product_line_id': form['product_line_id'],
                'product_id': form['product_id'],
            },
            context=context)
        for course in proxy_course.browse(cr, uid, context.get('active_ids',[]), context=context):
            if course.lang_id.id != form['lang_id']:
                raise osv.except_osv(_('Warning'), _("Please, You have selected a course with a different language"))
            proxy_course_offer_rel.create(cr, uid, { 'course_id' : course.id, 'offer_id' : offer_id }, context=context)
        proxy_offer.write(cr, uid, [offer_id], {'name' : form['name']}, context=context)
        return {
            'res_id' : int(offer_id),
            'name' : 'Offers',
            'view_type' : 'form',
            'view_mode' : 'form,tree',
            'res_model' : 'training.offer',
            'view_id' : False,
            'type' : 'ir.actions.act_window',
        }

training_create_block_offer()
