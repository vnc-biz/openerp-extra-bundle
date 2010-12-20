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

class joomla_images_wizard(osv.osv_memory):
    _name = 'training.joomla.images.wizard'

    _columns = {
        'images_new': fields.integer('Images New', readonly=True),
        'images_update': fields.integer('Images Update', readonly=True),
        'images_delete': fields.integer('Images Delete', readonly=True),
        'state':fields.selection([
            ('first','First'),
            ('done','Done'),
        ],'State'),
    }

    _defaults = {
        'state': lambda *a: 'first',
    }

    def _export_fields(self):
        return ['id', 'name','base_image','filename','comments','offer_id']

    def export_images(self, cr, uid, ids, data, context={}):
        """Export (synchronize) the training images to Joomla PHP server."""
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

                # images
                filter = []
                filterphp = ''

                (images_new, images_update, images_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'training.images', self._export_fields(), filter, filterphp)

                values = {
                    'state':'done',
                    'images_new':images_new,
                    'images_update':images_update,
                    'images_delete':images_delete,
                }
                self.write(cr, uid, ids, values)
        else:
            raise osv.except_osv(_('Error!'), _('No Joomla! location defined!\nPlease create one.'))

        return True

joomla_images_wizard()
