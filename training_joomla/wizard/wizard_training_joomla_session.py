# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
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

from osv import fields,osv
from tools.translate import _
import xmlrpclib
import export_table
import time

class joomla_session_wizard(osv.osv_memory):
    _name = 'training.joomla.session.wizard'

    _columns = {
        'session_new': fields.integer('Session New', readonly=True),
        'session_update': fields.integer('Session Update', readonly=True),
        'session_delete': fields.integer('Session Delete', readonly=True),
        'd_from': fields.date('From', required=True),
        'd_to': fields.date('To'),
        'state':fields.selection([
            ('first','First'),
            ('done','Done'),
        ],'State'),
    }

    _defaults = {
        'state': lambda *a: 'first',
        'd_from': lambda *a: time.strftime('%Y-%m-%d')
    }

    def _export_fields(self):
        return ['id', 'address_id', 'date_end', 'min_limit_reached', 'date', 'participant_count_manual', 'format_id', 'name', 'manual', 'catalog_id', 'offer_id', 'alias', 'metakey', 'metadescription']

    def export_sessions(self, cr, uid, ids, data, context={}):
        """Export (synchronize) the training sessions to Joomla PHP server."""
        web_ids = self.pool.get('training.joomla').search(cr, uid, [('active','=',True)])
        websites = self.pool.get('training.joomla').browse(cr, uid, web_ids, context)

        form = self.browse(cr, uid, ids[0])
        d_from = form.d_from
        d_to = form.d_to

        if websites:
            for website in websites:
                location = website.location
                username = website.username
                password = website.password

                if not location[-1] == '/':
                    location += '/'

                server = xmlrpclib.ServerProxy(location + "xmlrpc/index.php")

                # session
                filter = []
                filterphp = ''

                if website.session_draft:
                    filter.append(('state','=','draft'))
                if website.session_opened:
                    filter.append(('state','=','opened'))
                if website.session_opened_confirmed:
                    filter.append(('state','=','opened_confirmed'))
                if website.session_closed_confirmed:
                    filter.append(('state','=','closed_confirmed'))
                if website.session_inprogress:
                    filter.append(('state','=','inprogress'))
                if website.session_closed:
                    filter.append(('state','=','opened_closed'))
                if website.session_cancelled:
                    filter.append(('state','=','cancelled'))

                for i in range(len(filter)-1):
                    filter.insert(0, '|')

                if d_from:
                    filter.append(('date', '>=', d_from + ' 00:00:00'))
                    filterphp += " date >= '" + d_from + " 00:00:00'"
                if d_to:
                    filter.append(('date_end', '<=', d_to + ' 23:59:59'))
                    filterphp += " AND date_end <= '" + d_to + " 23:59:59'"

                (session_new, session_update, session_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'training.session', self._export_fields(), filter, filterphp)

                values = {
                    'state':'done',
                    'session_new':session_new,
                    'session_update':session_update,
                    'session_delete':session_delete,
                }
                self.write(cr, uid, ids, values)
        else:
            raise osv.except_osv(_('Error!'), _('No Joomla! location defined!\nPlease create one.'))

        return True

joomla_session_wizard()
