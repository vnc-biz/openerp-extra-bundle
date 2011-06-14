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
import pooler
import time
import tools
from tools.translate import _

class training_session_create_wizard(osv.osv_memory):
    _name = 'training.session.create.wizard'

    _columns = {
        'date': fields.datetime('Date', required=True),
        'name': fields.char('Name', size=64, required=True),
    }

    def _default_get_name(self, cr, uid, context=None):
        if context is None:
            return ''
        active_id = context.get('active_id')
        if not active_id:
            return ''
        offer = self.pool.get('training.offer').browse(cr, uid, active_id, context=context)
        return offer.name

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d 08:30:00'),
        'name': _default_get_name,
    }

    def create_session(self, cr, uid, ids, context=None):
        session_ids = []
        pool = pooler.get_pool(cr.dbname)
        proxy = pool.get('training.offer')
        offer = proxy.browse(cr, uid, context['active_id'], context=context)
        for form in self.read(cr, uid, ids, [], context=context):
            if not offer.can_be_planned:
                raise osv.except_osv(_('Warning'), _("You can not create a session with a non-validated offer") )

            proxy = pool.get('training.session')
            session_id = proxy.create(cr, uid,
                                      {
                                          'offer_id' : form['id'],
                                          'date' : form['date'],
                                          'name' : "%s (%s)" % (form['name'], time.strftime("%Y-%m-%d", time.strptime(form['date'], '%Y-%m-%d %H:%M:%S'))),
                                          'format_id' : offer.format_id.id,
                                      }
                                     )
            vals = proxy.on_change_offer(cr, uid, None, context['active_id'])
            if isinstance(vals, dict):
                # we have specified a custom name on session creation,
                # don't let on_change overwrite it now.
                try:
                    if 'name' in vals['value']:
                        del vals['value']['name']
                except KeyError:
                    pass
                proxy.write(cr, uid, [session_id], vals['value'], context=context)
            session_ids.append(session_id)
        number_of_sessions = len(session_ids)
        if not number_of_sessions:
            return {}
        elif number_of_sessions == 1:
            return {
                'res_id': int(session_ids[0]),
                'name': 'Sessions',
                'view_type': 'form',
                "view_mode": 'form,tree',
                'res_model': 'training.session',
                'view_id': pool.get('ir.ui.view').search(cr,uid,[('name','=','training.session.form')]),
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
        else:
            return {
                'domain' : "[('id', 'in', [%s])]" % ','.join(map(str,session_ids)),
                'name' : 'Sessions',
                'view_type' : 'form',
                'view_mode' : 'tree,form',
                'res_model' : 'training.session',
                'view_id' : False,
                'type' : 'ir.actions.act_window',
                'target': 'current',
            }

training_session_create_wizard()
