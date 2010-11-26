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
class wizard_subscription_second_line(wizard.interface):
    first_screen_fields = { }
    first_screen_form = '''<?xml version="1.0"?>
    <form string="Mass Subscription Second Line" colspan="6">
       <label string="This wizard will generate the subscription !" />

    </form>'''

    def make_subscription(self, cr, uid, data, context=None):

        subscription_line_second_ids = data['ids']

        if not subscription_line_second_ids:
            return {}

        pool=pooler.get_pool(cr.dbname)
        sls_proxy = pool.get('training.subscription.line.second')
        subscription_proxy= pool.get('training.subscription')
        subscription_line_proxy = pool.get('training.subscription.line')

        partners = {}

        for sls in sls_proxy.browse(cr, uid, subscription_line_second_ids, context=context):
            if sls.partner_id:
                partners.setdefault(sls.partner_id.id, []).append(sls)

        for partner_id, lines in partners.iteritems():
            values = subscription_proxy.on_change_partner(cr, uid, [], partner_id)['value']
            values.update({
                'partner_id' : partner_id,
            })
            subscription_id = subscription_proxy.create(cr, uid, values, context=context)

            for line in lines:
                subscription_line_proxy.create(cr, uid, {'subscription_id' : subscription_id,
                                                         'session_id' : line.session_id.id,
                                                         'contact_id' : line.job_id.id,
                                                        },
                                               context=context)

                line.unlink()

        return {}

    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': first_screen_form,
                'fields': first_screen_fields,
                'state':[('end','Cancel', 'gtk-cancel'),('make_subscription', 'Make Subscription', 'gtk-apply')],
            }
        },
        'make_subscription' : {
            'actions': [ make_subscription ],
            'result' : {
                'type' : 'state',
                'state' : 'end',
            }
        }
    }

wizard_subscription_second_line('training.subscription.line_second')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
