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

class joomla_offer_wizard(osv.osv_memory):
    _name = 'training.joomla.offer.wizard'

    _columns = {
        'offer_new': fields.integer('Offer New', readonly=True),
        'offer_update': fields.integer('Offer Update', readonly=True),
        'offer_delete': fields.integer('Offer Delete', readonly=True),
        'state':fields.selection([
            ('first','First'),
            ('done','Done'),
        ],'State'),
    }

    _defaults = {
        'state': lambda *a: 'first',
    }

    def _export_fields(self):
        return ['id', 'description', 'type_id', 'requeriments', 'management', 'notification_note', 'target_public_id', 'format_id', 'kind', 'name', 'product_line_id', 'sequence', 'lang_id', 'objective', 'target_public_id', 'product_id', 'is_certification', 'course_course_id_ids', 'preliminary_offer_ids', 'complementary_offer_ids', 'included_offer_ids', 'theme_ids', 'alias', 'metakey', 'metadescription', 'frontpage']

    def export_offers(self, cr, uid, ids, data, context={}):
        """Export (synchronize) the training offers to Joomla PHP server."""
        web_ids = self.pool.get('training.joomla').search(cr, uid, [('active','=',True)])
        websites = self.pool.get('training.joomla').browse(cr, uid, web_ids, context)
        if websites:
            for website in websites:
                location = website.location
                username = website.username
                password = website.password

                if not location[-1] == '/':
                    location += '/'

                server = xmlrpclib.ServerProxy(location + "xmlrpc/index.php")

                # offer
                filter = []
                filterphp = ''

                if website.offer_draft:
                    filter.append(('state','=','draft'))
                if website.offer_deprecated:
                    filter.append(('state','=','deprecated'))
                if website.offer_validated:
                    filter.append(('state','=','validated'))

                for i in range(len(filter)-1):
                    filter.insert(0, '|')

                (offer_new, offer_update, offer_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'training.offer', self._export_fields(), filter, filterphp)

                values = {
                    'state':'done',
                    'offer_new':offer_new,
                    'offer_update':offer_update,
                    'offer_delete':offer_delete,
                }
                self.write(cr, uid, ids, values)
        else:
            raise osv.except_osv(_('Error!'), _('No Joomla! location defined!\nPlease create one.'))

        return True

joomla_offer_wizard()
