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

class joomla_course_wizard(osv.osv_memory):
    _name = 'training.joomla.course.wizard'

    _columns = {
        'course_new': fields.integer('Course New', readonly=True),
        'course_update': fields.integer('Course Update', readonly=True),
        'course_delete': fields.integer('Course Delete', readonly=True),
        'state':fields.selection([
            ('first','First'),
            ('done','Done'),
        ],'State'),
    }

    _defaults = {
        'state': lambda *a: 'first',
    }

    def _export_fields(self):
        return ['id', 'duration_without_children', 'duration_with_children', 'course_type_id', 'p_id', 'sequence', 'long_name', 'reference_id', 'duration', 'internal_note', 'kind', 'has_support', 'with_children', 'state_course', 'lang_id', 'category_id', 'splitted_by', 'alias', 'metakey', 'metadescription']

    def export_courses(self, cr, uid, ids, data, context={}):
        """Export (synchronize) the training courses to Joomla PHP server."""
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

                # course
                filter = []
                filterphp = ''

                if website.course_draft:
                    filter.append(('state_course','=','draft'))
                if website.course_pending:
                    filter.append(('state_course','=','pending'))
                if website.course_deprecated:
                    filter.append(('state_course','=','deprecated'))
                if website.course_validated:
                    filter.append(('state_course','=','validated'))

                for i in range(len(filter)-1):
                    filter.insert(0, '|')

                (course_new, course_update, course_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'training.course', self._export_fields(), filter, filterphp)

                values = {
                    'state':'done',
                    'course_new':course_new,
                    'course_update':course_update,
                    'course_delete':course_delete,
                }
                self.write(cr, uid, ids, values)
        else:
            raise osv.except_osv(_('Error!'), _('No Joomla! location defined!\nPlease create one.'))

        return True

joomla_course_wizard()
