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
import time
import tools
from tools.translate import _

class wizard_create_session(wizard.interface):
    first_screen_fields = {
        'date' : {
            'string' : 'Date',
            'type' : 'datetime',
            'required' : True,
            'default' : time.strftime('%Y-%m-%d 08:30:00'),
        },
        'name' : {
            'string' : 'Name',
            'type' : 'char',
            'required' : True,
            'size' : 64,
        }
    }

    first_screen_form = '''<?xml version="1.0"?>
    <form string="Plannify Session" colspan="2">
        <label string="Can you select a date for the session ?" colspan="2" />
        <newline />
        <field name="name" />
        <newline />
        <field name="date" />
    </form>'''

    def create_session(self, cr, uid, data, context=None):
        pool = pooler.get_pool(cr.dbname)
        proxy = pool.get('training.offer')
        offer = proxy.browse(cr, uid, data['id'], context=context)

        if not offer.can_be_planned:
            raise wizard.except_wizard(_('Warning'),
                                       _("You can not create a session with a non-validated offer"))


        proxy = pool.get('training.session')
        session_id = proxy.create(cr, uid,
                                  {
                                      'offer_id' : data['id'],
                                      'date' : data['form']['date'],
                                      'name' : "%s (%s)" % (data['form']['name'], time.strftime("%Y-%m-%d", time.strptime(data['form']['date'], '%Y-%m-%d %H:%M:%S'))),
                                      'format_id' : offer.format_id.id,
                                  }
                                 )
        vals = proxy.on_change_offer(cr, uid, None, data['id'])
        if isinstance(vals, dict):
            # we have specified a custom name on session creation,
            # don't let on_change overwrite it now.
            try:
                if 'name' in vals['value']:
                    del vals['value']['name']
            except KeyError:
                pass
            proxy.write(cr, uid, [session_id], vals['value'], context=context)

        return {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'training.session',
            'view_id': pool.get('ir.ui.view').search(cr,uid,[('name','=','training.session.form')]),
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id' : int(session_id),
        }

    def init(self, cr, uid, data, context=None):
        if data['id']:
            offer = pooler.get_pool(cr.dbname).get(data['model']).browse(cr, uid, data['id'])
            if offer.state != 'validated':
                raise wizard.except_wizard(_('Warning'),
                                           _("Please, you can create a session with a validated offer"))
            return {'name' : offer.name}

    states = {
        'init': {
            'actions': [init],
            'result': {
                'type': 'form',
                'arch': first_screen_form,
                'fields': first_screen_fields,
                'state':[('end','Cancel', 'gtk-cancel'),('create_session', 'Create Session', 'gtk-apply')],
            }
        },
        'create_session' : {
            'result' : {
                'type' : 'action',
                'action' : create_session,
                'state' : 'end',
            }
        }
    }

wizard_create_session('training.offer.create.session')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
