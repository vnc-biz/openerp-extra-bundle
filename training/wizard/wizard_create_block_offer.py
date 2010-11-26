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
        'name' : {
            'type' : 'char',
            'size' : 64,
            'string' : 'Name',
            'required' : True,
        },
        'type_id' : {
            'type' : 'many2one',
            'relation' : 'training.course_type',
            'string' : 'Type',
            'required' : True,
        },
        'lang_id' : {
            'type' : 'many2one',
            'relation' : 'res.lang',
            'string' : 'Language',
            'required' : True,
        }
    }

    first_screen_form = '''<?xml version="1.0"?>
    <form string="Create a Block Offer" colspan="4">
        <separator string="Offer Description" colspan="4"/>
        <field name="name" />
        <newline />
        <field name="lang_id" />
        <newline />
        <field name="type_id" />
    </form>'''

    def init(self, cr, uid, data, context=None):
        proxy = pooler.get_pool(cr.dbname).get(data['model'])
        name = None
        languages = set()
        for course in proxy.browse(cr, uid, data['ids'], context=context):
            if course.state_course != 'validated':
                raise wizard.except_wizard(_('Warning'), _("Please, The state of all courses must be 'validated'"))
            if name is None:
                name = course.name
            languages.add(course.lang_id.id)

        if len(languages) > 1:
            raise wizard.except_wizard(_('Warning'), _('You have selected a course with a different language'))

        return {'name' : name, 'lang_id' : list(languages)[0]}

    def create_block_offer(self, cr, uid, data, context=None):
        pool = pooler.get_pool(cr.dbname)

        proxy_offer = pool.get('training.offer')
        offer_id = proxy_offer.create(cr, uid,
                                      {
                                          'name' : data['form']['name'],
                                          'lang_id' : data['form']['lang_id'],
                                          'type_id' : data['form']['type_id'],
                                      },
                                      context=context)

        proxy_course_offer_rel = pool.get('training.course.offer.rel')

        proxy_course = pooler.get_pool(cr.dbname).get(data['model'])

        for course in proxy_course.browse(cr, uid, data['ids'], context=context):
            if course.lang_id.id != data['form']['lang_id']:
                raise wizard.except_wizard(_('Warning'), _("Please, You have selected a course with a different language"))

            proxy_course_offer_rel.create(cr, uid, { 'course_id' : course.id, 'offer_id' : offer_id, }, context=context)

        proxy_offer.write(cr, uid, [offer_id], {'name' : data['form']['name']}, context=context)

        return {
            'res_id' : int(offer_id),
            'name' : 'Offers',
            'view_type' : 'form',
            'view_mode' : 'form,tree',
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
                'state':[('end','Cancel', 'gtk-cancel'),('create_offers', 'Create the Block Offer', 'gtk-apply')],
            }
        },
        'create_offers' : {
            'result' : {
                'type' : 'action',
                'action' : create_block_offer,
                'state' : 'end',
            }
        }
    }

wizard_create_offers('training.course.create.block.offer')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

