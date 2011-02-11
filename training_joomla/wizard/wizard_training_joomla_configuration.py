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

class joomla_configuration_wizard(osv.osv_memory):
    _name = 'training.joomla.configuration.wizard'

    _columns = {
        'lang_new': fields.integer('Lang New', readonly=True),
        'lang_update': fields.integer('Lang Update', readonly=True),
        'lang_delete': fields.integer('Lang Delete', readonly=True),
        'format_new': fields.integer('Format New', readonly=True),
        'format_update': fields.integer('Format Update', readonly=True),
        'format_delete': fields.integer('Format Delete', readonly=True),
        'type_new': fields.integer('Type New', readonly=True),
        'type_update': fields.integer('Type Update', readonly=True),
        'type_delete': fields.integer('Type Delete', readonly=True),
        'theme_new': fields.integer('Theme New', readonly=True),
        'theme_update': fields.integer('Theme Update', readonly=True),
        'theme_delete': fields.integer('Theme Delete', readonly=True),
        'audience_new': fields.integer('Audience New', readonly=True),
        'audience_update': fields.integer('Audience Update', readonly=True),
        'audience_delete': fields.integer('Audience Delete', readonly=True),
        'partner_new': fields.integer('Partner New', readonly=True),
        'partner_update': fields.integer('Partner Update', readonly=True),
        'partner_delete': fields.integer('Partner Delete', readonly=True),
        'address_new': fields.integer('Address New', readonly=True),
        'address_update': fields.integer('Address Update', readonly=True),
        'address_delete': fields.integer('Address Delete', readonly=True),
        'product_new': fields.integer('Product New', readonly=True),
        'product_update': fields.integer('Product Update', readonly=True),
        'product_delete': fields.integer('Product Delete', readonly=True),
        'country_new': fields.integer('Country New', readonly=True),
        'country_update': fields.integer('Country Update', readonly=True),
        'country_delete': fields.integer('Country Delete', readonly=True),
        'state':fields.selection([
            ('first','First'),
            ('done','Done'),
        ],'State'),
    }

    _defaults = {
        'state': lambda *a: 'first',
    }

    def export_configurations(self, cr, uid, ids, data, context={}):
        """Export (synchronize) the training configurations to Joomla PHP server."""
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

                # lang
                filter = [('active','=','1')]
                filterphp = ''
                (lang_new, lang_update, lang_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'res.lang',
                    ['id', 'name', 'code'], filter, filterphp)

                # format
                filter = [('active','=','1')]
                filterphp = ''
                (format_new, format_update, format_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'training.offer.format',
                    ['id', 'name'], filter, filterphp)

                # type
                filter = []
                filterphp = ''
                (type_new, type_update, type_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'training.course_type',
                    ['id', 'min_limit', 'max_limit', 'name', 'objective', 'description'], filter, filterphp)

                # theme
                filter = []
                filterphp = ''
                (theme_new, theme_update, theme_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'training.course.theme',
                    ['id', 'parent_id', 'name', 'description', 'priority'], filter, filterphp)

                # target audience
                filter = []
                filterphp = ''
                (audience_new, audience_update, audience_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'training.offer.public.target',
                    ['id', 'name', 'note'], filter, filterphp)

                # country
                filter = []
                filterphp = ''
                (country_new, country_update, country_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'res.country',
                    ['id', 'code', 'name'], filter, filterphp)

                # partner & address
                filter = []
                filter_partners = []
                filterphp = ''
                partners = website.partner_joomla_ids
                for partner in partners:
                    filter_partners.append(('id','=',partner.id))
                    for address in partner.address:
                        filter.append(('partner_id','=',partner.id))

                for i in range(len(filter)-1):
                    filter.insert(0, '|')

                for i in range(len(filter_partners)-1):
                    filter_partners.insert(0, '|')

                (partner_new, partner_update, partner_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'res.partner', ['id', 'name'], filter_partners, filterphp)

                (address_new, address_update, address_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'res.partner.address', ['id', 'name', 'street', 'zip', 'city', 'phone', 'partner_id'], filter, filterphp)

                # product
                product_category_id = website.product_category_id
                filter = [('categ_id','=',product_category_id.id),('active','=',True)]
                filterphp = ''
                (product_new, product_update, product_delete) = export_table.export_table(self, cr, uid, data, context, server, username, password, 'product.product', ['id', 'name','list_price','deposit_price','default_code'], filter, filterphp)

                values = {
                    'state':'done',
                    'lang_new':lang_new,
                    'lang_update':lang_update,
                    'lang_delete':lang_delete,
                    'format_new':format_new,
                    'format_update':format_update,
                    'format_delete':format_delete,
                    'type_new':type_new,
                    'type_update':type_update,
                    'type_delete':type_delete,
                    'theme_new':theme_new,
                    'theme_update':theme_update,
                    'theme_delete':theme_delete,
                    'audience_new':audience_new,
                    'audience_update':audience_update,
                    'audience_delete':audience_delete,
                    'partner_new':partner_new,
                    'partner_update':partner_update,
                    'partner_delete':partner_delete,
                    'address_new':address_new,
                    'address_update':address_update,
                    'address_delete':address_delete,
                    'product_new':product_new,
                    'product_update':product_update,
                    'product_delete':product_delete,
                    'country_new':country_new,
                    'country_update':country_update,
                    'country_delete':country_delete,
                }
                self.write(cr, uid, ids, values)
        else:
            raise osv.except_osv(_('Error!'), _('No Joomla! location defined!\nPlease create one.'))

        return True

joomla_configuration_wizard()
