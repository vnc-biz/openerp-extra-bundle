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
import tools
from tools.translate import _

class wizard_subscription_session(wizard.interface):
    first_screen_fields = {
        'partner_id' : {
            'string' : 'Partner',
            'type' : 'many2one',
            'relation' : 'res.partner',
            'required' : True,
        },
        'job_ids' : {
            'string' : 'Contacts',
            'type' : 'many2many',
            'relation' : 'res.partner.job',
            'domain' : "[('name', '=', partner_id),('state', '=', 'current')]",
        },
        'line_ids' : {
            'string' : 'Sessions',
            'type' : 'many2many',
            'relation' : 'training.session',
            'domain':"[('state', 'in', ('opened','opened_confirmed'))]"
        }
    }

    first_screen_form = '''<?xml version="1.0"?>
    <form string="Mass Subscription" colspan="6">
        <separator string="Partner" colspan="4" />
        <field name="partner_id" colspan="4" />
        <separator string="Contacts" colspan="4" />
        <field name="job_ids" nolabel="1" colspan="4" />
        <separator string="Sessions" colspan="2" />
        <field name="line_ids" nolabel="1" colspan="4" />
    </form>'''


    def _get_defaults(self, cr, uid, data, context):
        if data['ids']:
            data['form']['line_ids'] = data['ids']
        return data['form']

    def make_subscription(self, cr, uid, data, context=None):
        pool = pooler.get_pool(cr.dbname)

        subscription_proxy = pool.get('training.subscription')
        subscription_line_proxy = pool.get('training.subscription.line')
        partner_id=data['form']['partner_id']
        values = subscription_proxy.on_change_partner(cr, uid, [], partner_id)['value']
        values.update({
                'partner_id' : partner_id,
            })
        if 'address_id' not in values:
            raise wizard.except_wizard(_('Warning'),_("You have selected a partner that has no address."))

        subscription_id = subscription_proxy.create(cr, uid, values, context=context)

        partner = pool.get('res.partner').browse(cr, uid, data['form']['partner_id'], context=context)
        def_pricelist_id = partner.property_product_pricelist.id

        masslines = pool.get('training.subscription.mass.line')
        if data['form']['job_ids']:
            for job_id in data['form']['job_ids'][0][2]:
                for line in data['form']['line_ids']:
                    mlid = line[2]
                    if not isinstance(mlid, (int, long)):
                        for i in line[2]:
                            val={'session_id':i}
                            mlid = masslines.create(cr, uid, val)
                            massline = masslines.browse(cr, uid, mlid, context=context)
                            job = pool.get('res.partner.job').browse(cr, uid, job_id, context=context)
                            values = subscription_line_proxy._get_values_from_wizard(cr, uid, subscription_id, job, massline, context=context)
                            if 'price' not in values:
                                raise wizard.except_wizard(_('Warning'),_("The offer has not a product, so it is not possible to compute the price."))
                            sl_id = subscription_line_proxy.create(cr, uid, values, context=context)

        return {

            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'training.subscription',
            'view_id': pool.get('ir.ui.view').search(cr,uid,[('name','=','training.subscription.form')]),
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id' : int(subscription_id)
        }


    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {
                'type': 'form',
                'arch': first_screen_form,
                'fields': first_screen_fields,
                'state':[('end','Cancel', 'gtk-cancel'),('make_subscription', 'Make Subscription', 'gtk-apply')],
            }
        },
        'make_subscription' : {
            'result' : {
                'type' : 'action',
                'action' : make_subscription,
                'state' : 'end',
            }
        }
    }

wizard_subscription_session('training.subscription.session')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
