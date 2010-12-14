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

import wizard
import pooler
import netsvc
import tools
from tools.translate import _

class wizard_create_offers(wizard.interface):
    first_screen_fields = {
        'format_id' : {
            'string' : 'Format',
            'type' : 'many2one',
            'relation' : 'training.offer.format',
            'required' : True,
            'help' : "Delivery format of the course",
        },
    }

    first_screen_form = '''<?xml version="1.0"?>
    <form string="Create Offers" colspan="6">
        <label string="Do you want to create an offer for each selected course ?" colspan="2" />
        <newline/>
        <field name="format_id" />
    </form>'''

    def init(self, cr, uid, data, context=None):
        if data['id']:
            course = pooler.get_pool(cr.dbname).get(data['model']).browse(cr, uid, data['id'])
            if course.state_course != 'validated':
                raise wizard.except_wizard(_('Warning'),_("Please, you can create an offer with a validated course"))
        return {}

    def create_offers(self, cr, uid, data, context=None):
        workflow = netsvc.LocalService('workflow')
        pool = pooler.get_pool(cr.dbname)
        proxy = pool.get('training.offer')
        offer_ids = []
        for course in pool.get('training.course').browse(cr, uid, data['ids'], context=context):
            if course.state_course == 'validated':
                offer_id = proxy.create(cr, uid,
                                        {
                                            'name' : course.name,
                                            'lang_id' : course.lang_id.id,
                                            'type_id' : course.course_type_id.id,
                                            'product_line_id': course.category_id.id,
                                            'format_id' : data['form']['format_id'],
                                        },
                                        context=context)

                pool.get('training.course.offer.rel').create(cr, uid, {'offer_id' : offer_id, 'course_id' : course.id}, context=context)
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


    states = {
        'init': {
            'actions': [init],
            'result': {
                'type': 'form',
                'arch': first_screen_form,
                'fields': first_screen_fields,
                'state':[('end','Cancel', 'gtk-cancel'),('create_offers', 'Create Offers', 'gtk-apply')],
            }
        },
        'create_offers' : {
            'result' : {
                'type' : 'action',
                'action' : create_offers,
                'state' : 'end',
            }
        }
    }

wizard_create_offers('training.course.create.offer')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
